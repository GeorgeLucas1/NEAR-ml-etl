@echo off
cd /d "%~dp0"

echo ========================================
echo PC Health Monitor - Sistema Completo
echo ========================================
echo.

REM Kill processes
taskkill /F /IM pc-health-api.exe 2>nul
taskkill /F /IM python.exe 2>nul

echo [1/4] Verificando banco de dados...
python -c "from pathlib import Path; Path('data').mkdir(exist_ok=True)"
echo.

echo [2/4] Iniciando API Go...
start "API" /D "%~dp0api" pc-health-api.exe
timeout /t 3 /nobreak >nul

echo [3/4] Iniciando Collector Python...
start "Collector" cmd /c "python collector\simple_collector.py"
timeout /t 3 /nobreak >nul

echo [4/4] Iniciando Frontend Vue.js...
cd frontend
call npm install 2>nul
start "Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ========================================
echo Sistema iniciado!
echo - API: http://localhost:8080
echo - Frontend: http://localhost:3000
echo ========================================
pause
