@echo off
cd /d "%~dp0"
if exist "dist\RideGuardian-Launcher.exe" (
    start "" "dist\RideGuardian-Launcher.exe"
) else (
    echo RideGuardian-Launcher.exe not found in dist folder
    pause
)
