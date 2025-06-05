#!/usr/bin/env python3
"""
Enhanced Windows Build Script with Better Cross-Platform Compatibility
Addresses common PyInstaller cross-compilation issues
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def create_enhanced_spec_file(app_name, config):
    """Create enhanced PyInstaller spec file with better Windows compatibility"""
    script_path = config['script']
    exe_name = config['name']
    icon_path = config.get('icon', '')
    
    # Enhanced hidden imports for better Windows compatibility
    hidden_imports = [
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtSvg',
        'PyQt6.QtCharts',
        'PyQt6.sip',
        'pandas',
        'numpy',
        'openpyxl',
        'reportlab',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'PIL',
        'PIL._tkinter_finder',
        'requests',
        'sqlite3',
        'json',
        'csv',
        'datetime',
        'decimal',
        'email.mime.text',
        'email.mime.multipart',
        'urllib.parse',
        'urllib.request',
        'xml.etree.ElementTree',
        'xml.dom.minidom',
        'core.database',
        'core.translation_manager',
        'core.company_manager',
        'ui.views',
        'ui.components',
        'ui.widgets'
    ]
    
    # Windows-specific runtime hooks
    runtime_hooks = []
    
    # Enhanced data collection
    datas = []
    
    # Check for existing directories and files
    data_sources = [
        ('core', 'core'),
        ('ui', 'ui'),
        ('translations', 'translations'),
        ('assets', 'assets')
    ]
    
    for src, dst in data_sources:
        if os.path.exists(src):
            datas.append((src, dst))
    
    # Add all database and Excel files
    import glob
    for pattern in ['*.db', '*.sqlite', '*.sqlite3', '*.xlsx', '*.xls']:
        for file_match in glob.glob(pattern):
            datas.append((file_match, '.'))
    
    # Windows-specific binary excludes
    excludes = [
        'tkinter',
        'test',
        'tests',
        'setuptools',
        'pip',
        'wheel',
        'distutils',
        '_pytest',
        'py.test',
        'pytest',
        'numpy.tests',
        'pandas.tests',
        'matplotlib.tests'
    ]
    
    # Enhanced spec content with Windows optimizations
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Enhanced Windows Build Spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect additional data files
added_files = []
try:
    # Collect PyQt6 data files
    pyqt6_data = collect_data_files('PyQt6')
    added_files.extend(pyqt6_data)
except:
    pass

try:
    # Collect matplotlib data files
    matplotlib_data = collect_data_files('matplotlib')
    added_files.extend(matplotlib_data)
except:
    pass

a = Analysis(['{script_path}'],
             pathex=['.'],
             binaries=[],
             datas={datas} + added_files,
             hiddenimports={hidden_imports},
             hookspath=[],
             hooksconfig={{}},
             runtime_hooks={runtime_hooks},
             excludes={excludes},
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# Remove duplicate entries
a.datas = list(set(a.datas))

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='{exe_name}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          argv_emulation=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='{icon_path}',
          version_file='version_info.txt')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='{exe_name}')
'''
    
    spec_file = f'{exe_name}-enhanced.spec'
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    return spec_file

def create_portable_launcher():
    """Create a portable launcher that works on any Windows system"""
    launcher_content = '''@echo off
setlocal enabledelayedexpansion

title Ride Guardian Desktop - Portable Launcher
echo.
echo =========================================
echo  Ride Guardian Desktop - Portable Mode
echo =========================================
echo.

REM Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo Windows Version: %VERSION%
echo.

REM Check if running from network drive
set "CURRENT_DRIVE=%~d0"
if "%CURRENT_DRIVE:~0,2%"=="\\\\" (
    echo Warning: Running from network drive - performance may be slower
    echo.
)

REM Set working directory
cd /d "%~dp0"

REM Check available applications
echo Available Applications:
set APP_COUNT=0

if exist "RideGuardian-Launcher\\RideGuardian-Launcher.exe" (
    echo [1] Application Launcher
    set /a APP_COUNT+=1
    set APP1=RideGuardian-Launcher\\RideGuardian-Launcher.exe
)

if exist "RideGuardian-SingleCompany\\RideGuardian-SingleCompany.exe" (
    set /a APP_COUNT+=1
    echo [!APP_COUNT!] Single Company Mode
    set APP!APP_COUNT!=RideGuardian-SingleCompany\\RideGuardian-SingleCompany.exe
)

if exist "RideGuardian-MultiCompany\\RideGuardian-MultiCompany.exe" (
    set /a APP_COUNT+=1
    echo [!APP_COUNT!] Multi Company Mode  
    set APP!APP_COUNT!=RideGuardian-MultiCompany\\RideGuardian-MultiCompany.exe
)

if %APP_COUNT%==0 (
    echo No applications found!
    echo Please ensure all executable folders are present.
    pause
    exit /b 1
)

echo.
set /p CHOICE="Select application (1-%APP_COUNT%) or Q to quit: "

if /i "%CHOICE%"=="Q" exit /b 0

REM Validate choice
if %CHOICE% LSS 1 goto invalid
if %CHOICE% GTR %APP_COUNT% goto invalid

REM Launch selected application
echo.
echo Starting application...
call set SELECTED_APP=%%APP%CHOICE%%%
start "" "%SELECTED_APP%"

echo Application launched successfully!
echo You can close this window.
timeout /t 3 >nul
exit /b 0

:invalid
echo Invalid selection. Please try again.
pause
goto start
'''
    
    with open('START_RIDE_GUARDIAN.bat', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print("✅ Created portable launcher: START_RIDE_GUARDIAN.bat")

def main():
    print("🔧 Enhanced Windows Build Script")
    print("=" * 50)
    
    # Create enhanced builds
    from build_windows_exe import BUILD_CONFIG, build_executable
    
    for app_name, config in BUILD_CONFIG.items():
        print(f"\n🚀 Creating enhanced build for {app_name}...")
        
        # Create enhanced spec file
        enhanced_spec = create_enhanced_spec_file(app_name, config)
        
        # Build with enhanced spec
        try:
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--clean',
                '--noconfirm',
                enhanced_spec
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Enhanced build successful for {app_name}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Enhanced build failed for {app_name}: {e}")
    
    # Create portable launcher
    create_portable_launcher()
    
    print("\n🎉 Enhanced Windows build completed!")
    print("Use START_RIDE_GUARDIAN.bat for portable execution")

if __name__ == '__main__':
    main()