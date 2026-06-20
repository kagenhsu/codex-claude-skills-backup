@echo off
chcp 65001 > nul
setlocal
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

where powershell >nul 2>&1
if errorlevel 1 (
    echo 找不到 powershell，無法移除。請改用手動方式：
    echo   1. 開檔總管，網址列輸入 shell:startup
    echo   2. 刪除 QuotaGuardianAutostart.lnk
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\scripts\uninstall_windows_autostart.ps1"

echo.
pause
endlocal
