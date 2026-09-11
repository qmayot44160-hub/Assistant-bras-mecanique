@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title ARIA - cerveau local

rem Modele par defaut. Pour en changer sans editer ce fichier, dans un cmd :
rem   set OLLAMA_MODEL=qwen2.5:3b  puis  run_local.bat
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=qwen2.5:7b
set BRAIN_MODE=local

rem Par defaut ARIA n'ecoute que ce PC. run_reseau.bat met 0.0.0.0 pour
rem l'ouvrir au telephone et aux tunnels.
if "%ARIA_HOST%"=="" set ARIA_HOST=127.0.0.1

rem Garde-fou : les routes d'ARIA lisent sa memoire, l'effacent et acceptent
rem des fichiers. Ouvrir ca sans mot de passe serait une porte grande ouverte.
if not "%ARIA_HOST%"=="127.0.0.1" if "%ARIA_PASSWORD%"=="" (
  echo [X] Refus d'ouvrir ARIA sur le reseau sans mot de passe.
  echo.
  echo     N'importe qui sur le reseau pourrait lire sa memoire, l'effacer,
  echo     et deposer des fichiers sur ce PC.
  echo.
  echo     Lance run_reseau.bat, ou definis ARIA_PASSWORD toi-meme.
  call :hold
  exit /b 1
)

rem --- Le dossier est-il inscriptible ? -----------------------------------
rem Dezippe sur un disque protege, rien ne pourra s'y ecrire : ni la memoire
rem d'ARIA, ni les mises a jour. Autant le dire ici plutot que de laisser
rem Python exploser vingt lignes plus loin.
echo.> "%~dp0.wtest" 2>nul
if not exist "%~dp0.wtest" (
  echo [X] Ecriture refusee dans ce dossier :
  echo     %~dp0
  echo.
  echo     Copie ARIA sur ton disque systeme, puis relance de la-bas :
  echo       xcopy /e /i /y "%~dp0." "%USERPROFILE%\ARIA"
  echo       cd /d "%USERPROFILE%\ARIA"
  echo       run_local.bat
  call :hold
  exit /b 1
)
del "%~dp0.wtest" >nul 2>nul

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
  call :hold
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
call :hold
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
  call :hold
  exit /b 1
)
goto model_done
:model_ok
echo       deja installe.
:model_done

rem --- 3/4 : dependances + mise a jour d'ARIA -----------------------------
echo [3/4] Dependances Python...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt
echo       Mise a jour d'ARIA...
rem Ta memoire (data\) n'est jamais touchee. Pour sauter cette etape :
rem   set ARIA_NO_UPDATE=1
if exist selfupdate.py %PY% selfupdate.py

rem --- 4/4 : serveur ------------------------------------------------------
echo [4/4] Demarrage du serveur ARIA...
echo.
echo   Navigateur    :  http://127.0.0.1:8000
if not "%ARIA_HOST%"=="127.0.0.1" (
  for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set LANIP=%%a
  echo   Depuis le tel :  http://!LANIP: =!:8000
  echo   Mot de passe  :  demande a la connexion
)
echo   Memoire       :  %DATA_DIR%
echo   Pour arreter  :  Ctrl+C dans cette fenetre
echo.
echo   La premiere reponse peut prendre une minute : le modele se charge
echo   dans la VRAM. Ensuite c'est rapide.
echo.

rem Ouvre la page tout seul une fois le serveur debout.
if not "%ARIA_NO_BROWSER%"=="1" start "" /min cmd /c "timeout /t 6 /nobreak >nul & start "" http://127.0.0.1:8000"

%PY% -m uvicorn brain.main:app --host %ARIA_HOST% --port 8000
call :hold
exit /b 0

rem Lance depuis ARIA.vbs (sans fenetre), un "pause" bloquerait pour
rem toujours un processus invisible. On saute l'attente dans ce cas.
:hold
if "%ARIA_SILENT%"=="1" exit /b 0
pause
exit /b 0

:no_python
echo [X] Python introuvable.
echo     Installe Python 3 depuis https://www.python.org/downloads/
echo     ^(coche "Add python.exe to PATH" pendant l'installation^) puis relance.
call :hold
exit /b 1
