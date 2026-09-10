$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $taskRoot '.tools\venv\Scripts\python.exe'
$testExe=Join-Path $taskRoot 'build\control-tests.exe'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $testExe) | Out-Null
& $python -m ziglang c++ -std=c++17 -Wall -Wextra -Werror -O1 "-I$(Join-Path $taskRoot 'firmware\Windflow')" (Join-Path $taskRoot 'tests\control_tests.cpp') (Join-Path $taskRoot 'firmware\Windflow\Control.cpp') -o $testExe
if($LASTEXITCODE -ne 0){throw 'Host test compilation failed'}
& $testExe
if($LASTEXITCODE -ne 0){throw 'Host control tests failed'}
