@echo off
setlocal

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed. Please install Python to proceed.
    pause
    exit /b
)

REM Check if Tesseract OCR is already installed
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo Tesseract OCR is already installed. Skipping installation.
) else (
    REM Install Tesseract OCR
    if not exist "tesseract-ocr-w64-setup-5.4.0.20240606.exe" (
        echo Tesseract setup file not found! Please make sure the file is in the same directory.
        pause
        exit /b
    )

    echo Installing Tesseract OCR...
    tesseract-ocr-w64-setup-5.4.0.20240606.exe /SILENT /NORESTART

    if %ERRORLEVEL% neq 0 (
        echo Tesseract OCR installation failed. Please check the setup file or your permissions.
        pause
        exit /b
    )

    echo Tesseract OCR installed successfully.

    REM Add Tesseract-OCR to system PATH
    SETX PATH "%PATH%;C:\Program Files\Tesseract-OCR"
    if %ERRORLEVEL% neq 0 (
        echo Failed to add Tesseract-OCR to system PATH. Please add it manually.
        pause
        exit /b
    )
    echo Tesseract-OCR path added to the system PATH.
)

REM Check if virtual environment exists, else create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo Failed to create virtual environment. Please check Python installation or permissions.
        pause
        exit /b
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment. Please check the 'venv' folder and retry.
    pause
    exit /b
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

if %ERRORLEVEL% neq 0 (
    echo Failed to upgrade pip. Please ensure Python and pip are installed correctly.
    pause
    exit /b
)

REM Install required packages from requirements.txt if it exists
if exist "requirements.txt" (
    echo Installing required packages...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo Failed to install required packages. Check 'requirements.txt' or internet connection.
        pause
        exit /b
    )
) else (
    echo requirements.txt not found. Please make sure it is available in the directory.
    pause
    exit /b
)

REM Run Flask app
echo Starting Flask app...
start "" /b cmd /c python app.py
if %ERRORLEVEL% neq 0 (
    echo Failed to start the Flask app. Please check 'app.py' for errors.
    pause
    exit /b
)

REM Wait for the server to start
timeout /t 5 /nobreak > nul

REM Open the Flask app in the default browser
echo Opening Flask app in browser...
start http://127.0.0.1:5000/

pause
