[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$SkipInstall,
    [switch]$SkipTests,
    [switch]$KeepDatabase,
    [int]$PostgresPort = 55432
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $RepoRoot 'backend'
$Frontend = Join-Path $RepoRoot 'frontend'
$Venv = Join-Path $RepoRoot '.ci-venv'
$DbContainer = 'primeerp-release-gate-postgres'
$Results = [System.Collections.Generic.List[object]]::new()
$StartedDb = $false
$GateFailed = $false

function Write-Step([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Invoke-Gate([string]$Name, [scriptblock]$Action, [switch]$Optional) {
    Write-Host "[RUN ] $Name" -ForegroundColor Yellow
    try {
        & $Action
        $Results.Add([pscustomobject]@{ Check=$Name; Status='PASS'; Detail='' })
        Write-Host "[PASS] $Name" -ForegroundColor Green
        return $true
    }
    catch {
        $detail = $_.Exception.Message
        $status = if ($Optional) { 'WARN' } else { 'FAIL' }
        $Results.Add([pscustomobject]@{ Check=$Name; Status=$status; Detail=$detail })
        Write-Host "[$status] $Name - $detail" -ForegroundColor $(if ($Optional) { 'DarkYellow' } else { 'Red' })
        if (-not $Optional) { $script:GateFailed = $true }
        return $false
    }
}

function Invoke-Native([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable exited with code $LASTEXITCODE"
    }
}

function Invoke-Python([string]$WorkingDirectory, [string[]]$Arguments) {
    Push-Location $WorkingDirectory
    try { Invoke-Native $script:PythonExe $Arguments }
    finally { Pop-Location }
}

function Invoke-Alembic([string]$WorkingDirectory, [string[]]$Arguments) {
    Push-Location $WorkingDirectory
    try { Invoke-Native $script:AlembicExe $Arguments }
    finally { Pop-Location }
}

function Invoke-Npm([string]$WorkingDirectory, [string[]]$Arguments) {
    Push-Location $WorkingDirectory
    try {
        $npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue)
        if ($npm) { Invoke-Native $npm.Source $Arguments }
        else { Invoke-Native 'npm' $Arguments }
    }
    finally { Pop-Location }
}

function Test-Command([string]$CommandName, [string]$DisplayName) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "$DisplayName is not available on PATH"
    }
}

function Test-Python310([string]$PythonPath) {
    if (-not (Test-Path $PythonPath)) { return $false }
    $version = (& $PythonPath --version 2>&1).ToString()
    Write-Host "  $version"
    return ($version -match '^Python 3\.10\.')
}

