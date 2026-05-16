# HeartMuLa 一鍵安裝程式
# 自動偵測 GPU / CUDA / conda，建立隔離環境並安裝所有套件

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── 輔助函式 ─────────────────────────────────────────────────────────────────
function Write-Banner {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║     🎵  HeartMuLa 音樂生成器  一鍵安裝       ║" -ForegroundColor Cyan
    Write-Host "  ╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}
function Write-Step($n, $total, $msg) {
    Write-Host "  ── [$n/$total] $msg" -ForegroundColor Yellow
}
function Write-Ok($msg)   { Write-Host "      ✅ $msg" -ForegroundColor Green }
function Write-Info($msg) { Write-Host "      → $msg"  -ForegroundColor White }
function Write-Warn($msg) { Write-Host "      ⚠ $msg"  -ForegroundColor DarkYellow }
function Write-Err($msg)  { Write-Host "      ✗ $msg"  -ForegroundColor Red; exit 1 }

Write-Banner

# ── STEP 1: 偵測 GPU 與 CUDA ─────────────────────────────────────────────────
Write-Step 1 5 "偵測 GPU 與 CUDA 版本..."

$gpuName     = ""
$cudaVersion = ""
$torchCuda   = "cpu"
$torchIndex  = "https://download.pytorch.org/whl/cpu"

try {
    $nvOut = nvidia-smi 2>$null
    if ($nvOut) {
        $gpuName = (nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>$null |
                    Select-Object -First 1).Trim()

        $cudaLine = ($nvOut | Select-String "CUDA Version" | Select-Object -First 1).ToString()
        if ($cudaLine -match "CUDA Version:\s*(\d+\.\d+)") {
            $cudaVersion = $Matches[1]
        }
    }
} catch {}

if ($gpuName) {
    Write-Ok "GPU 型號：$gpuName"

    if ($cudaVersion) {
        $cv = [version]$cudaVersion
        Write-Ok "CUDA 版本：$cudaVersion"

        if     ($cv -ge [version]"12.8") { $torchCuda = "cu128"; $torchIndex = "https://download.pytorch.org/whl/cu128" }
        elseif ($cv -ge [version]"12.6") { $torchCuda = "cu126"; $torchIndex = "https://download.pytorch.org/whl/cu126" }
        elseif ($cv -ge [version]"12.4") { $torchCuda = "cu124"; $torchIndex = "https://download.pytorch.org/whl/cu124" }
        elseif ($cv -ge [version]"11.8") { $torchCuda = "cu118"; $torchIndex = "https://download.pytorch.org/whl/cu118" }
        else {
            $torchCuda  = "cpu"
            $torchIndex = "https://download.pytorch.org/whl/cpu"
            Write-Warn "CUDA 版本 $cudaVersion 過舊（建議升級驅動），將使用 CPU 模式"
        }

        Write-Ok "PyTorch 將安裝 $torchCuda 版本"
    } else {
        Write-Warn "無法取得 CUDA 版本，使用 CPU 模式（建議更新 NVIDIA 驅動）"
    }
} else {
    Write-Warn "未偵測到 NVIDIA GPU，將使用 CPU 模式（音樂生成速度較慢）"
}

# ── STEP 2: 尋找或安裝 Miniconda ─────────────────────────────────────────────
Write-Step 2 5 "檢查 conda 是否已安裝..."

$condaExe = $null

# 常見安裝路徑
$candidatePaths = @(
    "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
    "$env:USERPROFILE\Miniconda3\Scripts\conda.exe",
    "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
    "$env:USERPROFILE\Anaconda3\Scripts\conda.exe",
    "$env:ProgramData\miniconda3\Scripts\conda.exe",
    "$env:ProgramData\Miniconda3\Scripts\conda.exe",
    "$env:ProgramData\anaconda3\Scripts\conda.exe",
    "C:\miniconda3\Scripts\conda.exe",
    "C:\Miniconda3\Scripts\conda.exe",
    "C:\anaconda3\Scripts\conda.exe"
)

foreach ($p in $candidatePaths) {
    if (Test-Path $p) { $condaExe = $p; break }
}

if (-not $condaExe) {
    try {
        $condaCmd = Get-Command conda -ErrorAction Stop
        $condaExe = $condaCmd.Source
    } catch {}
}

if ($condaExe) {
    Write-Ok "找到 conda：$condaExe"
} else {
    Write-Info "未找到 conda，正在下載 Miniconda（約 90 MB）..."

    $installer  = "$env:TEMP\Miniconda3-latest-Windows-x86_64.exe"
    $installDst = "$env:USERPROFILE\miniconda3"
    $downloadUrl = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installer -UseBasicParsing
    } catch {
        Write-Err "下載 Miniconda 失敗，請檢查網路連線後重試。`n錯誤：$_"
    }

    Write-Info "安裝 Miniconda 到 $installDst ..."
    $proc = Start-Process -Wait -PassThru -FilePath $installer `
        -ArgumentList "/InstallationType=JustMe", "/RegisterPython=0", "/S", "/D=$installDst"

    if ($proc.ExitCode -ne 0) {
        Write-Err "Miniconda 安裝失敗（exit $($proc.ExitCode)）"
    }

    $condaExe = "$installDst\Scripts\conda.exe"
    if (-not (Test-Path $condaExe)) {
        Write-Err "安裝後仍找不到 conda.exe，請手動安裝：https://docs.conda.io/en/latest/miniconda.html"
    }

    Write-Ok "Miniconda 安裝完成：$installDst"
}

# 取得 conda 根目錄
$condaBase = (Split-Path (Split-Path $condaExe))

# ── STEP 3: 建立隔離 conda 環境 ───────────────────────────────────────────────
Write-Step 3 5 "建立隔離的 conda 環境（heartmula / Python 3.10）..."

$envList = & $condaExe env list 2>$null
if ($envList | Select-String "heartmula") {
    Write-Info "heartmula 環境已存在，略過建立步驟"
} else {
    Write-Info "建立環境中，請稍候..."
    & $condaExe create -n heartmula python=3.10 pip -y
    Write-Ok "heartmula 環境建立完成"
}

$envPython = "$condaBase\envs\heartmula\python.exe"
$envPip    = "$condaBase\envs\heartmula\Scripts\pip.exe"

if (-not (Test-Path $envPip)) {
    Write-Err "找不到 pip：$envPip`n請嘗試刪除環境後重新安裝：conda env remove -n heartmula"
}

