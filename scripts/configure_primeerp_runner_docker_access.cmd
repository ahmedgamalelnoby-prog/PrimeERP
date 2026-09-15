@echo off
setlocal

rem PrimeERP self-hosted runner must access Docker Desktop installed under the
rem interactive Admin profile. NETWORK SERVICE cannot read that user profile.
rem Run this script once from an elevated Administrator CMD, then restart
rem the runner service. Do not run run.cmd manually.

set "SERVICE=actions.runner.ahmedgamalelnoby-prog-PrimeERP.PrimeERP-Windows"

echo [1/4] Checking runner service...
sc.exe query "%SERVICE%"
if errorlevel 1 exit /b 1

echo [2/4] Stopping runner service...
sc.exe stop "%SERVICE%"

:wait_stop
sc.exe query "%SERVICE%" | findstr /I "STOPPED" >nul
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto wait_stop
)

echo [3/4] Switching runner service to LocalSystem...
sc.exe config "%SERVICE%" obj= LocalSystem
if errorlevel 1 exit /b 1

echo [4/4] Starting runner service...
sc.exe start "%SERVICE%"
if errorlevel 1 exit /b 1

timeout /t 3 /nobreak >nul
sc.exe query "%SERVICE%"

echo.
echo Runner Docker service-account configuration completed.
echo Verify the service reports RUNNING before rerunning PrimeERP Validation.
exit /b 0
