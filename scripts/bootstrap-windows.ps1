param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    New-Item -ItemType Directory -Path '.tools' -Force | Out-Null
    $archive = Join-Path $projectRoot '.tools\w64devkit-x64-2.10.0.7z.exe'
    $expectedHash = '18d0a4c71a166f8401ab6305781bec5882b40b5e06ba9807c61cb5f3b3c6325e'
    if (-not (Test-Path -LiteralPath $archive)) {
        Invoke-WebRequest -Uri 'https://github.com/skeeto/w64devkit/releases/download/v2.10.0/w64devkit-x64-2.10.0.7z.exe' -OutFile $archive
    }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expectedHash) {
        throw 'C++ toolkit checksum mismatch. Do not execute this archive.'
    }
    if (-not (Test-Path -LiteralPath '.tools\w64devkit\bin\g++.exe')) {
        $extract = Start-Process -FilePath $archive -ArgumentList '-y', '-o.tools' -WindowStyle Hidden -Wait -PassThru
        if ($extract.ExitCode -ne 0) { throw "Toolkit extraction failed: $($extract.ExitCode)" }
    }
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $Python -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 required"'
        if ($LASTEXITCODE -ne 0) { throw 'Use -Python with a Python 3.12 executable.' }
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install --require-hashes -r requirements.lock
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    npm.cmd --prefix frontend ci --ignore-scripts
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    Write-Output 'Setup complete. Run .\scripts\verify.ps1 next.'
} finally {
    Pop-Location
}
