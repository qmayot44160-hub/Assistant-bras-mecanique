@echo off
setlocal
cd /d "%~dp0"
title ARIA - creer le raccourci

rem Un raccourci .lnk vers run_local.bat, avec l'icone d'ARIA et la fenetre
rem reduite au demarrage (WindowStyle 7).
rem
rem Pourquoi pas une fenetre totalement invisible : un lancement cache qui
rem echoue ne peut rien te dire. Reduite, elle ne te gene pas, et le jour ou
rem ca coince tu cliques dessus dans la barre des taches et tu vois l'erreur.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Desktop');" ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut(\"$d\ARIA.lnk\");" ^
  "$s.TargetPath='%~dp0run_local.bat';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.IconLocation='%~dp0web\aria.ico';" ^
  "$s.WindowStyle=7;" ^
  "$s.Description='Atelier ARIA - bras robotise';" ^
  "$s.Save();" ^
  "if(Test-Path \"$d\ARIA.lnk\"){Write-Host '  OK ->' \"$d\ARIA.lnk\"}else{exit 1}"

if errorlevel 1 (
  echo.
  echo [X] Creation du raccourci echouee.
  echo     Tu peux le faire a la main : clic droit sur run_local.bat,
  echo     "Envoyer vers" ^> "Bureau ^(creer un raccourci^)".
  pause
  exit /b 1
)

echo.
echo   Raccourci "ARIA" cree sur ton Bureau.
echo   Double-clique dessus : la fenetre se reduit toute seule et
echo   la page s'ouvre au bout de 30 a 60 secondes.
echo.
pause
