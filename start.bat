@echo off
echo ============================================
echo   FRESAS STANDALONE - Iniciando...
echo ============================================
echo.

:: Start backend in new window using venv python
echo Iniciando Backend (puerto 8002)...
start "Fresas Backend" cmd /k "cd /d %~dp0backend && ..\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8002"

:: Wait a bit for backend to start
timeout /t 3 /nobreak > nul

:: Start frontend in new window
echo Iniciando Frontend (puerto 3000)...
start "Fresas Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo   Ambos servicios iniciados!
echo   - Backend:  http://localhost:8002
echo   - Frontend: http://localhost:3000
echo ============================================
echo.
timeout /t 3
