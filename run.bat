@echo off

:: Force display of any errors by adding pause at critical points
:: This prevents the window from closing immediately on errors

:: Immediate pause to catch any early errors
echo Starting FuguMT Translation Server...
echo Press any key to continue startup checks...
pause >nul

echo.
echo ======================================================
echo FuguMT Translation Server - Starting...
echo ======================================================
echo.

:: Test basic functionality first
echo [DEBUG] Testing basic Windows commands...
dir >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Basic Windows commands not working
    pause
    exit /b 1
)
echo [SUCCESS] Basic commands work.

echo [DEBUG] Current directory: %CD%
echo [DEBUG] Checking virtual environment...

:: Check virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment found.

:: Check configuration file
if not exist config\fugumt_translator.ini (
    echo [ERROR] Configuration file not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo [SUCCESS] Configuration file found.
echo [DEBUG] About to activate virtual environment...

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    echo [DEBUG] Activation script may be corrupted.
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment activated.

echo [INFO] Checking dependencies...
python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found in virtual environment.
    echo Please run setup.bat to fix this issue.
    echo.
    pause
    exit /b 1
)

echo [INFO] Checking PyTorch installation...
pip show torch
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Required libraries not installed.
    echo Please run setup.bat to install dependencies.
    echo.
    pause
    exit /b 1
)

echo [INFO] Checking main.py...
if not exist main.py (
    echo.
    echo [ERROR] main.py not found in current directory.
    echo Please ensure you are in the correct project directory.
    echo.
    pause
    exit /b 1
)

echo [INFO] Checking FuguMTTranslator module...
python -c "import FuguMTTranslator; print('Module import successful')" 2>import_error.log
if errorlevel 1 (
    echo.
    echo [ERROR] FuguMTTranslator module import failed.
    echo Error details:
    type import_error.log
    echo.
    echo Please run setup.bat to fix dependencies.
    echo.
    del import_error.log 2>nul
    pause
    exit /b 1
)
del import_error.log 2>nul

echo.
echo ======================================================
echo FuguMT Translation Server Starting...
echo ======================================================
echo Port: 55002
echo URL: ws://127.0.0.1:55002
echo Stop: Ctrl + C
echo ======================================================
echo.
echo [INFO] Starting server...
echo [INFO] If errors occur, they will be displayed below:
echo.

:: Start server with detailed error handling
echo [CRITICAL] About to start Python server...
echo Press any key to launch the server (if error occurs, window will stay open)
pause >nul

python -u main.py 2>&1
set EXIT_CODE=%ERRORLEVEL%

:: Force pause after any exit to see error messages
echo.
echo Python exited with code: %EXIT_CODE%
echo Press any key to continue error analysis...
pause >nul

:: Handle exit conditions with detailed error information
echo.
echo ======================================================
if %EXIT_CODE% == 0 (
    echo [INFO] Server stopped normally.
) else (
    echo [ERROR] Server exited with error (Exit code: %EXIT_CODE%).
    echo.
    echo Possible causes:
    echo - Configuration file issues
    echo - Missing dependencies  
    echo - Port already in use
    echo - GPU/CUDA configuration problems
    echo.
    if exist logs\translator.log (
        echo Recent log entries:
        echo ==================
        powershell "Get-Content logs\translator.log -Tail 10"
        echo ==================
    ) else (
        echo No log file found at logs\translator.log
    )
    echo.
    echo For more help:
    echo 1. Check above error messages
    echo 2. Run check_gpu.bat for environment check
    echo 3. Run setup.bat to reinstall dependencies
)
echo ======================================================

:: Deactivate virtual environment
deactivate

echo.
echo Press any key to close...
pause
exit /b %EXIT_CODE%