@echo off
echo Setting up frontend environment...

REM Determine script and repository directories
setlocal enableextensions enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
REM Normalize path without trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Possible frontend directories relative to repo root
set "REPO_ROOT=%SCRIPT_DIR%"
set "FRONTEND_DIR=%REPO_ROOT%\frontend"

REM If the script is already in the frontend folder, use that
if exist "%SCRIPT_DIR%\package.json" (
    set "FRONTEND_DIR=%SCRIPT_DIR%"
)

REM If frontend folder does not exist, fall back to repo root
if not exist "%FRONTEND_DIR%" (
    echo Could not find frontend folder at "%FRONTEND_DIR%". Using repo root "%REPO_ROOT%" instead.
    set "FRONTEND_DIR=%REPO_ROOT%"
)

echo Using frontend directory: "%FRONTEND_DIR%"

REM Change to frontend directory
pushd "%FRONTEND_DIR%" || (
    echo Failed to change directory to "%FRONTEND_DIR%".
    exit /b 1
)

REM Parse optional --no-start flag
set "NO_START=0"
for %%A in (%*) do (
    if /i "%%~A"=="--no-start" set "NO_START=1"
)

REM Check if node_modules exists and has content
set "NEED_INSTALL=0"
if not exist "node_modules" (
    echo node_modules folder not found. Will install dependencies.
    set "NEED_INSTALL=1"
) else (
    echo node_modules folder exists. Checking if reinstall is needed...
    REM If package.json is newer than node_modules, or node_modules is empty, reinstall
    if exist "package.json" (
        REM Simple heuristic: if node_modules exists but is empty or has very few files, reinstall
        dir /b /a "node_modules" | findstr /r "." >nul
        if errorlevel 1 (
            echo node_modules is empty. Will install dependencies.
            set "NEED_INSTALL=1"
        ) else (
            echo node_modules appears populated. Skipping npm install.
            echo If dependencies are outdated, run: npm install
        )
    )
)

REM Install dependencies if needed
if "%NEED_INSTALL%"=="1" (
    echo Installing npm dependencies...
    npm install
    if errorlevel 1 (
        echo npm install failed. Ensure Node.js and npm are installed and on PATH.
        popd
        endlocal
        exit /b 1
    )
    echo Dependencies installed successfully.
)

if "%NO_START%"=="1" (
    echo Setup complete. Dev server start suppressed by --no-start flag.
    popd
    endlocal
    exit /b 0
)

REM Start the Vite dev server
echo Starting Vite dev server...
npm run dev

REM Return to original directory
popd
endlocal