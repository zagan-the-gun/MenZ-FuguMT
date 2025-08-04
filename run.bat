@echo off
echo.
echo ======================================================
echo FuguMT Translation Server - Starting...
echo ======================================================
echo.

:: Check virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Check configuration file
if not exist config\fugumt_translator.ini (
    echo [ERROR] Configuration file not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Checking dependencies...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in virtual environment.
    echo Please run setup.bat.
    pause
    exit /b 1
)

pip show torch >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Required libraries not installed.
    echo Please run setup.bat.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo Port: 55002
echo URL: ws://127.0.0.1:55002
echo Stop: Ctrl + C (improved handling)
echo ======================================================
echo.

:: Start server with unbuffered output for better Ctrl+C handling
python -u main.py
set EXIT_CODE=%ERRORLEVEL%

:: Handle exit conditions
echo.
echo ======================================================
if %EXIT_CODE% == 0 (
    echo [INFO] Server stopped normally.
) else (
    echo [ERROR] Server exited abnormally (Exit code: %EXIT_CODE%).
    echo Check error log: logs\translator.log
)
echo ======================================================

:: Deactivate virtual environment
deactivate

echo.
echo Press any key to close...
pause > nul
exit /b %EXIT_CODE%