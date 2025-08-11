@echo off
title FuguMT Translation Server - Setup
setlocal EnableDelayedExpansion

:: Create setup log
set SETUP_LOG=setup_log_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set SETUP_LOG=%SETUP_LOG: =0%
echo Setup started at %date% %time% > %SETUP_LOG%

echo.
echo ======================================================
echo FuguMT Translation Server - Windows Setup
echo ======================================================
echo Setup log: %SETUP_LOG%
echo.

:: Check admin privileges
echo [STEP] Checking administrator privileges... >> %SETUP_LOG%
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
    echo [SUCCESS] Administrator privileges detected >> %SETUP_LOG%
) else (
    echo [WARNING] Administrator privileges recommended
    echo ^(for firewall configuration^)
    echo [WARNING] No administrator privileges >> %SETUP_LOG%
)
echo.

echo [1/6] Checking Python version...
echo [STEP] Checking Python installation... >> %SETUP_LOG%
python --version >> %SETUP_LOG% 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    echo Please install Python 3.8+ and add to PATH.
    echo https://www.python.org/downloads/windows/
    echo [ERROR] Python not found in PATH >> %SETUP_LOG%
    echo [ERROR] Setup failed. See log file: %SETUP_LOG%
    echo Setup failed at %date% %time% >> %SETUP_LOG%
    exit /b 1
)
echo [SUCCESS] Python found >> %SETUP_LOG%
echo.

echo [2/6] Creating virtual environment...
echo [STEP] Creating virtual environment... >> %SETUP_LOG%
if exist venv (
    echo [INFO] Existing virtual environment found. Using existing venv.
    echo [INFO] Reusing existing virtual environment >> %SETUP_LOG%
)

if not exist venv (
    echo [STEP] Creating new virtual environment... >> %SETUP_LOG%
    python -m venv venv >> %SETUP_LOG% 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo [ERROR] Virtual environment creation failed >> %SETUP_LOG%
        echo [ERROR] Check Python installation and permissions
        echo [ERROR] Setup failed. See log file: %SETUP_LOG%
        echo Setup failed at %date% %time% >> %SETUP_LOG%
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
    echo [SUCCESS] Virtual environment created >> %SETUP_LOG%
)
echo.

echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    echo [ERROR] Virtual environment activation failed >> %SETUP_LOG%
    echo [ERROR] Setup failed. See log file: %SETUP_LOG%
    echo Setup failed at %date% %time% >> %SETUP_LOG%
    exit /b 1
)
echo.

echo [4/6] Installing dependencies...
echo [INFO] This may take several minutes...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo [WARNING] Failed to upgrade pip, continuing with current version...
)

echo Installing dependencies...
echo [STEP] Installing dependencies from requirements.txt... >> %SETUP_LOG%
pip install -r requirements.txt >> %SETUP_LOG% 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo [ERROR] Dependencies installation failed >> %SETUP_LOG%
    echo [ERROR] Setup failed. See log file: %SETUP_LOG%
    echo Setup failed at %date% %time% >> %SETUP_LOG%
    exit /b 1
) else (
    echo [SUCCESS] Dependencies installed >> %SETUP_LOG%
    echo [SUCCESS] Dependencies installed
)

echo.
echo GPU support? (y/n)
set /p GPU="Choice: "
echo [INPUT] User selected: %GPU% >> %SETUP_LOG%

if /i "%GPU%"=="y" (
    echo Installing PyTorch with CUDA...
    echo [STEP] Installing PyTorch CUDA version... >> %SETUP_LOG%
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 --force-reinstall >> %SETUP_LOG% 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install PyTorch.
        echo [ERROR] PyTorch installation failed >> %SETUP_LOG%
        echo [ERROR] Setup failed. See log file: %SETUP_LOG%
        echo Setup failed at %date% %time% >> %SETUP_LOG%
        exit /b 1
    )
    echo [SUCCESS] PyTorch CUDA version installed >> %SETUP_LOG%
    echo [SUCCESS] PyTorch CUDA version installed
) else (
    echo Installing PyTorch CPU version...
    echo [STEP] Installing PyTorch CPU version... >> %SETUP_LOG%
    pip install torch torchvision torchaudio --force-reinstall >> %SETUP_LOG% 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install PyTorch CPU version.
        echo [ERROR] PyTorch installation failed >> %SETUP_LOG%
        echo [ERROR] Setup failed. See log file: %SETUP_LOG%
        echo Setup failed at %date% %time% >> %SETUP_LOG%
        exit /b 1
    )
    echo [SUCCESS] PyTorch installation completed >> %SETUP_LOG%
    echo [SUCCESS] PyTorch CPU version installed
)

:: Verify PyTorch version
echo [INFO] Verifying PyTorch installation...
python -c "import torch; print(f'[INFO] PyTorch {torch.__version__} installed successfully')"
python -c "import torch; print(f'[INFO] CUDA available: {torch.cuda.is_available()}')" 2>nul

echo [SUCCESS] Setup completed >> %SETUP_LOG%
echo.

echo [5/6] Creating necessary directories...
if not exist config mkdir config
if not exist logs mkdir logs
echo.

echo [6/6] Creating configuration file...
if not exist config\fugumt_translator.ini (
    echo [INFO] Creating default configuration file...
    
    :: Detect PyTorch device capability
    python -c "import torch; print('cuda' if torch.cuda.is_available() else 'cpu')" > temp_device.txt 2>nul
    set /p TORCH_DEVICE=<temp_device.txt
    del temp_device.txt 2>nul
    if "%TORCH_DEVICE%"=="" set TORCH_DEVICE=cpu
    
    echo [INFO] Configuring for device: %TORCH_DEVICE%
    (
        echo [SERVER]
        echo host = 127.0.0.1
        echo port = 55002
        echo max_connections = 10
        echo.
        echo [TRANSLATION]
        echo model_name = staka/fugumt-en-ja
        echo device = %TORCH_DEVICE%
        echo max_length = 128
        echo.
        echo [LOGGING]
        echo level = INFO
        echo file = logs/translator.log
        echo max_file_size = 10485760
        echo backup_count = 3
    ) > config\fugumt_translator.ini
    echo [SUCCESS] Configuration file created: config\fugumt_translator.ini
) else (
    echo [INFO] Using existing configuration: config\fugumt_translator.ini
)
echo.

echo ======================================================
echo Setup completed successfully!
echo ======================================================
echo Setup completed at %date% %time% >> %SETUP_LOG%
echo.
echo Next steps:
echo 1. Edit config\fugumt_translator.ini if needed
echo    - NVIDIA GPU PC: device = cuda
echo    - CPU only: device = cpu
echo.
echo 2. Start server: Double-click run.bat
echo.
echo Note: Allow access if Windows Firewall asks for permission
echo Setup log saved: %SETUP_LOG%
echo.
echo Press any key to close this window...
pause >nul