@echo off
setlocal
cd /d "%~dp0"
title ARIA - voix disponibles

rem Le catalogue est en ligne et bouge : on l'interroge au lieu de recopier
rem une liste qui vieillirait mal.

set PY=python
python --version >nul 2>nul
if errorlevel 1 set PY=py

echo Voix francaises disponibles :
echo.
%PY% -m piper.download_voices 2>nul | findstr /b "fr_FR"
if errorlevel 1 (
  echo   [X] Liste indisponible. Lance d'abord Installer-la-voix.bat,
  echo       et verifie ta connexion.
)
echo.
echo Pour en essayer une :
echo   set PIPER_VOICE=fr_FR-upmc-medium
echo   Installer-la-voix.bat
echo.
pause
