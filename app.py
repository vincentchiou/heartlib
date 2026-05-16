"""
HeartMuLa 音樂生成器 — Gradio UI
使用方式：python app.py
"""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- GPU optimizations for RTX 5060 Ti (Blackwell GB206, CUDA 12.8) --------
try:
    import torch

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.allow_tf32 = True
except Exception:
    pass

# Add src to Python path so heartlib is importable without pip install
sys.path.insert(0, str(Path(__file__).parent / "src"))

import gradio as gr

from heartlib.llm_providers import (
    PROVIDERS,
    LLMProvider,
    format_model_choice,
    parse_model_choice,
)

# ---------------------------------------------------------------------------
# Config persistence  (~/.heartmula_config.json)
# ---------------------------------------------------------------------------

CONFIG_PATH = Path.home() / ".heartmula_config.json"
DEFAULT_CKPT = str(Path(__file__).parent / "ckpt")


def _default_config() -> dict:
    return {
        "providers": {
            "mistral":  {"api_key": "", "selected_model": ""},
            "groq":     {"api_key": "", "selected_model": ""},
            "aistudio": {"api_key": "", "selected_model": ""},
        },
        "music": {
            "model_path":          DEFAULT_CKPT,
            "version":             "3B",
            "max_audio_length_ms": 240_000,
            "temperature":         1.0,
            "topk":                50,
            "cfg_scale":           1.5,
            "lazy_load":           True,
        },
    }


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            base  = _default_config()
            # Merge saved values into defaults (handles missing keys gracefully)
            for section in ("providers", "music"):
                if section in saved:
                    base[section].update(saved[section])
            return base
        except Exception:
            pass
    return _default_config()


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Global runtime state
# ---------------------------------------------------------------------------

_cfg: dict = load_config()
_connected: Dict[str, LLMProvider] = {}   # provider_id → LLMProvider
_models:    Dict[str, List[str]]   = {}   # provider_id → [model_id, ...]
_pipeline = None                          # HeartMuLaGenPipeline (lazy-loaded)


def _all_model_choices() -> List[str]:
    return [
        format_model_choice(pid, m)
        for pid, mlist in _models.items()
        for m in mlist
    ]


def _auto_connect_saved() -> None:
    """Reconnect providers that have saved API keys (called at startup)."""
    for pid, info in _cfg["providers"].items():
        key = info.get("api_key", "")
        if key:
            try:
                provider = LLMProvider(pid, key)
                models   = provider.list_models()
                _connected[pid] = provider
                _models[pid]    = models
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Provider connection
# ---------------------------------------------------------------------------

def _connect(
    provider_id: str,
    api_key: str,
) -> Tuple[str, gr.update, gr.update]:
    """
    Connect to one LLM provider.
    Returns (status_markdown, provider_dropdown_update, creator_selector_update).
    """
    api_key = (api_key or "").strip()
    if not api_key:
        return (
            "❌ 請輸入 API Key",
            gr.update(choices=[], visible=False),
            gr.update(),
        )
    try:
        provider = LLMProvider(provider_id, api_key)
        models   = provider.list_models()

        _connected[provider_id] = provider
        _models[provider_id]    = models
        _cfg["providers"][provider_id]["api_key"] = api_key
        save_config(_cfg)

        name        = PROVIDERS[provider_id]["name"]
        choices_fmt = [format_model_choice(provider_id, m) for m in models]
        saved_m     = _cfg["providers"][provider_id]["selected_model"]
        default_fmt = (
            format_model_choice(provider_id, saved_m)
            if saved_m in models else
            (choices_fmt[0] if choices_fmt else None)
        )

        all_choices = _all_model_choices()
        return (
            f"✅ **{name}** 連線成功，取得 **{len(models)}** 個模型",
            gr.update(choices=choices_fmt, value=default_fmt, visible=True),
            gr.update(
                choices=all_choices,
                value=all_choices[0] if all_choices else None,
            ),
        )
    except Exception as exc:
        return (
            f"❌ 連線失敗：{exc}",
            gr.update(choices=[], visible=False),
            gr.update(),
        )


