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

function Write-Step([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Invoke-Gate([string]$Name, [scriptblock]$Action, [switch]$Optional) {
    Write-Host "[RUN ] $Name" -ForegroundColor Yellow
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) { throw "Command exited with code $LASTEXITCODE" }
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

function Invoke-Python([string]$WorkingDirectory, [string[]]$Arguments) {
    Push-Location $WorkingDirectory
    try { & $script:PythonExe @Arguments; if ($LASTEXITCODE -ne 0) { throw "python exited with code $LASTEXITCODE" } }
    finally { Pop-Location }
}

function Invoke-Npm([string]$WorkingDirectory, [string[]]$Arguments) {
    Push-Location $WorkingDirectory
    try { & npm @Arguments; if ($LASTEXITCODE -ne 0) { throw "npm exited with code $LASTEXITCODE" } }
    finally { Pop-Location }
}

function Test-Command([string]$CommandName, [string]$DisplayName) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "$DisplayName is not available on PATH"
    }
}

$GateFailed = $false

try {
    if ((Get-Location).Path -ne $RepoRoot) {
        Write-Host "Repository: $RepoRoot" -ForegroundColor DarkGray
    }

    Write-Step 'Runtime prerequisites'
    Invoke-Gate 'Git repository' {
        Push-Location $RepoRoot
        try {
            & git rev-parse --is-inside-work-tree | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Not a Git repository' }
            & git status --short
        } finally { Pop-Location }
    }

    Invoke-Gate 'Python 3.10 available' {
        if (Test-Path (Join-Path $Venv 'Scripts/python.exe')) {
            $script:PythonExe = Join-Path $Venv 'Scripts/python.exe'
        } else {
            Test-Command 'py' 'Python launcher'
            & py -3.10 -c "import sys; print(sys.version); raise SystemExit(0 if sys.version_info[:2] == (3,10) else 1)"
            if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 is not installed. Install Python 3.10 or create .ci-venv with Python 3.10.' }
            $script:PythonExe = 'py'
        }
        & $script:PythonExe --version
    }

    Invoke-Gate 'Node.js 20+ available' {
        Test-Command 'node' 'Node.js'
        $major = [int](& node -p "process.versions.node.split('.')[0]")
        & node --version
        & npm --version
        if ($major -lt 20) { throw "Node.js 20+ required; found $major" }
    }

    Invoke-Gate 'Docker available' {
        if ($SkipDocker) { throw 'SKIPPED' }
        Test-Command 'docker' 'Docker'
        & docker version
        if ($LASTEXITCODE -ne 0) { throw 'Docker daemon is not available' }
    } -Optional:$SkipDocker

    Write-Step 'Backend'
    if (-not $SkipInstall) {
        Invoke-Gate 'Create CI virtual environment' {
            if (-not (Test-Path (Join-Path $Venv 'Scripts/python.exe'))) {
                Test-Command 'py' 'Python launcher'
                & py -3.10 -m venv $Venv
                if ($LASTEXITCODE -ne 0) { throw 'Failed to create Python 3.10 virtual environment' }
            }
            $script:PythonExe = Join-Path $Venv 'Scripts/python.exe'
            & $script:PythonExe --version
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
        $patterns = @(
            @{ Pattern='from app.modules.[^\r\n]+ import .*database'; Path='backend/app'; Message='Module imports database internals' },
            @{ Pattern='from app.modules.[^\r\n]+ import .*models'; Path='backend/app/modules'; Message='Cross-module model import requires review' }
        )
        foreach ($rule in $patterns) {
            $hits = Get-ChildItem (Join-Path $RepoRoot $rule.Path) -Recurse -File -Include *.py |
                Select-String -Pattern $rule.Pattern -ErrorAction SilentlyContinue
            if ($hits) {
                $hits | ForEach-Object { Write-Host "  $($_.Path):$($_.LineNumber): $($_.Line.Trim())" }
                throw $rule.Message
            }
        }
    }

    Invoke-Gate 'API security boundary scan' {
        $routers = Get-ChildItem (Join-Path $Backend 'app') -Recurse -File -Include *router*.py,*.py
        $dangerous = $routers | Select-String -Pattern 'Depends\(get_current_user\)|require_permission\(' -ErrorAction SilentlyContinue
        if (-not $dangerous) { throw 'No authenticated API boundaries found; review scan configuration' }
        Write-Host "  Authenticated API boundaries detected: $($dangerous.Count)"
    }

    Invoke-Gate 'Application import smoke test' {
        $env:DATABASE_URL = 'sqlite:///./release_gate_smoke.db'
        $env:APP_ENV = 'test'
        Invoke-Python $Backend @('-c','import main; print("PrimeERP application import: OK")')
        Remove-Item (Join-Path $Backend 'release_gate_smoke.db') -Force -ErrorAction SilentlyContinue
        Remove-Item (Join-Path $RepoRoot 'release_gate_smoke.db') -Force -ErrorAction SilentlyContinue
    }

    Invoke-Gate 'Production configuration safety checks' {
        $env:APP_ENV = 'production'
        $env:DEBUG = 'true'
        $env:DATABASE_URL = 'sqlite:///./unsafe.db'
        $env:SECRET_KEY = 'your-secret-key-change-this-in-production'
        $env:CORS_ORIGINS = 'https://erp.example.com'
        $code = @'
from app.core.config import Settings
try:
    Settings()
except ValueError:
    print('Unsafe production configuration rejected: OK')
    raise SystemExit(0)
raise SystemExit('Unsafe production configuration was accepted')
'@
        Push-Location $Backend
        try { & $script:PythonExe -c $code; if ($LASTEXITCODE -ne 0) { throw 'Production safety check failed' } }
        finally { Pop-Location }
        $env:APP_ENV = 'test'
        $env:DEBUG = 'false'
    }

    if (-not $SkipDocker) {
        Write-Step 'PostgreSQL + Alembic'
        Invoke-Gate 'Start isolated PostgreSQL' {
            & docker rm -f $DbContainer 2>$null | Out-Null
            & docker run -d --name $DbContainer -e POSTGRES_USER=primeerp_ci -e POSTGRES_PASSWORD=primeerp_ci -e POSTGRES_DB=primeerp_ci -p "${PostgresPort}:5432" postgres:17 | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Failed to start PostgreSQL container' }
            $script:StartedDb = $true
            for ($i=0; $i -lt 30; $i++) {
                & docker exec $DbContainer pg_isready -U primeerp_ci -d primeerp_ci 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) { return }
                Start-Sleep -Seconds 2
            }
            throw 'PostgreSQL did not become ready within 60 seconds'
        }

        $env:DATABASE_URL = "postgresql+psycopg://primeerp_ci:primeerp_ci@127.0.0.1:$PostgresPort/primeerp_ci"
        $env:APP_ENV = 'test'

        Invoke-Gate 'Alembic upgrade head' {
            Invoke-Python $Backend @('-m','alembic','upgrade','head')
        }
        Invoke-Gate 'Require single Alembic head' {
            Push-Location $Backend
            try {
                $heads = @(& $script:PythonExe -m alembic heads | Where-Object { $_ -match '^[0-9a-zA-Z_\-]+ ' })
                if ($heads.Count -ne 1) { throw "Expected exactly one Alembic head; found $($heads.Count)" }
                $heads | ForEach-Object { Write-Host "  $_" }
            } finally { Pop-Location }
        }
        Invoke-Gate 'Alembic check' {
            Invoke-Python $Backend @('-m','alembic','check')
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
        Push-Location $Frontend
        try {
            $pkg = Get-Content package.json -Raw | ConvertFrom-Json
            if ($pkg.scripts.typecheck) { Invoke-Npm $Frontend @('run','typecheck') } else { Write-Host '  No typecheck script; skipped.' -ForegroundColor DarkYellow }
        } finally { Pop-Location }
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
            & docker compose --env-file $envFile config -q
            if ($LASTEXITCODE -ne 0) { throw 'docker compose config failed' }
        }
        Invoke-Gate 'Backend Docker build' {
            & docker build --pull -t primeerp-backend:release-gate (Join-Path $RepoRoot 'backend')
            if ($LASTEXITCODE -ne 0) { throw 'Backend Docker build failed' }
            & docker run --rm primeerp-backend:release-gate python -m compileall -q app
            if ($LASTEXITCODE -ne 0) { throw 'Backend Docker source compilation failed' }
        }
        Invoke-Gate 'Frontend Docker build' {
            & docker build --pull -t primeerp-frontend:release-gate (Join-Path $RepoRoot 'frontend')
            if ($LASTEXITCODE -ne 0) { throw 'Frontend Docker build failed' }
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
