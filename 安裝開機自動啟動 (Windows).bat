@echo off
rem 把「配額守門員 + 本地控制台」裝成 Windows 登入後自動啟動。
rem 等同 Mac 上的「安裝開機自動啟動 (macOS).command」。

chcp 65001 > nul
setlocal
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

where powershell >nul 2>&1
if errorlevel 1 (
    echo 找不到 powershell，無法安裝。請改用手動方式：
    echo   1. 開檔總管，網址列輸入 shell:startup
    echo   2. 把「開啟控制台與配額守門員.bat」捷徑拖進去
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\scripts\install_windows_autostart.ps1" -RepoDir "%SCRIPT_DIR%"

echo.
pause
endlocal