# ── STEP 4: 安裝所有套件 ──────────────────────────────────────────────────────
Write-Step 4 5 "安裝套件（根據 GPU 環境選擇版本）..."

function Invoke-Pip {
    param([string[]]$Args)
    Write-Info "pip install $($Args -join ' ')"
    & $envPip install @Args
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "上方套件安裝出現警告，繼續安裝其餘套件..."
    }
}

# PyTorch（使用 --index-url 確保安裝正確的 CUDA 版本）
Write-Info "安裝 PyTorch（$torchCuda）..."
Invoke-Pip @("torch", "torchaudio", "torchvision", "--index-url", $torchIndex)

# HeartMuLa 核心依賴
Write-Info "安裝 HeartMuLa 核心套件..."
Invoke-Pip @(
    "torchtune==0.4.0", "torchao==0.9.0",
    "numpy==2.0.2", "tqdm==4.67.1",
    "traitlets==5.7.1", "traittypes==0.2.3",
    "transformers==4.57.0", "tokenizers==0.22.1",
    "ipykernel==6.17.1", "einops==0.8.1",
    "accelerate==1.12.0", "bitsandbytes==0.49.0",
    "vector-quantize-pytorch==1.27.15",
    "modelscope==1.33.0", "soundfile"
)

# Gradio UI + LLM API 客戶端
Write-Info "安裝 Gradio UI 與 API 套件..."
Invoke-Pip @("gradio>=4.44.0", "openai>=1.50.0")

