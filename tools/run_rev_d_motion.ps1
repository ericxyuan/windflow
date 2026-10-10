$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskPython=Join-Path $taskRoot '.tools\rev-c-cad-venv\Scripts\python.exe'
$taskOutput=Join-Path $taskRoot 'build\rev-d-cad'
New-Item -ItemType Directory -Force -Path $taskOutput | Out-Null
$taskResult=Join-Path $taskOutput 'motion-process-result.json'
$taskLog=Join-Path $taskOutput 'motion-run.log'
$taskCode=1
Push-Location $taskRoot
try {
    @{status='RUNNING';started_utc=[DateTime]::UtcNow.ToString('o');pid=$PID} | ConvertTo-Json | Set-Content -LiteralPath $taskResult -Encoding utf8
    & $taskPython 'cad/rev_d_motion.py' *> $taskLog
    $taskCode=$LASTEXITCODE
} catch {
    $_ | Out-String | Add-Content -LiteralPath $taskLog
} finally {
    @{status='COMPLETED';exit_code=$taskCode;completed_utc=[DateTime]::UtcNow.ToString('o');pid=$PID} | ConvertTo-Json | Set-Content -LiteralPath $taskResult -Encoding utf8
    Pop-Location
}
exit $taskCode
