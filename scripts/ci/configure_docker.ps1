$ErrorActionPreference = 'Stop'

# The self-hosted runner runs as a service account and must never probe a
# developer's private Docker Desktop installation. Provision isolated,
# version-pinned official Docker client binaries that are readable by CI.
$root = Join-Path $env:RUNNER_TEMP 'primeerp-docker-cli'
$bin = Join-Path $root 'bin'
$config = Join-Path $root 'config'
$plugins = Join-Path $config 'cli-plugins'
New-Item -ItemType Directory -Force -Path $bin, $plugins | Out-Null

$dockerExe = Join-Path $bin 'docker.exe'
$composeExe = Join-Path $plugins 'docker-compose.exe'
$dockerVersion = '29.8.0'
$composeVersion = '5.5.1'
$dockerUrl = "https://download.docker.com/win/static/stable/x86_64/docker-$dockerVersion.zip"
$composeUrl = "https://github.com/docker/compose/releases/download/v$composeVersion/docker-compose-windows-x86_64.exe"

if (-not (Test-Path -LiteralPath $dockerExe -PathType Leaf)) {
    $zip = Join-Path $root "docker-$dockerVersion.zip"
    Invoke-WebRequest -UseBasicParsing -Uri $dockerUrl -OutFile $zip
    $extract = Join-Path $root 'extract'
    if (Test-Path -LiteralPath $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $extract -Force
    $candidate = Get-ChildItem -LiteralPath $extract -Filter docker.exe -Recurse -File -ErrorAction Stop | Select-Object -First 1
    if (-not $candidate) { throw 'Official Docker CLI archive did not contain docker.exe.' }
    Copy-Item -LiteralPath $candidate.FullName -Destination $dockerExe -Force
}

if (-not (Test-Path -LiteralPath $composeExe -PathType Leaf)) {
    Invoke-WebRequest -UseBasicParsing -Uri $composeUrl -OutFile $composeExe
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
