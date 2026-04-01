@echo off
setlocal

cd /d "%~dp0"

echo Building PC Health API...
go mod tidy
go build -o pc-health-api.exe .

echo Build complete: pc-health-api.exe
