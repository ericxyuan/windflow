$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$cli=Join-Path $taskRoot '.tools\arduino-cli\arduino-cli.exe'
$config=Join-Path $taskRoot '.tools\arduino-cli.yaml'
$output=Join-Path $taskRoot 'firmware\dist'
New-Item -ItemType Directory -Force -Path $output | Out-Null
& $cli --config-file $config compile --fqbn 'rp2040:rp2040:rpipico:flash=2097152_262144,freq=133' --warnings all --output-dir $output (Join-Path $taskRoot 'firmware\Windflow')
if($LASTEXITCODE -ne 0){throw 'Firmware build failed'}
