$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Ambiente virtual nao encontrado. Instalando dependencias..."
    & (Join-Path $PSScriptRoot "install.ps1")
}

Set-Location $root
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8765

