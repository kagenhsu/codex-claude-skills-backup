@echo off
rem 更新本地控制台靜態檔，再起本地網址（127.0.0.1:8000）並打開預設瀏覽器。
rem 對應 Mac 上的「更新並開啟控制台.command」。

chcp 65001 > nul
setlocal
rem %~dp0 結尾帶 \ ，丟給 python 當 "%SCRIPT_DIR%" 會被 MSVCRT 當成 escaped quote，要先剝掉。
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

where python >nul 2>&1
if errorlevel 1 (
    echo 找不到 python，請先安裝 Python 3，或直接雙擊 index.html 開啟舊版控制台。
    pause
    exit /b 1
)

echo 正在更新二刀流開發助手控制台...
python "%SCRIPT_DIR%\scripts\build.py"
if errorlevel 1 (
    echo.
    echo 控制台更新失敗，請確認資料檔案格式是否正確。
    pause
    exit /b 1
)

echo.
echo 正在啟動本地控制台網址...
echo 瀏覽器會自動打開 127.0.0.1:7000~7999 之間的本地控制台網址。
echo 這個視窗請先不要關閉；關閉後，本地網址就會停止。
echo.
python "%SCRIPT_DIR%\scripts\serve_console.py" --root "%SCRIPT_DIR%" --open-browser
if errorlevel 1 (
    echo.
    echo 無法啟動本地控制台網址。
    echo 你可以先手動執行：python "%SCRIPT_DIR%\scripts\serve_console.py" --root "%SCRIPT_DIR%" --open-browser
    pause
    exit /b 1
)

endlocal