# --- per-provider connect handlers (explicit, no magic) --------------------

def connect_mistral(key: str):
    return _connect("mistral", key)

def connect_groq(key: str):
    return _connect("groq", key)

def connect_aistudio(key: str):
    return _connect("aistudio", key)


# ---------------------------------------------------------------------------
# LLM generation
# ---------------------------------------------------------------------------

def generate_lyrics_and_style(
    description: str,
    model_choice: str,
) -> Tuple[str, str, str]:
    if not description.strip():
        return "", "", "❌ 請輸入音樂描述"
    if not model_choice:
        return "", "", "❌ 請先在「API 設定」連線至少一個服務，再選擇模型"

    try:
        provider_id, model_id = parse_model_choice(model_choice)
    except ValueError as exc:
        return "", "", f"❌ {exc}"

    if provider_id not in _connected:
        return "", "", "❌ 找不到已連線的服務，請重新連線"

    try:
        result = _connected[provider_id].generate_music_content(description, model_id)
        _cfg["providers"][provider_id]["selected_model"] = model_id
        save_config(_cfg)
        return (
            result["lyrics"],
            result["tags"],
            f"✅ 生成完成（{PROVIDERS[provider_id]['name']} / `{model_id}`）",
        )
    except Exception as exc:
        return "", "", f"❌ 生成失敗：{exc}"


# ---------------------------------------------------------------------------
# Music generation (local GPU via HeartMuLa)
# ---------------------------------------------------------------------------

