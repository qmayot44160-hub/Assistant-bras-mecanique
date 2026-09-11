@echo off
setlocal
cd /d "%~dp0"
title ARIA - ouverte sur le reseau

echo ============================================
echo   ARIA - acces depuis tes autres appareils
echo ============================================
echo.
echo   ARIA va ecouter sur le reseau, pas seulement sur ce PC.
echo   Ses routes lisent sa memoire, l'effacent, et acceptent des
echo   fichiers : un mot de passe est donc obligatoire.
echo.

if not "%ARIA_PASSWORD%"=="" goto lance
set "ARIA_PASSWORD="
set /p ARIA_PASSWORD=  Choisis un mot de passe : 
if "%ARIA_PASSWORD%"=="" (
  echo.
  echo [X] Mot de passe vide, j'arrete la.
  pause
  exit /b 1
)
echo.

:lance
set ARIA_HOST=0.0.0.0
call "%~dp0run_local.bat"
