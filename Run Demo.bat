@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m evergreen_memory_lite.runner --input data\synthetic_inbox --output output\latest --document-intake --household-admin --write
) else (
  python -m evergreen_memory_lite.runner --input data\synthetic_inbox --output output\latest --document-intake --household-admin --write
)
if exist "output\latest\dashboard.html" (
  start "" "output\latest\dashboard.html"
)
endlocal
