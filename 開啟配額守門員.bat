@echo off
rem 桌面浮動小視窗（Windows 版）— 用 pythonw 啟動，不會跳黑色 console。
rem 對應 Mac 上的「開啟配額守門員.command」。

chcp 65001 > nul
setlocal
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

rem 殘留的先收掉，避免重複開（用 PowerShell + CIM 比 wmic 穩，且 wmic 已 deprecated）
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' or Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*quota_guard_floating.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" > nul 2>&1

where pythonw >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo 找不到 python / pythonw，請先安裝 Python 3。
        pause
        exit /b 1
    )
    start "" python "%SCRIPT_DIR%\scripts\quota_guard_floating.py"
) else (
    start "" pythonw "%SCRIPT_DIR%\scripts\quota_guard_floating.py"
)

endlocal
exit /b 0
