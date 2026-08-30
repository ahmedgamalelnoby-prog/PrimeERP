echo off
echo Starting PrimeERP...

REM تشغيل Backend
start "PrimeERP Backend" cmd /k "cd /d D:\PrimeERP\backend && call D:\PrimeERP\.venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM انتظر 3 ثواني
timeout /t 3 /nobreak >nul

REM تشغيل Frontend
start "PrimeERP Frontend" cmd /k "cd /d D:\PrimeERP\frontend && npm run dev"

echo PrimeERP is running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Press any key to close this window...
pause >nul