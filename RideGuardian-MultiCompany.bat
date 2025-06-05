@echo off
cd /d "%~dp0"
if exist "dist\RideGuardian-MultiCompany.exe" (
    start "" "dist\RideGuardian-MultiCompany.exe"
) else (
    echo RideGuardian-MultiCompany.exe not found in dist folder
    pause
)
