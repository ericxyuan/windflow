$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $taskRoot '.tools\venv\Scripts\python.exe'
$source=Join-Path $taskRoot 'firmware\WindflowRevC'
$output=Join-Path $taskRoot 'build'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$exe=Join-Path $output 'rev-c-esc-tests.exe'
& $python -m ziglang c++ -std=c++17 -Wall -Wextra -Werror -O1 -DWF_MOTION_BUILD_QUALIFIED=1 "-I$source" (Join-Path $taskRoot 'tests\rev_c_esc_tests.cpp') (Join-Path $source 'Control.cpp') (Join-Path $source 'EscSafety.cpp') (Join-Path $source 'DisplayView.cpp') -o $exe
if($LASTEXITCODE -ne 0){throw 'Rev C simulation compilation failed'}
& $exe
if($LASTEXITCODE -ne 0){throw 'Rev C simulation failed'}
$exe=Join-Path $output 'rev-c-esc-shipping-tests.exe'
& $python -m ziglang c++ -std=c++17 -Wall -Wextra -Werror -O1 "-I$source" (Join-Path $taskRoot 'tests\rev_c_esc_shipping_tests.cpp') (Join-Path $source 'Control.cpp') (Join-Path $source 'EscSafety.cpp') -o $exe
if($LASTEXITCODE -ne 0){throw 'Rev C shipping compilation failed'}
& $exe
if($LASTEXITCODE -ne 0){throw 'Rev C shipping safety gate failed'}
foreach($qualified in @(0,1)){
 $exe=Join-Path $output "rev-c-esc-service-$qualified-tests.exe"
 & $python -m ziglang c++ -std=c++17 -Wall -Wextra -Werror -O1 "-DWF_MOTION_BUILD_QUALIFIED=$qualified" "-I$(Join-Path $taskRoot 'tests\service_platform')" "-I$source" (Join-Path $taskRoot 'tests\rev_c_esc_service_tests.cpp') (Join-Path $source 'Service.cpp') (Join-Path $source 'Control.cpp') (Join-Path $source 'EscSafety.cpp') -o $exe
 if($LASTEXITCODE -ne 0){throw 'Rev C service compilation failed'}
 & $exe
 if($LASTEXITCODE -ne 0){throw 'Rev C service assertions failed'}
}
