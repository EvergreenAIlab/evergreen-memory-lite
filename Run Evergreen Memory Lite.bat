@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m evergreen_memory_lite.launcher
) else (
  python -m evergreen_memory_lite.launcher
)
endlocal
