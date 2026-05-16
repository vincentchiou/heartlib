@echo off
chcp 65001 >nul
echo.
echo  正在啟動 HeartMuLa 安裝程式...
echo.

:: 以 PowerShell 執行主安裝腳本
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"

echo.
pause
