@echo off
echo ========================================
echo PC Health Monitor - Docker Compose
echo ========================================
echo.

echo [1/3] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker nao encontrado! Instale Docker Desktop.
    pause
    exit /b 1
)

echo [2/3] Construindo imagens...
docker-compose build

echo [3/3] Iniciando servicos...
docker-compose up -d

echo.
echo ========================================
echo Servicos iniciados!
echo - Dashboard: http://localhost:3000
echo - API: http://localhost:8080
echo ========================================
pause
