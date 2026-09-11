@echo off
setlocal
cd /d "%~dp0"
title ARIA - installer sa vraie voix

rem Piper : synthese vocale neuronale, locale, bien meilleure que les voix
rem Windows. Separe de run_local.bat parce que ca telecharge ~300 Mo : autant
rem que ce soit un choix, pas une surprise au premier lancement.

if "%PIPER_VOICE%"=="" set PIPER_VOICE=fr_FR-siwis-medium
if "%DATA_DIR%"=="" set DATA_DIR=%~dp0data

echo ============================================
echo   ARIA - sa vraie voix (Piper, en local)
echo ============================================
echo.
echo   Voix     : %PIPER_VOICE%
echo   A prevoir: ~250 Mo de moteur + ~65 Mo de voix, une seule fois.
echo   Tout reste sur ce PC, rien n'est envoye nulle part.
echo.

set PY=python
python --version >nul 2>nul
if errorlevel 1 (
  set PY=py
  py --version >nul 2>nul
  if errorlevel 1 (
    echo [X] Python introuvable. Lance run_local.bat d'abord.
    pause
    exit /b 1
  )
)

echo [1/2] Moteur de synthese...
%PY% -m pip install --quiet --disable-pip-version-check --no-warn-script-location piper-tts
if errorlevel 1 (
  echo [X] Installation de piper-tts echouee.
  pause
  exit /b 1
)
echo       OK.

rem Le dossier de donnees n'est pas toujours .\data : quand il est refuse en
rem ecriture, ARIA se replie ailleurs. On demande a ARIA ou elle range.
for /f "usebackq tokens=*" %%d in (`%PY% -c "import sys;sys.path.insert(0,'brain');import catalog;print(catalog.DATA_DIR)"`) do set "VDIR=%%d\voices"
if "%VDIR%"=="" set "VDIR=%DATA_DIR%\voices"

echo [2/2] Voix %PIPER_VOICE% vers :
echo       %VDIR%
if not exist "%VDIR%" mkdir "%VDIR%"
%PY% -m piper.download_voices %PIPER_VOICE% --download-dir "%VDIR%"
if errorlevel 1 (
  echo [X] Telechargement de la voix echoue. Verifie ta connexion.
  pause
  exit /b 1
)

echo.
echo   Termine. Relance ARIA, clique sur "Sa voix", et le journal doit
echo   afficher : voix activee ^(Piper, synthese locale^).
echo.
echo   Pour essayer une autre voix, dans un cmd :
echo     set PIPER_VOICE=fr_FR-tom-medium
echo     Installer-la-voix.bat
echo.
pause
