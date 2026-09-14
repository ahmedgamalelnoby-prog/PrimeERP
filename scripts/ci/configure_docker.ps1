$ErrorActionPreference = 'Stop'

# The self-hosted runner runs as a service account and must never probe a
# developer's private Docker Desktop installation. That probe can itself
# raise UnauthorizedAccessException before we can fall back to a download.
# Always provision an isolated, official Docker CLI + Compose plugin for CI.
$root = Join-Path $env:RUNNER_TEMP 'primeerp-docker-cli'
$bin = Join-Path $root 'bin'
$config = Join-Path $root 'config'
$plugins = Join-Path $config 'cli-plugins'
New-Item -ItemType Directory -Force -Path $bin, $plugins | Out-Null

$dockerExe = Join-Path $bin 'docker.exe'
$headers = @{ 'User-Agent' = 'PrimeERP-CI' }

if (-not (Test-Path -LiteralPath $dockerExe -PathType Leaf)) {
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/docker/cli/releases/latest' -Headers $headers
    $asset = $release.assets |
        Where-Object { $_.name -match '^docker-.*windows.*(x86_64|amd64).*\.zip$' -or $_.name -match '^docker-.*\.zip$' } |
        Select-Object -First 1
    if (-not $asset) { throw 'Official Docker CLI Windows asset not found.' }
    $zip = Join-Path $root 'docker-cli.zip'
    Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -Headers $headers -OutFile $zip
    $extract = Join-Path $root 'extract'
    if (Test-Path -LiteralPath $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $extract -Force
    $candidate = Get-ChildItem -LiteralPath $extract -Filter docker.exe -Recurse -File -ErrorAction Stop | Select-Object -First 1
    if (-not $candidate) { throw 'Docker CLI archive did not contain docker.exe.' }
    Copy-Item -LiteralPath $candidate.FullName -Destination $dockerExe -Force
}

$composeExe = Join-Path $plugins 'docker-compose.exe'
if (-not (Test-Path -LiteralPath $composeExe -PathType Leaf)) {
    $composeRelease = Invoke-RestMethod -Uri 'https://api.github.com/repos/docker/compose/releases/latest' -Headers $headers
    $composeAsset = $composeRelease.assets |
        Where-Object { $_.name -eq 'docker-compose-windows-x86_64.exe' -or $_.name -eq 'docker-compose-windows-amd64.exe' } |
        Select-Object -First 1
    if (-not $composeAsset) { throw 'Official Docker Compose Windows asset not found.' }
    Invoke-WebRequest -UseBasicParsing -Uri $composeAsset.browser_download_url -Headers $headers -OutFile $composeExe
}

$bin | Out-File -FilePath $env:GITHUB_PATH -Encoding utf8 -Append
"DOCKER_CONFIG=$config" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"DOCKER_HOST=npipe:////./pipe/dockerDesktopLinuxEngine" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
$env:PATH = "$bin;$env:PATH"
$env:DOCKER_CONFIG = $config
$env:DOCKER_HOST = 'npipe:////./pipe/dockerDesktopLinuxEngine'

& $dockerExe version
if ($LASTEXITCODE -ne 0) { throw 'Docker CLI was provisioned, but the runner cannot connect to the Docker Desktop Linux engine.' }
& $dockerExe compose version
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose plugin is not usable.' }
