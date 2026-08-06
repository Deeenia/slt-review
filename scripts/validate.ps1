$ErrorActionPreference = "Stop"
$python = (Get-Command python -ErrorAction Stop).Source
& $python (Join-Path $PSScriptRoot "validate_repo.py")
exit $LASTEXITCODE
