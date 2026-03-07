@echo off
title Building GitHub Release Manager

echo ==================================================
echo      Building GitHub Release Manager EXE
echo ==================================================
echo.

REM Ensure we are in the script's directory
cd /d "%~dp0"

REM Check if PyInstaller is installed by checking its executable in PATH
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller not found.
    echo Please install it first by running: pip install pyinstaller ttkbootstrap
    echo.
    pause
    exit /b 1
)

echo [INFO] PyInstaller found. Starting the build process...
echo [INFO] This may take a few moments.
echo.

REM Run PyInstaller with the icon parameter
pyinstaller --noconfirm --onefile --windowed --name "GitHubReleaseManager" "main.py"
if %errorlevel% neq 0 (
    echo.
    echo [FAILURE] Build failed. Please check the output above for errors.
    goto end
)

echo.
echo ==================================================
echo Build process finished.
echo ==================================================
echo.

echo [SUCCESS] Executable created successfully!
echo You can find it in the 'dist' folder:
echo %cd%\dist\GitHubReleaseManager.exe
echo.
explorer "dist"

:end
echo.
echo Press any key to exit...
pause > nul