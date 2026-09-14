$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$originalPath = $env:PATH
Push-Location $projectRoot
try {
    $env:PATH = (Join-Path $projectRoot '.tools\w64devkit\bin') + ';' + $env:PATH
    New-Item -ItemType Directory -Path 'artifacts' -Force | Out-Null
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
    if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }
    cmake --build build
    if ($LASTEXITCODE -ne 0) { throw 'C++ build failed.' }
    ctest --test-dir build --output-on-failure --output-junit "$projectRoot/artifacts/cpp-tests.xml"
    if ($LASTEXITCODE -ne 0) { throw 'C++ tests failed.' }
    & '.\.venv\Scripts\python.exe' -m pytest -q --junitxml=artifacts/python-tests.xml
    if ($LASTEXITCODE -ne 0) { throw 'Python or integration tests failed.' }
    & '.\.venv\Scripts\ruff.exe' check backend scripts
    if ($LASTEXITCODE -ne 0) { throw 'Python lint failed.' }
    & '.\.venv\Scripts\python.exe' scripts/export_contracts.py --check
    if ($LASTEXITCODE -ne 0) { throw 'Committed schemas are stale.' }
    & '.\.venv\Scripts\python.exe' -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency compatibility check failed.' }
    npm.cmd --prefix frontend run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend checks failed.' }
    Write-Output 'Foundation verification passed. Reports are in artifacts/.'
} finally {
    $env:PATH = $originalPath
    Pop-Location
}
