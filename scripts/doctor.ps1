$ErrorActionPreference = "Continue"

Write-Host "Python:"
python --version

Write-Host ""
Write-Host "FFmpeg:"
ffmpeg -version | Select-Object -First 1

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (Test-Path $python) {
    Write-Host ""
    Write-Host "Torch/CUDA:"
    & $python -c "import torch; print('torch', torch.__version__); print('cuda_available', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

    Write-Host ""
    Write-Host "CTranslate2/CUDA:"
    & $python -c "import ctranslate2; print('cuda_device_count', ctranslate2.get_cuda_device_count())"

    Write-Host ""
    Write-Host "Dependencias de transcricao:"
    & $python -c "import faster_whisper; print('faster_whisper OK')"

    Write-Host ""
    Write-Host "Dependencias opcionais de audio:"
    & $python -c "import importlib.util; print('demucs', 'OK' if importlib.util.find_spec('demucs') else 'NAO instalado'); print('df', 'OK' if importlib.util.find_spec('df') else 'NAO instalado')"
} else {
    Write-Host ""
    Write-Host "Ambiente virtual ainda nao existe. Rode .\scripts\install.ps1"
}
