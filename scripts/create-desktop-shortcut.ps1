$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$AppExe = Join-Path $Root "launcher\App Transcript\App Transcript.exe"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "App Transcript.lnk"

if (-not (Test-Path $AppExe)) {
    & (Join-Path $PSScriptRoot "build-launcher.ps1")
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $AppExe
$Shortcut.Arguments = "`"$Root`""
$Shortcut.WorkingDirectory = $Root
$Shortcut.IconLocation = "$AppExe,0"
$Shortcut.Description = "App Transcript local"
$Shortcut.Save()

Write-Host "Atalho criado em: $ShortcutPath"
