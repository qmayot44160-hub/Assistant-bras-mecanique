@echo off
setlocal
cd /d "%~dp0"
title ARIA - cerveau local

rem Modele par defaut. Pour en changer sans editer ce fichier, dans un cmd :
rem   set OLLAMA_MODEL=qwen2.5:3b  puis  run_local.bat
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=qwen2.5:7b
set BRAIN_MODE=local

rem Memoire + catalogue d'ARIA, ranges a cote de l'app (et pas dans C:\data).
if "%DATA_DIR%"=="" set DATA_DIR=%~dp0data
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo ============================================
echo   ARIA - cerveau local (Ollama + RTX)
echo ============================================
echo.

rem --- Python : "python", sinon le lanceur "py" ---------------------------
set PY=python
python --version >nul 2>nul
if errorlevel 1 (
  set PY=py
  py --version >nul 2>nul
  if errorlevel 1 goto no_python
)

where ollama >nul 2>nul
if errorlevel 1 (
  echo [X] Ollama introuvable.
  echo     Installe-le depuis https://ollama.com/download puis relance ce script.
  pause
  exit /b 1
)

rem --- Carte graphique, pour information ----------------------------------
where nvidia-smi >nul 2>nul
if not errorlevel 1 (
  for /f "tokens=*" %%g in ('nvidia-smi --query-gpu^=name^,memory.total --format^=csv^,noheader 2^>nul') do echo   GPU : %%g
  echo.
)

rem --- 1/4 : le service Ollama repond-il ? --------------------------------
rem Sur Windows, Ollama tourne en tache de fond. S'il est eteint, l'app
rem tomberait sur les reflexes scriptes sans qu'on comprenne pourquoi.
echo [1/4] Service Ollama...
ollama list >nul 2>nul
if not errorlevel 1 goto ollama_ok
echo       pas demarre, je le lance...
start "Ollama" /min ollama serve
for /l %%i in (1,1,30) do (
  timeout /t 1 /nobreak >nul
  ollama list >nul 2>nul
  if not errorlevel 1 goto ollama_ok
)
echo [X] Ollama n'a pas demarre en 30 s.
echo     Ouvre l'application Ollama a la main, puis relance ce script.
pause
exit /b 1
:ollama_ok
echo       OK.

rem --- 2/4 : le modele est-il deja la ? -----------------------------------
rem On teste avant de tirer : "ollama pull" a chaque lancement demande le
rem reseau pour rien, et echoue si tu es hors ligne.
echo [2/4] Modele %OLLAMA_MODEL%...
ollama list | findstr /b /c:"%OLLAMA_MODEL%" >nul 2>nul
if not errorlevel 1 goto model_ok
echo       absent, telechargement ^(quelques Go, une seule fois^)...
ollama pull %OLLAMA_MODEL%
if errorlevel 1 (
  echo [X] Telechargement echoue. Verifie ta connexion, puis relance.
  pause
  exit /b 1
)
goto model_done
:model_ok
echo       deja installe.
:model_done

rem --- 3/4 : dependances Python -------------------------------------------
echo [3/4] Dependances Python...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt

rem --- 4/4 : serveur ------------------------------------------------------
echo [4/4] Demarrage du serveur ARIA...
echo.
echo   Navigateur    :  http://127.0.0.1:8000
echo   Memoire       :  %DATA_DIR%
echo   Pour arreter  :  Ctrl+C dans cette fenetre
echo.
echo   La premiere reponse peut prendre une minute : le modele se charge
echo   dans la VRAM. Ensuite c'est rapide.
echo.

rem Ouvre la page tout seul une fois le serveur debout.
start "" /min cmd /c "timeout /t 6 /nobreak >nul & start "" http://127.0.0.1:8000"

%PY% -m uvicorn brain.main:app --host 127.0.0.1 --port 8000
pause
exit /b 0

:no_python
echo [X] Python introuvable.
echo     Installe Python 3 depuis https://www.python.org/downloads/
echo     ^(coche "Add python.exe to PATH" pendant l'installation^) puis relance.
pause
exit /b 1
