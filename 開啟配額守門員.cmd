@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\quota_guard_app.py --config quota_guard.example.json
  goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
  python scripts\quota_guard_app.py --config quota_guard.example.json
  goto :eof
)

echo Python 3 not found.
pause
