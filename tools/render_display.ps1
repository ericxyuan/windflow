$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $taskRoot '.tools\venv\Scripts\python.exe'
$gfx=Join-Path $taskRoot '.tools\arduino-user\libraries\Adafruit_GFX_Library'
$exe=Join-Path $taskRoot 'build\display-preview.exe'
$frames=Join-Path $taskRoot 'build\screen-previews'
New-Item -ItemType Directory -Force -Path $frames | Out-Null
# Compile the same DisplayLayout.cpp and unchanged Adafruit GFX used on the Pico.
# Only platform/bus declarations are mocked; all graphics and fonts are real GFX.
& $python -m ziglang c++ -std=c++17 -DARDUINO=100 "-I$(Join-Path $taskRoot 'tests\display_platform')" "-I$gfx" "-I$(Join-Path $taskRoot 'firmware\Windflow')" (Join-Path $taskRoot 'tests\display_preview.cpp') (Join-Path $taskRoot 'firmware\Windflow\DisplayLayout.cpp') (Join-Path $taskRoot 'firmware\Windflow\DisplayView.cpp') (Join-Path $taskRoot 'firmware\Windflow\Control.cpp') (Join-Path $gfx 'Adafruit_GFX.cpp') -o $exe
if($LASTEXITCODE -ne 0){throw 'Display preview compilation failed'}
& $exe $frames
if($LASTEXITCODE -ne 0){throw 'Display pixel comparison or rendering failed'}
& $python (Join-Path $PSScriptRoot 'render_display.py')
if($LASTEXITCODE -ne 0){throw 'Display preview composition failed'}