# 安裝 heartlib 本體（editable mode）
Write-Info "安裝 heartlib 本體..."
Invoke-Pip @("-e", $scriptDir)

# 驗證 PyTorch 與 GPU
Write-Info "驗證 PyTorch 安裝..."
$torchCheck = & $envPython -c @"
import torch
cuda = torch.cuda.is_available()
ver  = torch.__version__
dev  = torch.cuda.get_device_name(0) if cuda else 'CPU'
mem  = f'{torch.cuda.get_device_properties(0).total_memory/1024**3:.0f} GB' if cuda else '-'
print(f'PyTorch {ver} | GPU:{dev} | VRAM:{mem} | CUDA:{cuda}')
"@ 2>&1

Write-Ok "驗證結果：$torchCheck"

# ── STEP 5: 建立捷徑與完成 ────────────────────────────────────────────────────
Write-Step 5 5 "建立啟動捷徑..."

# 更新 run.bat 記錄 conda 路徑（讓 run.bat 精確找到 conda）
$runBatContent = @"
@echo off
chcp 65001 >nul
echo ================================================
echo   HeartMuLa 音樂生成器  正在啟動...
echo ================================================
echo.
:: GPU 資訊
"$envPython" -c "import torch; print('  GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '未偵測到 GPU'); print('  VRAM:', f'{torch.cuda.get_device_properties(0).total_memory/1024**3:.0f} GB' if torch.cuda.is_available() else 'N/A'); print('  PyTorch:', torch.__version__)" 2>nul
echo.
echo   開啟瀏覽器：http://localhost:7860
echo   按 Ctrl+C 可停止服務
echo.
"$envPython" "%~dp0app.py"
pause
"@
$runBatContent | Out-File -FilePath "$scriptDir\run.bat" -Encoding utf8

# 桌面捷徑
$shortcutPath = "$env:USERPROFILE\Desktop\HeartMuLa 音樂生成器.lnk"
try {
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($shortcutPath)
    $sc.TargetPath    = "$scriptDir\run.bat"
    $sc.WorkingDirectory = $scriptDir
    $sc.Description   = "HeartMuLa AI 音樂生成器"
    $sc.Save()
    Write-Ok "桌面捷徑已建立：HeartMuLa 音樂生成器"
} catch {
    Write-Warn "無法建立桌面捷徑（$_），請直接執行 run.bat"
}

# ── 完成畫面 ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║          ✅  安裝完成！                       ║" -ForegroundColor Green
Write-Host "  ╚═══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
if ($gpuName) {
    Write-Host "  🖥️  GPU：$gpuName" -ForegroundColor Cyan
    Write-Host "  ⚡  模式：$torchCuda（本地 GPU 加速）" -ForegroundColor Cyan
} else {
    Write-Host "  💻  模式：CPU（無 GPU）" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "  ─── 接下來的步驟 ───────────────────────────────" -ForegroundColor White
Write-Host ""
Write-Host "  1️⃣  雙擊桌面「HeartMuLa 音樂生成器」啟動 UI" -ForegroundColor White
Write-Host "      （或直接執行 run.bat）" -ForegroundColor Gray
Write-Host ""
Write-Host "  2️⃣  在 UI「API 設定」頁貼入任一免費 API Key：" -ForegroundColor White
Write-Host "      Mistral：https://console.mistral.ai/" -ForegroundColor Gray
Write-Host "      Groq：   https://console.groq.com/" -ForegroundColor Gray
Write-Host "      AI Studio：https://aistudio.google.com/" -ForegroundColor Gray
Write-Host ""
Write-Host "  3️⃣  下載音樂生成模型（約 12 GB）：" -ForegroundColor White
Write-Host "      執行 download_models.bat" -ForegroundColor Gray
Write-Host ""
