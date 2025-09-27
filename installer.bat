@echo off
setlocal

rem Get the current script directory
set "SCRIPT_DIR=%~dp0"
set "TEMP_DIR=%SCRIPT_DIR%pythonEnv"

rem Notify user about the process start
echo Starting Python environment setup...

rem Remove existing temporary directory if it exists
if exist "%TEMP_DIR%" (
    rd /s /q "%TEMP_DIR%"
)

rem Check if the script has permission to create directories
mkdir "%TEMP_DIR%" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Permission denied. Please run this script as an administrator.
    exit /b 1
)

mkdir "%TEMP_DIR%"

rem Define Python version and URL for Windows x86_64
set "PYTHON_VERSION=3.12.9"
set "PYTHON_BINARY=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.zip"

rem Determine architecture
set "ARCH=x64"
if "%PROCESSOR_ARCHITECTURE%"=="ARM" (
    set "ARCH=arm"
    set "PYTHON_BINARY=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-win32.zip"
) else if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "ARCH=arm64"
    set "PYTHON_BINARY=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.zip"
) else if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "ARCH=x86"
    set "PYTHON_BINARY=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-win32.zip"
)

rem Download the Python ZIP archive
set "ZIP_PATH=%TEMP_DIR%\python.zip"
echo Downloading Python %PYTHON_VERSION%...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_BINARY%' -OutFile '%ZIP_PATH%'"

rem Extract the ZIP archive
echo Extracting Python files...
powershell -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%TEMP_DIR%' -Force"

rem Set the Python executable path
set "PYTHON_PATH=%TEMP_DIR%\python.exe"

rem Verify installation
if not exist "%PYTHON_PATH%" (
    echo ERROR: Python extraction failed.
    exit /b 1
)

rem Download the Python script from an online source
set "SCRIPT_URL=https://raw.githubusercontent.com/ChocoMeow/Vocard-Installer/refs/heads/main/installer.py"  rem Change to the actual URL of your Python script
set "SCRIPT_PATH=%SCRIPT_DIR%\script.py"
echo Downloading Python script...
powershell -Command "Invoke-WebRequest -Uri '%SCRIPT_URL%' -OutFile '%SCRIPT_PATH%'"

rem Check if the script was downloaded successfully
if not exist "%SCRIPT_PATH%" (
    echo ERROR: Failed to download the Python script.
    exit /b 1
)

rem Install pip if not already installed
echo Installing pip...
"%PYTHON_PATH%" -m ensurepip

rem Upgrade pip to the latest version
echo Upgrading pip...
"%PYTHON_PATH%" -m pip install --upgrade pip

rem Install pyyaml
echo Installing pyyaml package...
"%PYTHON_PATH%" -m pip install pyyaml

rem Execute the Python script
echo Running the Python script...
"%PYTHON_PATH%" "%SCRIPT_PATH%"

if %errorlevel% neq 0 (
    echo ERROR: The Python script failed to execute.
    pause
    exit /b 1
)

rem Clean up: Remove the temporary directory and all its contents
rd /s /q "%TEMP_DIR%"
echo Temporary Python environment removed.

echo Process completed successfully.
endlocal