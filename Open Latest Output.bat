@echo off
setlocal
cd /d "%~dp0"
if exist "output\latest\dashboard.html" (
  start "" "output\latest\dashboard.html"
) else (
  echo No dashboard found. Run Evergreen Memory Lite first.
  pause
)
endlocal
