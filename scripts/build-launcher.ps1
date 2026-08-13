$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ElectronDist = Join-Path $Root "node_modules\electron\dist"
$LauncherRoot = Join-Path $Root "launcher"
$AppDir = Join-Path $LauncherRoot "App Transcript"
$ElectronExe = Join-Path $AppDir "electron.exe"
$AppExe = Join-Path $AppDir "App Transcript.exe"

if (-not (Test-Path $ElectronDist)) {
    throw "Electron nao encontrado. Rode npm install antes de criar o executavel."
}

if (Test-Path $AppDir) {
    $ResolvedLauncher = (Resolve-Path $LauncherRoot -ErrorAction SilentlyContinue)
    if ($ResolvedLauncher -and $ResolvedLauncher.Path.StartsWith($Root)) {
        Remove-Item -LiteralPath $AppDir -Recurse -Force
    } else {
        throw "Caminho de launcher invalido: $AppDir"
    }
}

New-Item -ItemType Directory -Path $LauncherRoot -Force | Out-Null
Copy-Item -LiteralPath $ElectronDist -Destination $AppDir -Recurse

if (-not (Test-Path $ElectronExe)) {
    throw "Falha ao preparar o Electron portatil."
}

Rename-Item -LiteralPath $ElectronExe -NewName "App Transcript.exe"

$LaunchCmd = Join-Path $AppDir "Abrir App Transcript.cmd"
@"
@echo off
cd /d "$Root"
"$AppExe" "$Root"
"@ | Set-Content -LiteralPath $LaunchCmd -Encoding ASCII

Write-Host "Executavel criado em: $AppExe"
