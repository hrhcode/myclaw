@echo off
echo Starting MyClaw...
start "MyClaw Backend" cmd /k "%~dp0start-backend.bat"
timeout /t 3 /nobreak > nul
start "MyClaw Frontend" cmd /k "%~dp0start-frontend.bat"
echo.
echo MyClaw is starting...
echo Backend: http://127.0.0.1:18789
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window (services will keep running)
pause > nul
