@echo off
REM Ride Guardian Desktop - Quick Windows Build Script
REM Cross-platform compatible - works on Windows, macOS, and Linux

echo.
echo ========================================
echo Ride Guardian Desktop - Windows Builder
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo Found Python:
python --version

REM Check if we're cross-compiling (detect non-Windows platforms)
echo.
echo Platform Detection:
python -c "import sys; print('Platform:', sys.platform)"
python -c "import sys; print('Warning: Cross-compiling for Windows' if sys.platform != 'win32' else 'Native Windows build')"

REM Install/update required packages
echo.
echo Installing required packages...
python -m pip install --upgrade pip

REM Check if requirements.txt exists
if exist requirements.txt (
    echo Installing from requirements.txt...
    python -m pip install -r requirements.txt
) else (
    echo No requirements.txt found, installing basic dependencies...
    python -m pip install PyQt6 pyinstaller pandas numpy openpyxl reportlab matplotlib pillow requests
)

REM Run the build script
echo.
echo Starting build process...
echo Running: python build_windows_exe.py --clean --apps all
echo.

python build_windows_exe.py --clean --apps all

REM Check build result
if errorlevel 1 (
    echo.
    echo ❌ Build failed! Check the error messages above.
    echo.
    echo Common solutions:
    echo - Make sure all dependencies are installed
    echo - Check that all Python files exist
    echo - Verify PyInstaller is working correctly
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Build process completed successfully!
echo.
echo Your executables are in the 'dist' folder:

REM List created executables if dist folder exists
if exist dist (
    echo.
    dir dist /AD /B 2>nul | findstr /R "." >nul
    if not errorlevel 1 (
        echo Available executables:
        for /d %%i in (dist\*) do (
            if exist "%%i\%%~ni.exe" (
                echo   • %%~ni.exe
            )
        )
    )
)

echo.
echo Cross-Platform Notes:
python -c "import sys; print('• Test on Windows before distribution' if sys.platform != 'win32' else '• Ready for Windows distribution')"
python -c "import sys; print('• Consider using Wine or Windows VM for testing' if sys.platform == 'darwin' else '')"

echo.
echo Installation:
echo - Run 'install_windows.bat' as Administrator on Windows
echo - Or run executables directly from dist folders
echo.
pause