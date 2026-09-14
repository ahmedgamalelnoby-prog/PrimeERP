$ErrorActionPreference = 'Stop'

$root = Join-Path $env:RUNNER_TEMP 'primeerp-docker-cli'
$bin = Join-Path $root 'bin'
$config = Join-Path $root 'config'
$plugins = Join-Path $config 'cli-plugins'
New-Item -ItemType Directory -Force -Path $bin, $plugins | Out-Null

$dockerExe = Join-Path $bin 'docker.exe'
if (-not (Test-Path $dockerExe)) {
    $known = @(
        'C:\Users\Admin\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe',
        'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($known) {
        Copy-Item $known $dockerExe -Force
    } else {
        $headers = @{ 'User-Agent' = 'PrimeERP-CI' }
        $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/docker/cli/releases/latest' -Headers $headers
        $asset = $release.assets | Where-Object { $_.name -match '^docker-.*\.zip$' } | Select-Object -First 1
        if (-not $asset) { throw 'Official Docker CLI Windows asset not found.' }
        $zip = Join-Path $root 'docker-cli.zip'
        Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -Headers $headers -OutFile $zip
        $extract = Join-Path $root 'extract'
        if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
        Expand-Archive -Path $zip -DestinationPath $extract -Force
        $candidate = Get-ChildItem $extract -Filter docker.exe -Recurse | Select-Object -First 1
        if (-not $candidate) { throw 'Docker CLI archive did not contain docker.exe.' }
        Copy-Item $candidate.FullName $dockerExe -Force
    }
}

$composeExe = Join-Path $plugins 'docker-compose.exe'
if (-not (Test-Path $composeExe)) {
    $headers = @{ 'User-Agent' = 'PrimeERP-CI' }
    $composeRelease = Invoke-RestMethod -Uri 'https://api.github.com/repos/docker/compose/releases/latest' -Headers $headers
    $composeAsset = $composeRelease.assets | Where-Object { $_.name -eq 'docker-compose-windows-x86_64.exe' } | Select-Object -First 1
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
if ($LASTEXITCODE -ne 0) { throw 'Docker CLI cannot connect to Docker Desktop Linux engine.' }
& $dockerExe compose version
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose plugin is not usable.' }
