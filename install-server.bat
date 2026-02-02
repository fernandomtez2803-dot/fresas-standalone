@echo off
echo ============================================
echo   FRESAS STANDALONE - Instalacion Servidor
echo ============================================
echo.

REM Verificar Python (cualquier version)
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo.
    echo Soluciones:
    echo 1. Reinstala Python y marca "Add to PATH"
    echo 2. O ejecuta desde donde instalaste Python
    pause
    exit /b 1
)

echo Python encontrado:
python --version
echo.

REM Verificar Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no esta instalado o no esta en el PATH
    pause
    exit /b 1
)

echo Node.js encontrado:
node --version
echo.

echo [1/3] Creando entorno virtual e instalando backend...
cd /d "%~dp0backend"
python -m venv .venv
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install uvicorn fastapi pydantic pydantic-settings xlrd xlwt xlutils
echo.

echo [2/3] Instalando dependencias del frontend...
cd /d "%~dp0frontend"
call npm install
echo.

echo [3/3] Construyendo frontend...
call npm run build
echo.

echo ============================================
echo   INSTALACION COMPLETADA!
echo.
echo   Ahora ejecuta: start-server.bat
echo ============================================
pause
