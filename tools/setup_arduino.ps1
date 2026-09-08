$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$toolsRoot = Join-Path $taskRoot '.tools'
$cliRoot = Join-Path $toolsRoot 'arduino-cli'
New-Item -ItemType Directory -Force -Path $cliRoot | Out-Null
$cliZip = Join-Path $toolsRoot 'arduino-cli.zip'
if (-not (Test-Path -LiteralPath (Join-Path $cliRoot 'arduino-cli.exe'))) {
    Invoke-WebRequest -Uri 'https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Windows_64bit.zip' -OutFile $cliZip
    Expand-Archive -LiteralPath $cliZip -DestinationPath $cliRoot -Force
}
$cli = Join-Path $cliRoot 'arduino-cli.exe'
$dataPath = (Join-Path $toolsRoot 'arduino-data').Replace('\','/')
$userPath = (Join-Path $toolsRoot 'arduino-user').Replace('\','/')
$downloadPath = (Join-Path $toolsRoot 'arduino-downloads').Replace('\','/')
$config = Join-Path $toolsRoot 'arduino-cli.yaml'
@"
board_manager:
  additional_urls:
    - https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
directories:
  data: $dataPath
  user: $userPath
  downloads: $downloadPath
"@ | Set-Content -LiteralPath $config
& $cli --config-file $config core update-index
if ($LASTEXITCODE -ne 0) { throw 'Index update failed' }
& $cli --config-file $config core install rp2040:rp2040@6.1.0
if ($LASTEXITCODE -ne 0) { throw 'Core install failed' }
& $cli --config-file $config lib install 'Adafruit NeoPixel@1.15.2'
if ($LASTEXITCODE -ne 0) { throw 'NeoPixel install failed' }
