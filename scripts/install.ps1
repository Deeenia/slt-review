param(
    [string]$CodexHome,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$python = (Get-Command python -ErrorAction Stop).Source
$arguments = @((Join-Path $PSScriptRoot "manage.py"), "install")
if ($CodexHome) { $arguments += @("--codex-home", $CodexHome) }
if ($Force) { $arguments += "--force" }
& $python @arguments
exit $LASTEXITCODE
