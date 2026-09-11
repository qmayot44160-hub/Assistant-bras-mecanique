@echo off
setlocal
cd /d "%~dp0"
title ARIA - creer le raccourci

rem Fabrique un raccourci sur le Bureau qui pointe sur ARIA.vbs, avec l'icone
rem de l'app. Powershell sait ecrire un .lnk, pas le batch.

powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\ARIA.lnk');" ^
  "$s.TargetPath='%~dp0ARIA.vbs';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.IconLocation='%~dp0web\aria.ico';" ^
  "$s.Description='Atelier ARIA - bras robotise';" ^
  "$s.Save()"

if errorlevel 1 (
  echo [X] Creation du raccourci echouee.
  pause
  exit /b 1
)

echo.
echo   Raccourci "ARIA" cree sur ton Bureau.
echo   Double-clique dessus : plus de fenetre noire.
echo.
pause
