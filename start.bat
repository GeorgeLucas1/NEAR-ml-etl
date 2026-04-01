@echo off
echo ========================================
echo PC Health Monitor - Iniciar Sistema
echo ========================================
echo.

echo [1/3] Iniciando API Go...
start "PC Health API" /D "%~dp0api" pc-health-api.exe

timeout /t 2 /nobreak >nul

echo [2/3] Iniciando Collector Python...
start "PC Health Collector" /D "%~dp0" python collector/simple_collector.py

timeout /t 5 /nobreak >nul

echo [3/3] Abrindo Streamlit Dashboard...
start "PC Health Dashboard" /D "%~dp0" streamlit run streamlit/app.py

echo.
echo ========================================
echo Sistema iniciado!
echo - API: http://localhost:8080
echo - Dashboard: http://localhost:8501
echo ========================================
pause
