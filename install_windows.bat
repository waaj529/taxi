@echo off
echo Ride Guardian Desktop - Windows Installer
echo ==========================================
echo.

echo Installing Ride Guardian Desktop...
echo.

:: Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\RideGuardian
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy executables
echo Copying files...
if exist "dist\RideGuardian-Launcher" (
    xcopy /E /I /Y "dist\RideGuardian-Launcher" "%INSTALL_DIR%\Launcher"
)

if exist "dist\RideGuardian-SingleCompany" (
    xcopy /E /I /Y "dist\RideGuardian-SingleCompany" "%INSTALL_DIR%\SingleCompany"
)

if exist "dist\RideGuardian-MultiCompany" (
    xcopy /E /I /Y "dist\RideGuardian-MultiCompany" "%INSTALL_DIR%\MultiCompany"
)

if exist "dist\RideGuardian-Main" (
    xcopy /E /I /Y "dist\RideGuardian-Main" "%INSTALL_DIR%\Main"
)

:: Create desktop shortcuts
echo Creating desktop shortcuts...
set DESKTOP=%USERPROFILE%\Desktop

:: Launcher shortcut
if exist "%INSTALL_DIR%\Launcher\RideGuardian-Launcher.exe" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Ride Guardian Launcher.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Launcher\RideGuardian-Launcher.exe'; $Shortcut.Save()"
)

:: Single Company shortcut
if exist "%INSTALL_DIR%\SingleCompany\RideGuardian-SingleCompany.exe" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Ride Guardian Single.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\SingleCompany\RideGuardian-SingleCompany.exe'; $Shortcut.Save()"
)

:: Multi Company shortcut
if exist "%INSTALL_DIR%\MultiCompany\RideGuardian-MultiCompany.exe" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Ride Guardian Multi.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\MultiCompany\RideGuardian-MultiCompany.exe'; $Shortcut.Save()"
)

echo.
echo Installation completed successfully!
echo Desktop shortcuts have been created.
echo.
pause
