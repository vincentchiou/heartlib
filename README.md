<p align="center">
    <picture>
        <source srcset="./assets/logo.png" media="(prefers-color-scheme: dark)">
        <img src="./assets/logo.png" width="30%">
    </picture>
    
</p>

<p align="center">
    <a href="https://heartmula.github.io/">線上展示 🎶</a> &nbsp;|&nbsp; 📑 <a href="https://arxiv.org/pdf/2601.10547">論文</a>
    <br>
    <a href="https://huggingface.co/HeartMuLa/HeartMuLa-oss-3B-happy-new-year">HeartMuLa-oss-3B-happy-new-year 🤗</a> &nbsp;|&nbsp; <a href="https://modelscope.cn/models/HeartMuLa/HeartMuLa-oss-3B-happy-new-year">HeartMuLa-oss-3B-happy-new-year <picture>
        <source srcset="./assets/badge.svg" media="(prefers-color-scheme: dark)">
        <img src="./assets/badge.svg" width="20px">
    </picture></a>
    <br>
</p>

---

## 🆕 v0.2.0 — Gradio 網頁介面 ＋ 多服務 LLM 整合

本版本新增**一鍵啟動的 Gradio 網頁介面**，將 AI 歌詞／曲風／樂器生成與本地 GPU 音樂生成串接成完整流程：

| 功能 | 說明 |
|---|---|
| 🎵 AI 生成歌詞＋曲風＋樂器 | 支援 Mistral AI / Groq / Google AI Studio |
| 🔌 免輸入網址 | API 連線網址已預先設定，只需貼上 API Key |
| 📋 模型下拉選單 | 連線後自動取得可用模型清單，點選即可使用 |
| 🖥️ 本地 GPU 推理 | 針對 RTX 5060 Ti 16GB（Blackwell，CUDA 12.8）最佳化 |
| 🐍 獨立環境 | 專屬 conda 環境（`heartmula`），不干擾其他專案 |

**快速開始：**
```bash
# 1. 建立 conda 環境
conda env create -f environment.yml
conda activate heartmula

# 2. 下載模型檔案（約 12 GB）
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' HeartMuLa/HeartCodec-oss-20260123

# 3. 啟動介面（Windows）
run.bat
# 或直接執行：python app.py
```

---

# HeartMuLa：開源音樂基礎模型家族

HeartMuLa 是一系列開源音樂基礎模型，包含以下元件：

1. **HeartMuLa**：音樂語言模型，根據歌詞與風格標籤生成音樂，支援幾乎所有語言的多語系輸入。
2. **HeartCodec**：12.5 Hz 高保真音樂編解碼器。
3. **HeartTranscriptor**：基於 Whisper 微調的歌詞轉錄模型，詳見[使用說明](./examples/README.md)。
4. **HeartCLAP**：音訊與文字對齊模型，建立音樂描述與跨模態檢索的統一嵌入空間。

---

以下為 oss-3B 版本與其他基準模型的實驗結果比較：

<p align="center">
    <picture>
        <source srcset="./assets/exp-new.png" media="(prefers-color-scheme: dark)">
        <img src="./assets/exp-new.png" width="90%">
    </picture>
</p>

---

## 🔥 亮點

最新內部版本 HeartMuLa-7B 在音樂性、保真度與可控性方面已達到**與 Suno 相當的水準**。

