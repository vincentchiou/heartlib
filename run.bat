@echo off
chcp 65001 >nul
echo ================================================
echo   HeartMuLa 音樂生成器
echo   RTX 5060 Ti 16GB  ^|  Gradio UI
echo ================================================
echo.

:: ── 檢查 conda 是否存在 ───────────────────────────────────────────────────
where conda >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 conda 指令。
    echo 請先安裝 Miniconda 或 Anaconda：
    echo   https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

:: ── 啟動 heartmula 環境 ───────────────────────────────────────────────────
echo [1/3] 啟動 conda 環境 (heartmula)...
call conda activate heartmula 2>nul
if errorlevel 1 (
    echo.
    echo [提示] heartmula 環境不存在，正在建立...
    echo 這是首次設定，需要幾分鐘時間，請稍候。
    echo.
    conda env create -f environment.yml
    if errorlevel 1 (
        echo.
        echo [錯誤] 環境建立失敗，請查看上方錯誤訊息。
        echo 常見問題：NVIDIA 驅動版本需 >= 570 (for CUDA 12.8)
        pause
        exit /b 1
    )
    call conda activate heartmula
)

:: ── 顯示 GPU 資訊 ─────────────────────────────────────────────────────────
echo.
echo [2/3] 檢查 GPU...
python -c "import torch; print('  GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '未偵測到 GPU'); print('  VRAM:', f'{torch.cuda.get_device_properties(0).total_memory/1024**3:.0f} GB' if torch.cuda.is_available() else 'N/A'); print('  PyTorch:', torch.__version__); print('  CUDA:', torch.version.cuda)" 2>nul || echo   (無法取得 GPU 資訊)

:: ── 啟動 Gradio ───────────────────────────────────────────────────────────
echo.
echo [3/3] 啟動 HeartMuLa UI (http://localhost:7860)...
echo       按 Ctrl+C 可停止服務
echo.
python app.py

pause
