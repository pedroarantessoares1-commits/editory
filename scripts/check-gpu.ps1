$ErrorActionPreference = "Continue"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "Verificando GPU e DLLs CUDA para App Transcript"
Write-Host ""

if (-not (Test-Path $python)) {
    Write-Host "Ambiente virtual nao encontrado. Rode .\scripts\install.ps1 primeiro."
    exit 1
}

& $python -c "from app.cuda_paths import CUDA_DLL_PATHS; print('paths adicionados:'); [print(' -', p) for p in CUDA_DLL_PATHS]"

Write-Host ""
Write-Host "CTranslate2:"
& $python -c "import ctranslate2; print('version', ctranslate2.__version__); print('cuda_device_count', ctranslate2.get_cuda_device_count())"

Write-Host ""
Write-Host "DLLs encontradas:"
$dlls = "cublas64_12.dll", "cudnn64_9.dll", "cudart64_12.dll"
$searchRoots = @(
    (Join-Path $root ".venv"),
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
)

foreach ($dll in $dlls) {
    $found = @()
    foreach ($searchRoot in $searchRoots) {
        if (Test-Path $searchRoot) {
            $found += Get-ChildItem -LiteralPath $searchRoot -Recurse -Filter $dll -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
        }
    }
    if ($found.Count -gt 0) {
        Write-Host "OK $dll"
        $found | Select-Object -First 3 | ForEach-Object { Write-Host " - $_" }
    } else {
        Write-Host "FALTA $dll"
    }
}

Write-Host ""
Write-Host "Se faltar cublas/cudnn, instale o CUDA Toolkit 12.x da NVIDIA ou rode scripts\install-gpu-runtime.ps1."