def generate_music(
    lyrics: str,
    tags: str,
    model_path: str,
    version: str,
    max_length_ms: int,
    temperature: float,
    topk: int,
    cfg_scale: float,
    lazy_load: bool,
) -> Tuple[Optional[str], str]:
    global _pipeline

    if not lyrics.strip():
        return None, "❌ 歌詞不能為空"
    if not tags.strip():
        return None, "❌ 請提供曲風標籤"
    if not model_path or not Path(model_path).exists():
        guide = (
            f"hf download --local-dir '{model_path}' HeartMuLa/HeartMuLaGen\n"
            f"hf download --local-dir '{model_path}/HeartMuLa-oss-3B' "
            f"HeartMuLa/HeartMuLa-oss-3B-happy-new-year\n"
            f"hf download --local-dir '{model_path}/HeartCodec-oss' "
            f"HeartMuLa/HeartCodec-oss-20260123"
        )
        return None, f"❌ 找不到模型路徑：{model_path}\n\n請先下載模型：\n```\n{guide}\n```"

    try:
        import torch
        from heartlib import HeartMuLaGenPipeline
    except ImportError as exc:
        return None, (
            f"❌ 無法載入 HeartMuLa：{exc}\n"
            "請確認已啟動正確的 conda 環境（conda activate heartmula）"
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    try:
        tmp_dir     = Path(__file__).parent / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        lyrics_path = tmp_dir / "lyrics.txt"
        tags_path   = tmp_dir / "tags.txt"
        output_path = tmp_dir / "output.mp3"

        lyrics_path.write_text(lyrics.lower().strip(), encoding="utf-8")
        tags_path.write_text(tags.lower().strip(), encoding="utf-8")

        # Load pipeline once, reuse on subsequent calls
        if _pipeline is None:
            _pipeline = HeartMuLaGenPipeline.from_pretrained(
                model_path,
                device={"mula": device, "codec": device},
                dtype={"mula": torch.bfloat16, "codec": torch.float32},
                version=version,
                lazy_load=lazy_load,
            )

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats(device)

        with torch.no_grad():
            _pipeline(
                {"lyrics": str(lyrics_path), "tags": str(tags_path)},
                max_audio_length_ms=int(max_length_ms),
                save_path=str(output_path),
                topk=int(topk),
                temperature=float(temperature),
                cfg_scale=float(cfg_scale),
            )

        status = f"✅ 音樂生成完成！已儲存至：{output_path}"
        if torch.cuda.is_available():
            peak_gb = torch.cuda.max_memory_allocated(device) / 1024**3
            status += f"\n📊 GPU 峰值顯存：{peak_gb:.1f} GB"

        return str(output_path), status

    except Exception as exc:  # catches torch.cuda.OutOfMemoryError too
        _pipeline = None
        gc.collect()
        try:
            import torch as _t
            if _t.cuda.is_available():
                _t.cuda.empty_cache()
        except Exception:
            pass

        if "out of memory" in str(exc).lower():
            return None, (
                "❌ GPU 顯存不足！\n"
                "建議：\n"
                "1. 勾選「Lazy Load」選項\n"
                "2. 縮短最大音樂長度（例如 120000 ms）\n"
                "3. 確認沒有其他程式佔用 GPU 顯存"
            )
        return None, f"❌ 生成失敗：{exc}"


def reset_pipeline() -> str:
    global _pipeline
    _pipeline = None
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    return "🔄 模型已從 GPU 卸載，下次生成將重新載入"


# ---------------------------------------------------------------------------
# Settings auto-save
# ---------------------------------------------------------------------------

def _save_music_settings(path, version, max_len, temp, tk, cfg, lazy):
    _cfg["music"].update({
        "model_path":          path,
        "version":             version,
        "max_audio_length_ms": int(max_len),
        "temperature":         float(temp),
        "topk":                int(tk),
        "cfg_scale":           float(cfg),
        "lazy_load":           bool(lazy),
    })
    save_config(_cfg)


# ---------------------------------------------------------------------------
# GPU info helper
# ---------------------------------------------------------------------------

def _gpu_banner() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            name   = torch.cuda.get_device_name(0)
            vram   = torch.cuda.get_device_properties(0).total_memory / 1024**3
            return (
                f'<div style="background:#f0fdf4;border:1px solid #86efac;'
                f'border-radius:8px;padding:8px 14px;margin-bottom:8px;">'
                f'🖥️ <b>偵測到 GPU：{name}（{vram:.0f} GB VRAM）</b>'
                f' — 將用於本地音樂生成</div>'
            )
    except Exception:
        pass
    return (
        '<div style="background:#fefce8;border:1px solid #fde047;'
        'border-radius:8px;padding:8px 14px;margin-bottom:8px;">'
        '⚠️ <b>未偵測到 GPU</b>，將使用 CPU（生成速度非常慢）</div>'
    )


# ---------------------------------------------------------------------------
# Build Gradio UI
# ---------------------------------------------------------------------------

def build_ui() -> gr.Blocks:
    cfg = _cfg
    mc  = cfg["music"]

    # Pre-compute initial model choices (from auto-connect at startup)
    init_choices = _all_model_choices()

    with gr.Blocks(
        title="HeartMuLa 音樂生成器",
        theme=gr.themes.Soft(primary_hue="violet", secondary_hue="purple"),
    ) as demo:

        gr.HTML("""
        <div style="text-align:center;margin-bottom:8px;">
          <h1>🎵 HeartMuLa 音樂生成器</h1>
          <p>AI 輔助創作：描述音樂風格 →
             生成歌詞 ＋ 曲風 ＋ 樂器 →
             本地 GPU 生成音樂</p>
        </div>
        """)
        gr.HTML(_gpu_banner())

        # ===================================================================
        #  TAB 1 — API 設定
        # ===================================================================
        with gr.Tab("🔌 API 設定"):
            gr.Markdown(
                "輸入各服務的免費 API Key 並點擊「連線並取得模型」。"
                "系統已預先設定連線網址，**不需手動輸入 URL**。"
            )

            # ---- Mistral --------------------------------------------------
            with gr.Accordion("🇫🇷 Mistral AI", open=True):
                with gr.Row():
                    mistral_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="貼上 Mistral API Key...",
                        value=cfg["providers"]["mistral"]["api_key"],
                        scale=5,
                    )
                    mistral_btn = gr.Button(
                        "🔗 連線並取得模型", variant="primary", scale=1, min_width=160
                    )
                mistral_status = gr.Markdown(
                    "✅ 已有儲存的 Key，請點連線重新取得模型清單"
                    if cfg["providers"]["mistral"]["api_key"] else ""
                )
                mistral_dd = gr.Dropdown(
                    label="可用模型（點選即選取）",
                    choices=(
                        [format_model_choice("mistral", m) for m in _models.get("mistral", [])]
                    ),
                    value=(
                        format_model_choice("mistral", cfg["providers"]["mistral"]["selected_model"])
                        if cfg["providers"]["mistral"]["selected_model"] in _models.get("mistral", [])
                        else None
                    ),
                    visible=bool(_models.get("mistral")),
                )

            # ---- Groq -----------------------------------------------------
            with gr.Accordion("⚡ Groq", open=True):
                with gr.Row():
                    groq_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="貼上 Groq API Key...",
                        value=cfg["providers"]["groq"]["api_key"],
                        scale=5,
                    )
                    groq_btn = gr.Button(
                        "🔗 連線並取得模型", variant="primary", scale=1, min_width=160
                    )
                groq_status = gr.Markdown(
                    "✅ 已有儲存的 Key，請點連線重新取得模型清單"
                    if cfg["providers"]["groq"]["api_key"] else ""
                )
                groq_dd = gr.Dropdown(
                    label="可用模型（點選即選取）",
                    choices=(
                        [format_model_choice("groq", m) for m in _models.get("groq", [])]
                    ),
                    value=(
                        format_model_choice("groq", cfg["providers"]["groq"]["selected_model"])
                        if cfg["providers"]["groq"]["selected_model"] in _models.get("groq", [])
                        else None
                    ),
                    visible=bool(_models.get("groq")),
                )

            # ---- Google AI Studio -----------------------------------------
            with gr.Accordion("🔷 Google AI Studio", open=True):
                with gr.Row():
                    aistudio_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="貼上 Google AI Studio API Key...",
                        value=cfg["providers"]["aistudio"]["api_key"],
                        scale=5,
                    )
                    aistudio_btn = gr.Button(
                        "🔗 連線並取得模型", variant="primary", scale=1, min_width=160
                    )
                aistudio_status = gr.Markdown(
                    "✅ 已有儲存的 Key，請點連線重新取得模型清單"
                    if cfg["providers"]["aistudio"]["api_key"] else ""
                )
                aistudio_dd = gr.Dropdown(
                    label="可用模型（點選即選取）",
                    choices=(
                        [format_model_choice("aistudio", m) for m in _models.get("aistudio", [])]
                    ),
                    value=(
                        format_model_choice("aistudio", cfg["providers"]["aistudio"]["selected_model"])
                        if cfg["providers"]["aistudio"]["selected_model"] in _models.get("aistudio", [])
                        else None
                    ),
                    visible=bool(_models.get("aistudio")),
                )

            gr.Markdown(
                "💡 **申請免費 API Key：**  "
                "[Mistral AI](https://console.mistral.ai/) ｜ "
                "[Groq](https://console.groq.com/) ｜ "
                "[Google AI Studio](https://aistudio.google.com/)",
                elem_classes=["tip"] if hasattr(gr, "themes") else [],
            )

        # ===================================================================
        #  TAB 2 — 音樂創作
        # ===================================================================
        with gr.Tab("🎵 音樂創作"):

            with gr.Row():
                # ---- Left: prompt + model selector ------------------------
                with gr.Column(scale=1):
                    gr.Markdown("### ✍️ 描述您想要的音樂")
                    description_box = gr.Textbox(
                        label="音樂描述（任何語言）",
                        placeholder=(
                            "例如：一首充滿希望的國語流行歌，描述畢業後離鄉追夢的心情，"
                            "帶有鋼琴、弦樂和輕鼓，節奏中板，女聲主唱..."
                        ),
                        lines=5,
                    )

                    model_selector = gr.Dropdown(
                        label="使用哪個 AI 模型生成歌詞與曲風",
                        choices=init_choices,
                        value=init_choices[0] if init_choices else None,
                        allow_custom_value=False,
                        info="請先在「API 設定」頁面連線",
                    )
                    refresh_btn = gr.Button("🔄 更新模型清單", size="sm")

                    generate_btn = gr.Button(
                        "✨ AI 生成歌詞、曲風與樂器", variant="primary", size="lg"
                    )
                    llm_status = gr.Markdown("")

                # ---- Right: generated content (editable) ------------------
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 生成結果（可直接修改）")
                    lyrics_box = gr.Textbox(
                        label="歌詞（HeartMuLa 格式）",
                        lines=12,
                        placeholder="AI 生成的歌詞將顯示在這裡，您可以直接修改...",
                        show_copy_button=True,
                    )
                    tags_box = gr.Textbox(
                        label="曲風 ＋ 樂器標籤（逗號分隔，無空格）",
                        lines=2,
                        placeholder="例如：pop,happy,piano,acoustic_guitar,drums,upbeat,female_vocal",
                        show_copy_button=True,
                    )

            gr.Markdown("---")
            gr.Markdown("### 🎶 本地 GPU 生成音樂")

            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Row():
                        model_path_box = gr.Textbox(
                            label="HeartMuLa 模型路徑",
                            value=mc["model_path"],
                            placeholder="./ckpt",
                            scale=4,
                        )
                        version_radio = gr.Radio(
                            label="版本",
                            choices=["3B", "7B"],
                            value=mc["version"],
                            scale=1,
                        )

                    with gr.Accordion("🔧 生成參數（進階）", open=False):
                        with gr.Row():
                            sl_max_len = gr.Slider(
                                30_000, 300_000,
                                value=mc["max_audio_length_ms"],
                                step=10_000,
                                label="最大音樂長度 (ms)",
                            )
                            sl_temp = gr.Slider(
                                0.5, 2.0,
                                value=mc["temperature"],
                                step=0.05,
                                label="Temperature",
                            )
                        with gr.Row():
                            sl_topk = gr.Slider(
                                10, 200,
                                value=mc["topk"],
                                step=5,
                                label="Top-K",
                            )
                            sl_cfg = gr.Slider(
                                1.0, 5.0,
                                value=mc["cfg_scale"],
                                step=0.1,
                                label="CFG Scale",
                            )
                        cb_lazy = gr.Checkbox(
                            label="Lazy Load（單 GPU 省顯存，速度略慢）",
                            value=mc["lazy_load"],
                        )

                    with gr.Row():
                        music_btn = gr.Button("🎵 生成音樂", variant="primary", size="lg")
                        reset_btn = gr.Button("🔄 卸載模型", size="sm")

                with gr.Column(scale=1):
                    music_status = gr.Markdown("")
                    audio_out    = gr.Audio(label="生成的音樂", type="filepath")

        # ===================================================================
        #  TAB 3 — 使用說明
        # ===================================================================
        with gr.Tab("📖 使用說明"):
            gr.Markdown("""
## 快速開始

### 1️⃣ 取得免費 API Key（三選一即可）
| 服務 | 申請連結 | 特色 |
|---|---|---|
| Mistral AI | [console.mistral.ai](https://console.mistral.ai/) | 高品質法系模型 |
| Groq | [console.groq.com](https://console.groq.com/) | 推理速度極快 |
| Google AI Studio | [aistudio.google.com](https://aistudio.google.com/) | Gemini 系列 |

### 2️⃣ 下載音樂生成模型（約 12 GB）
```bash
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' HeartMuLa/HeartCodec-oss-20260123
```

### 3️⃣ 操作流程
1. 「API 設定」→ 貼上 Key → 點「連線並取得模型」→ 從下拉清單選模型
2. 「音樂創作」→ 輸入音樂描述 → 點「✨ AI 生成歌詞、曲風與樂器」
3. 確認或修改歌詞與標籤 → 點「🎵 生成音樂」→ 等待完成並播放

---

## 歌詞格式
HeartMuLa 使用段落標記（AI 會自動套用正確格式）：
```
[Intro]  [Verse]  [Prechorus]  [Chorus]  [Bridge]  [Outro]
```

## 曲風標籤範例
```
pop,happy,upbeat,piano,guitar,drums,female_vocal
classical,orchestral,dramatic,strings,epic,choir
jazz,smooth,saxophone,bass,drums,relaxed,male_vocal
```

## RTX 5060 Ti 16 GB 建議設定
| 參數 | 建議值 | 說明 |
|---|---|---|
| 版本 | 3B | 16 GB VRAM 充裕，無需 Lazy Load |
| Lazy Load | 可不勾 | 速度更快 |
| Temperature | 1.0 | 預設即可 |
| CFG Scale | 1.5 | 提高可增加歌詞依循度 |
| 最大長度 | 240000 ms | 約 4 分鐘 |

## API Key 安全性
您的 API Key 僅儲存在本機 `~/.heartmula_config.json`，不會傳送至任何第三方伺服器。
""")

        # ===================================================================
        #  Event bindings (all explicit — no magic iteration)
        # ===================================================================

        # -- Provider connect buttons → update provider dropdown + creator selector
        mistral_btn.click(
            fn=connect_mistral,
            inputs=[mistral_key],
            outputs=[mistral_status, mistral_dd, model_selector],
        )
        groq_btn.click(
            fn=connect_groq,
            inputs=[groq_key],
            outputs=[groq_status, groq_dd, model_selector],
        )
        aistudio_btn.click(
            fn=connect_aistudio,
            inputs=[aistudio_key],
            outputs=[aistudio_status, aistudio_dd, model_selector],
        )

        # -- Refresh creator model list
        def _refresh():
            choices = _all_model_choices()
            return gr.update(choices=choices, value=choices[0] if choices else None)

        refresh_btn.click(fn=_refresh, outputs=[model_selector])

        # -- LLM: generate lyrics + style
        generate_btn.click(
            fn=generate_lyrics_and_style,
            inputs=[description_box, model_selector],
            outputs=[lyrics_box, tags_box, llm_status],
        )

        # -- HeartMuLa: generate music
        music_settings = [
            lyrics_box, tags_box, model_path_box, version_radio,
            sl_max_len, sl_temp, sl_topk, sl_cfg, cb_lazy,
        ]
        music_btn.click(
            fn=generate_music,
            inputs=music_settings,
            outputs=[audio_out, music_status],
        )

        # -- Reset / unload pipeline
        reset_btn.click(fn=reset_pipeline, outputs=[music_status])

        # -- Auto-save music settings on change
        save_inputs = [
            model_path_box, version_radio, sl_max_len,
            sl_temp, sl_topk, sl_cfg, cb_lazy,
        ]
        for comp in save_inputs:
            comp.change(fn=_save_music_settings, inputs=save_inputs)

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  HeartMuLa 音樂生成器 啟動中...")
    print("=" * 50)

    _auto_connect_saved()

    choices = _all_model_choices()
    if choices:
        print(f"  自動重連成功：{len(choices)} 個可用模型")
    else:
        print("  尚未設定 API Key，請在「API 設定」頁面進行設定")

    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        show_error=True,
    )
