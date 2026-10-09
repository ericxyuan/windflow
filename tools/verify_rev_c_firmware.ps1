$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$hostLog=Join-Path $taskRoot 'build\rev-c-firmware-host.log'
$buildLog=Join-Path $taskRoot 'build\rev-c-firmware-build.log'
& (Join-Path $PSScriptRoot 'test_rev_c_firmware.ps1') *> $hostLog
if($LASTEXITCODE -ne 0){throw 'Rev C host verification failed'}
& (Join-Path $PSScriptRoot 'build_rev_c_firmware.ps1') *> $buildLog
if($LASTEXITCODE -ne 0){throw 'Rev C firmware build failed'}
$hostText=Get-Content -Raw -LiteralPath $hostLog
$buildText=Get-Content -Raw -LiteralPath $buildLog
$hostMatch=[regex]::Match($hostText,'parser/safety/control/display (\d+) checks')
$shippingMatch=[regex]::Match($hostText,'service (\d+) assertions \(motion build flag 0\)')
$qualifiedMatch=[regex]::Match($hostText,'service (\d+) assertions \(motion build flag 1\)')
$flashMatch=[regex]::Match($buildText,'Sketch uses (\d+) bytes')
$ramMatch=[regex]::Match($buildText,'Global variables use (\d+) bytes')
foreach($m in @($hostMatch,$shippingMatch,$qualifiedMatch,$flashMatch,$ramMatch)){
 if(-not $m.Success){throw 'Verification log did not contain the required result'}
}
if($hostText -notmatch 'PASS Rev C distributed build cannot request rotor motion'){throw 'Missing motion inhibit evidence'}
$reportPath=Join-Path $taskRoot 'firmware\WindflowRevC\validation.json'
$report=Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
$report.client_date='2026-10-08'
$report.commands[0].parser_safety_control_display_assertions=[int]$hostMatch.Groups[1].Value
$report.commands[0].shipping_service_assertions=[int]$shippingMatch.Groups[1].Value
$report.commands[0].qualified_host_simulation_service_assertions=[int]$qualifiedMatch.Groups[1].Value
$report.commands[1].program_bytes=[int]$flashMatch.Groups[1].Value
$report.commands[1].static_ram_bytes=[int]$ramMatch.Groups[1].Value
$uf2=Join-Path $taskRoot 'firmware\dist\rev-c\WindflowRevC.ino.uf2'
$report.uf2.sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $uf2).Hash.ToLowerInvariant()
$report.uf2.bytes=(Get-Item -LiteralPath $uf2).Length
foreach($entry in $report.source_sha256.PSObject.Properties){
 $entry.Value=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskRoot $entry.Name)).Hash.ToLowerInvariant()
}
foreach($entry in $report.evidence_logs.PSObject.Properties){
 $entry.Value=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskRoot $entry.Name)).Hash.ToLowerInvariant()
}
$report | Add-Member -NotePropertyName verification_script_sha256 -NotePropertyValue (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLowerInvariant() -Force
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding utf8
Write-Output "PASS $($report.commands[0].parser_safety_control_display_assertions) host assertions; shipping/service gates; Pico build $($report.commands[1].program_bytes) bytes; source and artifact hashes refreshed"
