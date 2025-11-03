@echo off
echo Setting up backend environment...

REM Determine script and repository directories
setlocal enableextensions enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
REM Normalize path without trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Possible backend directories relative to repo root
set "REPO_ROOT=%SCRIPT_DIR%"
set "BACKEND_DIR=%REPO_ROOT%\backend"

REM If the script is already in the backend folder, use that
if exist "%SCRIPT_DIR%\app.py" (
    set "BACKEND_DIR=%SCRIPT_DIR%"
)

REM If backend folder does not exist, fall back to repo root
if not exist "%BACKEND_DIR%" (
    echo Could not find backend folder at "%BACKEND_DIR%". Using repo root "%REPO_ROOT%" instead.
    set "BACKEND_DIR=%REPO_ROOT%"
)

echo Using backend directory: "%BACKEND_DIR%"

REM Change to backend directory
pushd "%BACKEND_DIR%" || (
    echo Failed to change directory to "%BACKEND_DIR%".
    exit /b 1
)

REM Parse optional --no-start flag
set "NO_START=0"
for %%A in (%*) do (
    if /i "%%~A"=="--no-start" set "NO_START=1"
)

REM Create or reuse virtual environment in ./venv
if exist "venv\Scripts\python.exe" (
    echo Virtual environment found. Reusing ./venv
    set "EXISTING_VENV=1"
) else (
    echo Creating virtual environment in "%BACKEND_DIR%\venv"...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Ensure Python is installed and on PATH.
        popd
        exit /b 1
    )
    set "EXISTING_VENV=0"
)

REM Activate venv
call "venv\Scripts\activate"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    popd
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip (in venv)...
python -m pip install --upgrade pip setuptools wheel

REM Check for requirements file. Keep pip invocations outside parenthesized blocks to avoid parsing issues.
set "SKIP_INSTALL=0"
if exist "requirements.txt" (
    echo requirements.txt found.
) else (
    echo No requirements.txt found in "%BACKEND_DIR%". Skipping dependency installation.
    set "SKIP_INSTALL=1"
)

if "%SKIP_INSTALL%"=="0" (
    echo Installing dependencies from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        set "INSTALL_FAILED=1"
    ) else (
        set "INSTALL_FAILED=0"
    )
    if "%INSTALL_FAILED%"=="1" (
        if "%EXISTING_VENV%"=="1" (
            echo Installation failed when reusing existing venv. Trying to recreate venv and retry install...
            popd
            REM Remove venv folder and recreate
            rmdir /s /q "%BACKEND_DIR%\venv"
            if exist "%BACKEND_DIR%\venv" (
                echo Failed to remove old venv. Please remove it manually and re-run this script.
                exit /b 1
            )
            pushd "%BACKEND_DIR%"
            python -m venv venv
            if errorlevel 1 (
                echo Failed to recreate virtual environment. Ensure Python is installed and on PATH.
                popd
                exit /b 1
            )
            call "venv\Scripts\activate"
            if errorlevel 1 (
                echo Failed to activate recreated virtual environment.
                popd
                exit /b 1
            )
            echo Upgrading pip in recreated venv...
            python -m pip install --upgrade pip setuptools wheel
            echo Retrying dependency installation...
            python -m pip install -r requirements.txt
            if errorlevel 1 (
                echo Dependency installation failed after recreating venv. See output above.
                popd
                exit /b 1
            )
        ) else (
            echo Dependency installation failed. See output above.
            popd
            exit /b 1
        )
    )
)

if "%NO_START%"=="1" (
    echo Installation complete. Server start suppressed by --no-start flag.
    popd
    endlocal
    exit /b 0
)

REM Start the Flask application
set "FLASK_APP=app.py"
echo Using app.py (refactored modular version)

REM Start the Flask server
echo.
echo Starting Flask server ^(%FLASK_APP%^)...
python %FLASK_APP%

REM Return to original directory
popd
endlocal