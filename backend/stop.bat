echo off
echo Stopping PrimeERP...
taskkill /F /FI "WINDOWTITLE eq PrimeERP Backend"
taskkill /F /FI "WINDOWTITLE eq PrimeERP Frontend"
echo PrimeERP stopped!
pause