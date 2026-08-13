$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

Push-Location $Root
try {
    if (-not (Test-Path $Python)) {
        throw "Python da .venv nao encontrado. Rode scripts/install.ps1 antes."
    }

    Write-Host "== Python compile =="
    & $Python -m py_compile app\main.py app\models.py app\silence.py app\transcriber.py app\engine.py app\cuda_paths.py

    Write-Host "== Web check =="
    npm run check:web

    Write-Host "== Desktop check =="
    npm run check:desktop

    Write-Host "== API health, se o app estiver aberto =="
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/health" -TimeoutSec 5
        $health | ConvertTo-Json -Depth 4
    } catch {
        Write-Host "API health nao respondeu. Abra o app desktop para validar manualmente."
    }

    Write-Host "Release check concluido."
} finally {
    Pop-Location
}
