@echo off
title PrimeERP Startup

echo Starting PrimeERP Backend...

start "PrimeERP Backend" cmd /k ^
"cd /d D:\PrimeERP\backend && D:\PrimeERP\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001"

echo Starting PrimeERP Frontend...

start "PrimeERP Frontend" cmd /k ^
"cd /d D:\PrimeERP\frontend && npm run dev -- --host 0.0.0.0"

echo Waiting for the system...

timeout /t 8 /nobreak > nul

echo Opening PrimeERP...

start "" http://localhost:3000

exit