## 📰 最新消息
加入 Discord！[<img alt="加入 discord" src="https://img.shields.io/discord/842440537755353128?color=%237289da&logo=discord"/>](https://discord.gg/rkC4VmpH)

- 🚀 **2026 年 4 月 10 日**

  在 [Hugging Face](https://huggingface.co/spaces/HeartMuLa/heartmula) 與 [ModelScope](https://www.modelscope.cn/studios/HeartMuLa/heartmula/) 上線線上展示空間。

- 🚀 **2026 年 2 月 13 日**

  發布 **HeartMuLa-oss-3B-happy-new-year** 版本。此版本目前在歌詞可控性與音樂品質方面為最佳開源模型。推薦搭配 **HeartMuLa-oss-3B-happy-new-year** 與 **HeartCodec-oss-20260123** 進行音樂生成。

- ⚖️ **2026 年 2 月 3 日**

  發布 [HeartMuLa-Benchmark](https://modelscope.cn/datasets/HeartMuLa/HeartMuLa-Benchmark)（論文中稱為 **HeartBeats Benchmark**）。此基準測試集涵蓋多語言、多風格的 AI 生成歌詞與標籤，提供嚴謹公平的評估框架。

- 🚀 **2026 年 1 月 23 日**

  透過強化學習持續優化模型，正式發布 **HeartMuLa-RL-oss-3B-20260123**，可對風格與標籤進行更精確的控制；同步發布 **HeartCodec-oss-20260123**，大幅提升音訊解碼品質。

- 🫶 **2026 年 1 月 20 日**

  感謝 [Benji](https://github.com/benjiyaya) 為 HeartMuLa 製作了出色的 [ComfyUI 自訂節點](https://github.com/benjiyaya/HeartMuLa_ComfyUI)！

- ⚖️ **2026 年 1 月 20 日**

  授權更新：本 repo 及所有相關模型權重的授權已更新為 **Apache 2.0**。

- 🚀 **2026 年 1 月 14 日**

  正式發布 **HeartTranscriptor-oss**、首個 **HeartMuLa-oss-3B** 版本及 **HeartCodec-oss**。

---

## 🧭 開發計畫

- ⏳ 發布推理加速與串流推理腳本（目前推理速度約 RTF ≈ 1.0）。
- ⏳ 支援**參考音訊條件生成**、**細粒度可控音樂生成**、**熱門歌曲生成**。
- ⏳ 發布 **HeartMuLa-oss-7B** 版本。
- ✅ 已發布 **HeartCodec-oss**、**HeartMuLa-oss-3B** 及 **HeartTranscriptor-oss** 的推理程式碼與預訓練權重。

---

## 🛠️ 本地部署

### ⚙️ 方式一：使用 Gradio 網頁介面（推薦）

建立獨立 conda 環境並一鍵啟動：

```bash
# 建立環境（首次需幾分鐘）
conda env create -f environment.yml
conda activate heartmula

# 下載模型（約 12 GB）
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' HeartMuLa/HeartCodec-oss-20260123

# 啟動（Windows 雙擊即可）
run.bat
```

### ⚙️ 方式二：傳統命令列安裝

建議使用 `python=3.10`。

```bash
git clone https://github.com/vincentchiou/heartlib.git
cd heartlib
pip install -e .
```

下載預訓練模型：

```bash
# 使用 Hugging Face
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' HeartMuLa/HeartCodec-oss-20260123

# 使用 ModelScope
modelscope download --model 'HeartMuLa/HeartMuLaGen' --local_dir './ckpt'
modelscope download --model 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year' --local_dir './ckpt/HeartMuLa-oss-3B'
modelscope download --model 'HeartMuLa/HeartCodec-oss-20260123' --local_dir './ckpt/HeartCodec-oss'
```

下載完成後，`./ckpt` 資料夾結構應如下：

```
./ckpt/
├── HeartCodec-oss/
├── HeartMuLa-oss-3B/
├── gen_config.json
└── tokenizer.json
```

### ▶️ 命令列使用範例

執行音樂生成：

```bash
python ./examples/run_music_generation.py --model_path=./ckpt --version="3B"
```

預設會根據 `./assets` 資料夾中的歌詞與標籤生成音樂，輸出儲存於 `./assets/output.mp3`。

#### 常見問題

**1. 如何指定歌詞與標籤？**

模型會從 `--lyrics` 指定的 txt 檔載入歌詞（預設：`./assets/lyrics.txt`）。如要使用自訂歌詞，直接修改該檔案內容，或指定新路徑：`--lyrics my_awesome_lyrics.txt`。標籤操作方式相同。

**2. CUDA 顯存不足？**

若有多張 GPU（例如兩張 4090），可將 HeartMuLa 與 HeartCodec 分別載至不同裝置：
```bash
--mula_device cuda:0 --codec_device cuda:1
```

若只有單張 GPU，請啟用 Lazy Load：
```bash
--lazy_load true
```

**所有參數說明：**

| 參數 | 預設值 | 說明 |
|---|---|---|
| `--model_path` | 必填 | 預訓練模型路徑 |
| `--lyrics` | `./assets/lyrics.txt` | 歌詞檔路徑 |
| `--tags` | `./assets/tags.txt` | 標籤檔路徑 |
| `--save_path` | `./assets/output.mp3` | 輸出音訊路徑 |
| `--max_audio_length_ms` | `240000` | 最大音樂長度（毫秒） |
| `--topk` | `50` | Top-K 採樣參數 |
| `--temperature` | `1.0` | 採樣溫度 |
| `--cfg_scale` | `1.5` | 分類器自由引導強度 |
| `--version` | `3B` | 模型版本（`3B` 或 `7B`，7B 尚未發布） |
| `--mula_device` / `--codec_device` | `cuda` | 各模組載入裝置 |
| `--mula_dtype` / `--codec_dtype` | `bf16` / `fp32` | 推理精度（HeartCodec 使用 bf16 可能降低音質） |
| `--lazy_load` | `false` | 按需載入模組以節省顯存 |

**歌詞格式範例：**

```txt
[Intro]

[Verse]
The sun creeps in across the floor
I hear the traffic outside the door
The coffee pot begins to hiss
It is another morning just like this

[Prechorus]
The world keeps spinning round and round
Feet are planted on the ground
I find my rhythm in the sound

[Chorus]
Every day the light returns
Every day the fire burns
We keep on walking down this street
Moving to the same steady beat
It is the ordinary magic that we meet

[Verse]
The hours tick deeply into noon
Chasing shadows,chasing the moon
Work is done and the lights go low
Watching the city start to glow

[Bridge]
It is not always easy,not always bright
Sometimes we wrestle with the night
But we make it to the morning light

[Chorus]
Every day the light returns
Every day the fire burns
We keep on walking down this street
Moving to the same steady beat

[Outro]
Just another day
Every single day
```

標籤格式（逗號分隔，無空格，全部小寫），可參考[此討論串](https://github.com/HeartMuLa/heartlib/issues/17)：

```txt
piano,happy,wedding,synthesizer,romantic
```

---

## ⚖️ 授權

本 repository 採用 Apache 2.0 授權條款。

---

## 📚 引用

```
@misc{yang2026heartmulafamilyopensourced,
      title={HeartMuLa: A Family of Open Sourced Music Foundation Models}, 
      author={Dongchao Yang and Yuxin Xie and Yuguo Yin and Zheyu Wang and Xiaoyu Yi and Gongxi Zhu and Xiaolong Weng and Zihan Xiong and Yingzhe Ma and Dading Cong and Jingliang Liu and Zihang Huang and Jinghan Ru and Rongjie Huang and Haoran Wan and Peixu Wang and Kuoxi Yu and Helin Wang and Liming Liang and Xianwei Zhuang and Yuanyuan Wang and Haohan Guo and Junjie Cao and Zeqian Ju and Songxiang Liu and Yuewen Cao and Heming Weng and Yuexian Zou},
      year={2026},
      eprint={2601.10547},
      archivePrefix={arXiv},
      primaryClass={cs.SD},
      url={https://arxiv.org/abs/2601.10547}, 
}
```

## 📬 聯絡我們

對 HeartMuLa 有興趣，歡迎來信：heartmula.ai@gmail.com

也可透過 [Discord](https://discord.gg/BKXF5FgH) 或微信群加入我們。

掃描左側 QR Code 加入微信群（若已過期請發 Issue 通知更新）。若群成員超過 200 人，微信限制直接掃碼加群，請掃描右側團隊成員 QR Code，並發送請求文字「**HeartMuLa Group Invite**」，我們將手動邀請您入群。

<p align="center">
    <picture>
        <source srcset="./assets/group_wx.jpeg" media="(prefers-color-scheme: dark)">
        <img src="./assets/group_wx.jpeg" width="40%">
    </picture>
    <picture>
        <source srcset="./assets/lead_wx.jpeg" media="(prefers-color-scheme: dark)">
        <img src="./assets/lead_wx.jpeg" width="40%">
    </picture>
</p>
