$ErrorActionPreference = "Stop"

Write-Host "Este script tenta instalar o runtime CUDA oficial para acelerar o App Transcript."
Write-Host "Ele nao cria DLLs falsas; ele instala/configura DLLs oficiais NVIDIA."
Write-Host ""

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Tentando instalar NVIDIA CUDA Toolkit pelo winget..."
    winget install --id Nvidia.CUDA --source winget --accept-package-agreements --accept-source-agreements
} else {
    Write-Host "winget nao encontrado."
    Write-Host "Instale manualmente o CUDA Toolkit 12.x em https://developer.nvidia.com/cuda-downloads"
}

Write-Host ""
Write-Host "Depois de instalar, feche e abra o App Transcript e rode:"
Write-Host ".\scripts\check-gpu.ps1"
