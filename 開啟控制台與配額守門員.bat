@echo off
rem 一次開「本地控制台」+「桌面浮動小視窗」。
rem 對應 Mac 上的「開啟控制台與配額守門員.command」。

chcp 65001 > nul
setlocal
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

rem 浮動視窗先丟背景跑（不擋本地網址前景）
start "" "%SCRIPT_DIR%\開啟配額守門員.bat"

rem 然後在這個視窗跑本地網址（exec 風格）
call "%SCRIPT_DIR%\更新並開啟控制台.bat"

endlocal
