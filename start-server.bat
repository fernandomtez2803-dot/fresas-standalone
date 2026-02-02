@echo off
echo ============================================
echo   FRESAS STANDALONE - Servidor
echo ============================================
echo.

REM Obtener IP del servidor
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set IP=%%b
)
echo IP del servidor: %IP%
echo.

echo Iniciando Backend (puerto 8002)...
start "Fresas Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002"

timeout /t 3 /nobreak > nul

echo Iniciando Frontend (puerto 3000)...
start "Fresas Frontend" cmd /k "cd /d %~dp0frontend && npm run start"

echo.
echo ============================================
echo   SERVIDOR INICIADO!
echo.
echo   Accede desde cualquier PC de la red:
echo   http://%IP%:3000
echo.
echo   NO CIERRES estas ventanas
echo ============================================
echo.
pause