try {
    Write-Host "Repository: $RepoRoot" -ForegroundColor DarkGray

    Write-Step 'Runtime prerequisites'
    Invoke-Gate 'Git repository' {
        Push-Location $RepoRoot
        try {
            Invoke-Native 'git' @('rev-parse','--is-inside-work-tree')
            & git status --short
            if (Test-Path (Join-Path $RepoRoot '.git\MERGE_HEAD')) {
                throw 'Repository is in the middle of an unresolved merge. Abort/finish the merge before running the release gate.'
            }
        } finally { Pop-Location }
    }

    Invoke-Gate 'Python 3.10 available' {
        Test-Command 'py' 'Python launcher'
        Invoke-Native 'py' @('-3.10','--version')
        $script:PythonExe = Join-Path $Venv 'Scripts\python.exe'
        if (-not (Test-Python310 $script:PythonExe)) {
            if (Test-Path $Venv) { Remove-Item $Venv -Recurse -Force }
            Invoke-Native 'py' @('-3.10','-m','venv',$Venv)
            $script:PythonExe = Join-Path $Venv 'Scripts\python.exe'
        }
        if (-not (Test-Python310 $script:PythonExe)) {
            throw 'The CI virtual environment is not using Python 3.10.'
        }
        $script:AlembicExe = Join-Path $Venv 'Scripts\alembic.exe'
    }

    Invoke-Gate 'Node.js 20+ available' {
        Test-Command 'node' 'Node.js'
        Test-Command 'npm.cmd' 'npm'
        $version = (& node --version).ToString()
        $major = [int]$version.TrimStart('v').Split('.')[0]
        Write-Host "  $version"
        & npm.cmd --version
        if ($major -lt 20) { throw "Node.js 20+ required; found $major" }
    }

    Invoke-Gate 'Docker available' {
        if ($SkipDocker) { throw 'Docker checks skipped by -SkipDocker' }
        Test-Command 'docker' 'Docker'
        Invoke-Native 'docker' @('version')
    } -Optional:$SkipDocker

    Write-Step 'Backend'
    if (-not $SkipInstall) {
        Invoke-Gate 'Create CI virtual environment' {
            if (-not (Test-Python310 $script:PythonExe)) {
                if (Test-Path $Venv) { Remove-Item $Venv -Recurse -Force }
                Invoke-Native 'py' @('-3.10','-m','venv',$Venv)
            }
            if (-not (Test-Python310 $script:PythonExe)) { throw 'Failed to create Python 3.10 virtual environment' }
        }
        Invoke-Gate 'Install backend dependencies' {
            Invoke-Python $Backend @('-m','pip','install','--upgrade','pip')
            Invoke-Python $Backend @('-m','pip','install','-r','requirements.txt')
            Invoke-Python $Backend @('-m','pip','install','pytest')
        }
    }

    Invoke-Gate 'Compile Python sources' {
        Invoke-Python $Backend @('-m','compileall','-q','app')
    }

    Invoke-Gate 'Modular architecture check' {
        Invoke-Python $Backend @('scripts/check_modular_architecture.py')
    }

    Invoke-Gate 'API security boundary scan' {
        Invoke-Python $Backend @('scripts/check_api_security.py')
    }

    Invoke-Gate 'Application import smoke test' {
        $env:DATABASE_URL = 'sqlite:///./release_gate_smoke.db'
        $env:APP_ENV = 'test'
        Invoke-Python $Backend @('scripts/smoke_import.py')
        Remove-Item (Join-Path $Backend 'release_gate_smoke.db') -Force -ErrorAction SilentlyContinue
        Remove-Item (Join-Path $RepoRoot 'release_gate_smoke.db') -Force -ErrorAction SilentlyContinue
    }

    Invoke-Gate 'Production configuration safety checks' {
        $env:APP_ENV = 'production'
        $env:DEBUG = 'false'
        $env:DATABASE_URL = 'sqlite:///./unsafe.db'
        $env:SECRET_KEY = 'your-secret-key-change-this-in-production'
        $env:CORS_ORIGINS = 'https://erp.example.com'
        Invoke-Python $Backend @('scripts/check_production_config.py')
    }

    if (-not $SkipDocker) {
        Write-Step 'PostgreSQL + Alembic'
        Invoke-Gate 'Start isolated PostgreSQL' {
            & docker rm -f $DbContainer 2>$null | Out-Null
            Invoke-Native 'docker' @('run','-d','--name',$DbContainer,'-e','POSTGRES_USER=primeerp_ci','-e','POSTGRES_PASSWORD=primeerp_ci','-e','POSTGRES_DB=primeerp_ci','-p',"${PostgresPort}:5432",'postgres:17')
            $script:StartedDb = $true
            for ($i = 0; $i -lt 30; $i++) {
                & docker exec $DbContainer pg_isready -U primeerp_ci -d primeerp_ci 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) { return }
                Start-Sleep -Seconds 2
            }
            throw 'PostgreSQL did not become ready within 60 seconds'
        }

        $env:DATABASE_URL = "postgresql+psycopg://primeerp_ci:primeerp_ci@127.0.0.1:$PostgresPort/primeerp_ci"
        $env:APP_ENV = 'test'

        Invoke-Gate 'Alembic upgrade head' {
            Invoke-Alembic $Backend @('upgrade','head')
        }
        Invoke-Gate 'Require single Alembic head' {
            Push-Location $Backend
            try {
                $heads = @(& $script:AlembicExe heads 2>&1)
                if ($LASTEXITCODE -ne 0) { throw "alembic heads exited with code $LASTEXITCODE" }
                $heads | ForEach-Object { Write-Host "  $_" }
                $count = @($heads | Where-Object { $_ -match '\(head\)' }).Count
                if ($count -ne 1) { throw "Expected exactly one Alembic head; found $count" }
            } finally { Pop-Location }
        }
        Invoke-Gate 'Alembic check' {
            Invoke-Alembic $Backend @('check')
        }
    }

    if (-not $SkipTests) {
        Invoke-Gate 'Backend tests' {
            $testDir = Join-Path $Backend 'tests'
            if (Test-Path $testDir) {
                Invoke-Python $Backend @('-m','pytest','-q')
            } else {
                Write-Host '  No backend tests directory found; compile/import/migration checks still ran.' -ForegroundColor DarkYellow
            }
        }
    }

    Write-Step 'Frontend'
    if (-not $SkipInstall) {
        Invoke-Gate 'Install frontend dependencies' {
            Invoke-Npm $Frontend @('ci')
        }
    }
    Invoke-Gate 'Frontend typecheck' {
        Invoke-Npm $Frontend @('run','typecheck')
    }
    Invoke-Gate 'Frontend lint' {
        Invoke-Npm $Frontend @('run','lint')
    }
    Invoke-Gate 'Frontend production build' {
        Invoke-Npm $Frontend @('run','build')
    }

    if (-not $SkipDocker) {
        Write-Step 'Docker images'
        Invoke-Gate 'Docker Compose configuration' {
            $envFile = Join-Path $RepoRoot '.env.docker.example'
            if (-not (Test-Path $envFile)) { throw '.env.docker.example not found' }
            Invoke-Native 'docker' @('compose','--env-file',$envFile,'config','-q')
        }
        Invoke-Gate 'Backend Docker build' {
            Invoke-Native 'docker' @('build','--pull','-t','primeerp-backend:release-gate',(Join-Path $RepoRoot 'backend'))
            Invoke-Native 'docker' @('run','--rm','primeerp-backend:release-gate','python','-m','compileall','-q','app')
        }
        Invoke-Gate 'Frontend Docker build' {
            Invoke-Native 'docker' @('build','--pull','-t','primeerp-frontend:release-gate',(Join-Path $RepoRoot 'frontend'))
        }
    }
}
finally {
    if ($StartedDb -and -not $KeepDatabase) {
        Write-Step 'Cleanup'
        & docker rm -f $DbContainer 2>$null | Out-Null
    }
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:APP_ENV -ErrorAction SilentlyContinue
    Remove-Item Env:DEBUG -ErrorAction SilentlyContinue
    Remove-Item Env:SECRET_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:CORS_ORIGINS -ErrorAction SilentlyContinue
}

Write-Host "`n================ RELEASE GATE SUMMARY ================" -ForegroundColor Cyan
$Results | Format-Table -AutoSize
$failed = @($Results | Where-Object Status -eq 'FAIL')
$warnings = @($Results | Where-Object Status -eq 'WARN')
Write-Host "PASS: $(@($Results | Where-Object Status -eq 'PASS').Count)  WARN: $($warnings.Count)  FAIL: $($failed.Count)"
if ($failed.Count -gt 0) {
    Write-Host "`nRELEASE GATE: FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "`nRELEASE GATE: PASSED" -ForegroundColor Green
exit 0
