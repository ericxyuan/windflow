$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$localTools = Join-Path $taskRoot '.tools'
$archiveTool = Join-Path $localTools '7zip'
$kicadRoot = Join-Path $localTools 'kicad-10.0.6'
New-Item -ItemType Directory -Force -Path $localTools | Out-Null
$sevenInstaller = Join-Path $localTools '7z2603-x64.exe'
$sevenBootstrap = Join-Path $localTools '7zr.exe'
$kicadInstaller = Join-Path $localTools 'kicad-10.0.6-x86_64.exe'
$downloads = @(
    @{ path=$sevenInstaller; url='https://github.com/ip7z/7zip/releases/download/26.03/7z2603-x64.exe' },
    @{ path=$sevenBootstrap; url='https://github.com/ip7z/7zip/releases/download/26.03/7zr.exe' },
    @{ path=$kicadInstaller; url='https://github.com/KiCad/kicad-source-mirror/releases/download/10.0.6/kicad-10.0.6-x86_64.exe' }
)
foreach ($item in $downloads) {
    if (-not (Test-Path -LiteralPath $item.path)) {
        Write-Output "Downloading $([IO.Path]::GetFileName($item.path))"
        Invoke-WebRequest -Uri $item.url -OutFile ($item.path + '.tmp')
        # Cloud-backed folders may keep the downloaded temporary file locked
        # against rename. A read/copy preserves it and avoids another download.
        Copy-Item -LiteralPath ($item.path + '.tmp') -Destination $item.path
    }
}
$signature = Get-AuthenticodeSignature -LiteralPath $kicadInstaller
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'KiCad Services Corporation') {
    throw 'KiCad signature is not valid or does not identify the official publisher'
}
if (-not (Test-Path -LiteralPath (Join-Path $archiveTool '7z.exe'))) {
    # Extract the embedded archive without elevation or an installation wizard.
    & $sevenBootstrap x $sevenInstaller "-o$archiveTool" -y
    if ($LASTEXITCODE -ne 0) { throw 'Archive tool extraction failed' }
}
if (-not (Test-Path -LiteralPath (Join-Path $kicadRoot 'bin/kicad-cli.exe'))) {
    # Extract the signed installer; do not run KiCad's installation wizard.
    & (Join-Path $archiveTool '7z.exe') x $kicadInstaller "-o$kicadRoot" -y
    if ($LASTEXITCODE -ne 0) { throw 'KiCad extraction failed' }
}
$manifest = foreach ($item in $downloads) {
    @{ name=[IO.Path]::GetFileName($item.path); url=$item.url; sha256=(Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash.ToLowerInvariant() }
}
@{ version='10.0.6'; official_download_page='https://www.kicad.org/download/windows/'; signature_status=[string]$signature.Status; signer=$signature.SignerCertificate.Subject; downloads=@($manifest) } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'tools/kicad-runtime.json') -Encoding utf8
& (Join-Path $kicadRoot 'bin/kicad-cli.exe') version
if ($LASTEXITCODE -ne 0) { throw 'Extracted KiCad CLI failed' }
