@echo off
echo Starting PrimeERP Backend...
cd /d D:\PrimeERP\backend
call D:\PrimeERP\.venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause