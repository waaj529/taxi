@echo off
cd /d "%~dp0"
if exist "dist\RideGuardian-SingleCompany.exe" (
    start "" "dist\RideGuardian-SingleCompany.exe"
) else (
    echo RideGuardian-SingleCompany.exe not found in dist folder
    pause
)
