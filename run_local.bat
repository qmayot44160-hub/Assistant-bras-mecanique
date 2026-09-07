@echo off
setlocal
cd /d "%~dp0"
title ARIA - cerveau local

if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=qwen2.5:7b
set BRAIN_MODE=local

echo ============================================
echo   ARIA - cerveau local (Ollama + RTX)
echo ============================================
echo.

where ollama >nul 2>nul
if errorlevel 1 (
  echo [X] Ollama introuvable.
  echo     Installe-le depuis https://ollama.com/download puis relance ce script.
  pause
  exit /b 1
)

python --version >nul 2>nul
if errorlevel 1 (
  echo [X] Python introuvable.
  echo     Installe Python 3 depuis https://www.python.org/downloads/
  echo     ^(coche "Add python.exe to PATH" pendant l'installation^) puis relance.
  pause
  exit /b 1
)

echo [1/3] Dependances Python...
python -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo [2/3] Modele local %OLLAMA_MODEL% (telechargement unique, quelques Go)...
ollama pull %OLLAMA_MODEL%

echo [3/3] Demarrage du serveur ARIA...
echo.
echo   Ouvre ton navigateur sur :  http://127.0.0.1:8000
echo   (Ctrl+C dans cette fenetre pour arreter)
echo.
python -m uvicorn brain.main:app --host 127.0.0.1 --port 8000
pause
