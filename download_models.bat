@echo off
chcp 65001 >nul
echo ================================================
echo   HeartMuLa 模型下載工具
echo   下載位置：%~dp0ckpt\
echo ================================================
echo.

:: 確認 hf 指令存在
where hf >nul 2>&1
if errorlevel 1 (
    echo  [安裝 huggingface-hub 工具...]
    pip install huggingface-hub -q
)

echo  開始下載（共約 12 GB，依網速需要 10-60 分鐘）
echo.

echo  [1/3] 下載 HeartMuLaGen（設定檔 + tokenizer）...
hf download --local-dir "%~dp0ckpt" "HeartMuLa/HeartMuLaGen"
echo.

echo  [2/3] 下載 HeartMuLa-oss-3B（音樂語言模型）...
hf download --local-dir "%~dp0ckpt\HeartMuLa-oss-3B" "HeartMuLa/HeartMuLa-oss-3B-happy-new-year"
echo.

echo  [3/3] 下載 HeartCodec-oss（音訊編解碼器）...
hf download --local-dir "%~dp0ckpt\HeartCodec-oss" "HeartMuLa/HeartCodec-oss-20260123"
echo.

echo ================================================
echo   ✅ 模型下載完成！
echo   位置：%~dp0ckpt\
echo ================================================
echo.
echo   現在可以啟動 HeartMuLa 生成音樂了：
echo   雙擊桌面「HeartMuLa 音樂生成器」或執行 run.bat
echo.
pause
