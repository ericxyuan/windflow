param([switch]$RebuildRotor)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskPython=Join-Path $taskRoot '.tools\rev-c-cad-venv\Scripts\python.exe'
if(-not(Test-Path -LiteralPath $taskPython)){throw 'Install the pinned CAD environment described in docs/rev-d-150mm-cad.md first.'}
Push-Location $taskRoot
try {
    if($RebuildRotor){
        & $taskPython 'cad/rev_d_rotor.py'
        if($LASTEXITCODE -ne 0){throw 'Rotor geometry or mesh validation failed.'}
    }
    & $taskPython 'cad/rev_d_stage.py'
    if($LASTEXITCODE -ne 0){throw 'Stage geometry or nominal collision validation failed.'}
    & $taskPython 'cad/rev_d_motion.py'
    if($LASTEXITCODE -ne 0){throw 'Motion validation failed.'}
    & $taskPython 'cad/rev_d_export.py'
    if($LASTEXITCODE -ne 0){throw 'Assembly exchange validation failed.'}
} finally {Pop-Location}
