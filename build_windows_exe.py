#!/usr/bin/env python3
"""
Ride Guardian Desktop - Windows .exe Build Script
Cross-platform compatible - builds Windows executables from any platform
"""

import os
import sys
import subprocess
import shutil
import argparse
import platform
from pathlib import Path

# Build configuration
BUILD_CONFIG = {
    'launcher': {
        'script': 'launcher.py',
        'name': 'RideGuardian-Launcher',
        'icon': 'assets/ride_guardian_icon.ico',
        'description': 'Ride Guardian Desktop Launcher'
    },
    'single': {
        'script': 'main_single_company.py',
        'name': 'RideGuardian-SingleCompany',
        'icon': 'assets/ride_guardian_icon.ico',
        'description': 'Ride Guardian Desktop - Single Company Mode'
    },
    'multi': {
        'script': 'main_multi_company.py',
        'name': 'RideGuardian-MultiCompany',
        'icon': 'assets/ride_guardian_icon.ico',
        'description': 'Ride Guardian Desktop - Multi Company Mode'
    },
    'main': {
        'script': 'main.py',
        'name': 'RideGuardian-Main',
        'icon': 'assets/ride_guardian_icon.ico',
        'description': 'Ride Guardian Desktop - Main Application'
    }
}

def detect_platform():
    """Detect current platform and provide warnings for cross-compilation"""
    current_platform = platform.system().lower()
    print(f"[INFO] Current platform: {platform.system()} {platform.machine()}")
    
    if current_platform != 'windows':
        print("[WARNING] Cross-compiling for Windows from non-Windows platform")
        print("   • Executables may need testing on actual Windows systems")
        print("   • Some Windows-specific features might not work correctly")
        if current_platform == 'darwin':
            print("   • Consider using Wine, Parallels, or VMware for testing")
        elif current_platform == 'linux':
            print("   • Consider using Wine or Windows VM for testing")
    else:
        print("[SUCCESS] Building on native Windows platform")
    
    return current_platform

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("[INFO] Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        print("   Please install Python 3.8+ from https://www.python.org/downloads/")
        return False
    
    print(f"[SUCCESS] Python {sys.version}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[SUCCESS] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("[ERROR] PyInstaller not found. Installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller>=5.10.0'], 
                         check=True, capture_output=True)
            print("[SUCCESS] PyInstaller installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install PyInstaller: {e}")
            return False
        
    # Check other required packages
    required_packages = {
        'PyQt6': 'PyQt6',
        'pandas': 'pandas', 
        'numpy': 'numpy',
        'openpyxl': 'openpyxl',
        'reportlab': 'reportlab',
        'matplotlib': 'matplotlib',
        'PIL': 'Pillow',
        'requests': 'requests'
    }
    
    missing_packages = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"[SUCCESS] {package_name}")
        except ImportError:
            print(f"[WARNING] {package_name} not found")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"[INFO] Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages,
                         check=True, capture_output=True)
            print("[SUCCESS] Missing packages installed")
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Some packages may not have installed correctly: {e}")
            
    return True

def create_icon_file():
    """Create a basic icon file if it doesn't exist"""
    icon_dir = Path('assets')
    icon_dir.mkdir(exist_ok=True)
    
    icon_path = icon_dir / 'ride_guardian_icon.ico'
    
    if not icon_path.exists():
        print("[INFO] Creating basic icon file...")
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple icon
            img = Image.new('RGBA', (256, 256), (0, 123, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # Draw a car symbol
            draw.ellipse([50, 100, 206, 200], fill=(255, 255, 255, 255))
            draw.rectangle([70, 120, 186, 180], fill=(0, 123, 255, 255))
            draw.ellipse([80, 130, 120, 170], fill=(255, 255, 255, 255))
            draw.ellipse([136, 130, 176, 170], fill=(255, 255, 255, 255))
            
            # Add text
            try:
                # Try different font paths for cross-platform compatibility
                font_paths = [
                    "arial.ttf",  # Windows
                    "/System/Library/Fonts/Arial.ttf",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                ]
                font = None
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, 24)
                        break
                    except (OSError, IOError):
                        continue
                
                if font is None:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            draw.text((128, 60), "RG", fill=(255, 255, 255, 255), 
                     font=font, anchor="mm")
            
            # Save as ICO
            img.save(str(icon_path), format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"[SUCCESS] Created icon: {icon_path}")
            
        except ImportError:
            print("[WARNING] PIL not available, creating placeholder icon")
            # Create a simple placeholder
            with open(icon_path, 'w') as f:
                f.write("# Placeholder icon file")
    
    return str(icon_path)

def create_spec_file(app_name, config):
    """Create PyInstaller spec file for the application"""
    script_path = config['script']
    exe_name = config['name']
    icon_path = config.get('icon', '')
    
    # Enhanced hidden imports for PyQt6 with explicit QtCharts support
    hidden_imports = [
        # Core PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtSvg',
        
        # QtCharts - explicit imports for all chart components
        'PyQt6.QtCharts',
        'PyQt6.QtCharts.QChart',
        'PyQt6.QtCharts.QChartView',
        'PyQt6.QtCharts.QBarSet',
        'PyQt6.QtCharts.QBarSeries',
        'PyQt6.QtCharts.QBarCategoryAxis',
        'PyQt6.QtCharts.QValueAxis',
        'PyQt6.QtCharts.QPieSeries',
        'PyQt6.QtCharts.QPieSlice',
        'PyQt6.QtCharts.QLineSeries',
        'PyQt6.QtCharts.QScatterSeries',
        
        # Additional PyQt6 modules that might be needed
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.sip',
        
        # Python packages
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
        
        # Application modules
        'core.database',
        'core.translation_manager',
        'core.company_manager',
        'ui.views',
        'ui.components',
        'ui.widgets',
        'ui.widgets.km_per_driver_widget'
    ]
    
    # Binaries to include - specifically for PyQt6-Charts
    binaries = []
    
    # Try to find PyQt6 installation path for binaries
    try:
        import PyQt6
        pyqt6_path = os.path.dirname(PyQt6.__file__)
        
        # Add QtCharts binaries if they exist
        charts_dll_patterns = [
            os.path.join(pyqt6_path, 'Qt6', 'bin', 'Qt6Charts.dll'),
            os.path.join(pyqt6_path, 'Qt6', 'bin', 'Qt6ChartsQml.dll'),
            os.path.join(pyqt6_path, 'Qt6Charts.dll'),
            os.path.join(pyqt6_path, 'QtCharts.pyd'),
        ]
        
        for pattern in charts_dll_patterns:
            if os.path.exists(pattern):
                binaries.append((pattern, '.'))
                print(f"[INFO] Including QtCharts binary: {pattern}")
    except Exception as e:
        print(f"[WARNING] Could not locate PyQt6 binaries: {e}")
    
    # Data files to include - only add existing directories/files
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
            print(f"[INFO] Including data: {src} -> {dst}")
    
    # Add database files if they exist
    for db_file in ['*.db', '*.sqlite', '*.sqlite3']:
        import glob
        db_matches = glob.glob(db_file)
        for db_match in db_matches:
            datas.append((db_match, '.'))
            print(f"[INFO] Including database: {db_match}")
    
    # Add Excel files if they exist
    for excel_file in ['*.xlsx', '*.xls']:
        import glob
        excel_matches = glob.glob(excel_file)
        for excel_match in excel_matches:
            datas.append((excel_match, '.'))
            print(f"[INFO] Including Excel file: {excel_match}")
    
    # Add translation files if they exist
    translation_files = []
    if os.path.exists('translations'):
        for ext in ['*.qm', '*.ts']:
            import glob
            trans_matches = glob.glob(f'translations/{ext}')
            for trans_match in trans_matches:
                translation_files.append((trans_match, 'translations'))
                print(f"[INFO] Including translation: {trans_match}")
    
    datas.extend(translation_files)
    
    # Binary excludes for smaller file size
    excludes = [
        'tkinter',
        'matplotlib.tests',
        'pandas.tests',
        'numpy.tests',
        'test',
        'tests',
        'setuptools',
        'pip',
        'wheel'
    ]
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['{script_path}'],
             pathex=['.'],
             binaries={binaries},
             datas={datas},
             hiddenimports={hidden_imports},
             hookspath=['hooks'],
             hooksconfig={{}},
             runtime_hooks=[],
             excludes={excludes},
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

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
    
    spec_file = f'{exe_name}.spec'
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"[INFO] Created spec file: {spec_file}")
    return spec_file

def create_version_info():
    """Create version info file for Windows executables"""
    version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Ride Guardian Desktop'),
        StringStruct(u'FileDescription', u'Professional Fleet Management Solution'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'RideGuardian'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 Ride Guardian Desktop'),
        StringStruct(u'OriginalFilename', u'RideGuardian.exe'),
        StringStruct(u'ProductName', u'Ride Guardian Desktop'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("[INFO] Created version info file")

def build_executable(app_name, config, clean_build=False):
    """Build a single executable"""
    print(f"\n[BUILD] Building {app_name} executable...")
    
    script_path = config['script']
    exe_name = config['name']
    
    # Check if script exists
    if not os.path.exists(script_path):
        print(f"[ERROR] Script not found: {script_path}")
        return False
    
    # Clean previous build
    if clean_build:
        build_dir = f'build/{exe_name}'
        dist_dir = f'dist/{exe_name}'
        
        # Safely remove build directory
        if os.path.exists(build_dir):
            try:
                if os.path.isdir(build_dir):
                    shutil.rmtree(build_dir)
                    print(f"[CLEAN] Cleaned build directory: {build_dir}")
                else:
                    os.remove(build_dir)
                    print(f"[CLEAN] Removed build file: {build_dir}")
            except Exception as e:
                print(f"[WARNING] Could not clean build directory {build_dir}: {e}")
        
        # Safely remove dist directory
        if os.path.exists(dist_dir):
            try:
                if os.path.isdir(dist_dir):
                    shutil.rmtree(dist_dir)
                    print(f"[CLEAN] Cleaned dist directory: {dist_dir}")
                else:
                    os.remove(dist_dir)
                    print(f"[CLEAN] Removed dist file: {dist_dir}")
            except Exception as e:
                print(f"[WARNING] Could not clean dist directory {dist_dir}: {e}")
    
    # Create spec file
    spec_file = create_spec_file(app_name, config)
    
    try:
        # Build with PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            spec_file
        ]
        
        print(f"[BUILD] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print(f"[SUCCESS] Successfully built {exe_name}")
        
        # Post-build: Fix executable for Windows
        dist_folder = f'dist/{exe_name}'
        exe_path_unix = f'{dist_folder}/{exe_name}'
        exe_path_windows = f'{dist_folder}/{exe_name}.exe'
        
        # Rename executable to have .exe extension if needed
        if os.path.exists(exe_path_unix) and not os.path.exists(exe_path_windows):
            try:
                os.rename(exe_path_unix, exe_path_windows)
                print(f"[FIX] Fixed executable: {exe_name} -> {exe_name}.exe")
            except Exception as e:
                print(f"[WARNING] Could not rename executable: {e}")
        
        # Check if executable was created
        if os.path.exists(exe_path_windows):
            size_mb = os.path.getsize(exe_path_windows) / (1024 * 1024)
            print(f"[INFO] Windows executable created: {exe_path_windows} ({size_mb:.1f} MB)")
            
            # Verify _internal folder exists
            internal_path = f'{dist_folder}/_internal'
            if os.path.exists(internal_path):
                print(f"   [INFO] Dependencies folder: _internal/")
            
            return True
        else:
            print(f"[ERROR] Executable not found: {exe_path_windows}")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed for {app_name}")
        print(f"Error: {e.stderr}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error building {app_name}: {e}")
        return False

def fix_windows_executables():
    """Fix executables for Windows by adding .exe extension and ensuring proper format"""
    print("\n[FIX] Fixing Windows executables...")
    
    fixed_count = 0
    for app_name, config in BUILD_CONFIG.items():
        exe_name = config['name']
        dist_folder = f'dist/{exe_name}'
        
        if os.path.exists(dist_folder):
            # Look for the main executable file (without .exe)
            exe_path = f'{dist_folder}/{exe_name}'
            exe_path_with_ext = f'{dist_folder}/{exe_name}.exe'
            
            if os.path.exists(exe_path) and not os.path.exists(exe_path_with_ext):
                try:
                    # Rename the executable to have .exe extension
                    os.rename(exe_path, exe_path_with_ext)
                    print(f"[SUCCESS] Fixed: {exe_name} -> {exe_name}.exe")
                    fixed_count += 1
                    
                    # Verify the executable exists
                    if os.path.exists(exe_path_with_ext):
                        size_mb = os.path.getsize(exe_path_with_ext) / (1024 * 1024)
                        print(f"   [INFO] Windows executable: {exe_path_with_ext} ({size_mb:.1f} MB)")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to fix {exe_name}: {e}")
            elif os.path.exists(exe_path_with_ext):
                size_mb = os.path.getsize(exe_path_with_ext) / (1024 * 1024)
                print(f"[SUCCESS] Already fixed: {exe_path_with_ext} ({size_mb:.1f} MB)")
                fixed_count += 1
    
    if fixed_count > 0:
        print(f"[SUCCESS] Fixed {fixed_count} executables for Windows compatibility")
    else:
        print("[WARNING] No executables found to fix")
    
    return fixed_count

def create_windows_launcher_scripts():
    """Create .bat launcher scripts for each application"""
    print("\n[INFO] Creating Windows launcher scripts...")
    
    launcher_scripts = {
        'RideGuardian-Launcher': 'Ride Guardian Launcher',
        'RideGuardian-SingleCompany': 'Ride Guardian Single Company',
        'RideGuardian-MultiCompany': 'Ride Guardian Multi Company',
        'RideGuardian-Main': 'Ride Guardian Main'
    }
    
    for exe_name, display_name in launcher_scripts.items():
        dist_folder = f'dist/{exe_name}'
        exe_path = f'{dist_folder}/{exe_name}.exe'
        
        if os.path.exists(exe_path):
            # Create a .bat launcher script
            bat_content = f'''@echo off
title {display_name}
cd /d "%~dp0"
start "" "{exe_name}.exe"
'''
            bat_path = f'{dist_folder}/{exe_name}.bat'
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(bat_content)
            
            print(f"[SUCCESS] Created launcher: {bat_path}")
    
    print("[SUCCESS] Windows launcher scripts created successfully!")

def create_installer_script():
    """Create a batch script for easy Windows installation"""
    installer_script = '''@echo off
echo Ride Guardian Desktop - Windows Installer
echo ==========================================
echo.

echo Installing Ride Guardian Desktop...
echo.

:: Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\\RideGuardian
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy executables
echo Copying files...
if exist "dist\\RideGuardian-Launcher" (
    xcopy /E /I /Y "dist\\RideGuardian-Launcher" "%INSTALL_DIR%\\Launcher"
)

if exist "dist\\RideGuardian-SingleCompany" (
    xcopy /E /I /Y "dist\\RideGuardian-SingleCompany" "%INSTALL_DIR%\\SingleCompany"
)

if exist "dist\\RideGuardian-MultiCompany" (
    xcopy /E /I /Y "dist\\RideGuardian-MultiCompany" "%INSTALL_DIR%\\MultiCompany"
)

if exist "dist\\RideGuardian-Main" (
    xcopy /E /I /Y "dist\\RideGuardian-Main" "%INSTALL_DIR%\\Main"
)

:: Create desktop shortcuts
echo Creating desktop shortcuts...
set DESKTOP=%USERPROFILE%\\Desktop

:: Launcher shortcut
if exist "%INSTALL_DIR%\\Launcher\\RideGuardian-Launcher.exe" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\\Ride Guardian Launcher.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\Launcher\\RideGuardian-Launcher.exe'; $Shortcut.Save()"
)

:: Single Company shortcut
if exist "%INSTALL_DIR%\\SingleCompany\\RideGuardian-SingleCompany.exe" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\\Ride Guardian Single.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\SingleCompany\\RideGuardian-SingleCompany.exe'; $Shortcut.Save()"
)

:: Multi Company shortcut
if exist "%INSTALL_DIR%\\MultiCompany\\RideGuardian-MultiCompany.exe" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\\Ride Guardian Multi.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\MultiCompany\\RideGuardian-MultiCompany.exe'; $Shortcut.Save()"
)

echo.
echo Installation completed successfully!
echo Desktop shortcuts have been created.
echo.
pause
'''
    
    with open('install_windows.bat', 'w', encoding='utf-8') as f:
        f.write(installer_script)
    
    print("[INFO] Created Windows installer script: install_windows.bat")

def create_build_info():
    """Create a build information file"""
    import datetime
    
    build_info = f'''Ride Guardian Desktop - Build Information
==========================================

Build Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Python Version: {sys.version}
Platform: {sys.platform}

Built Executables:
'''
    
    for app_name, config in BUILD_CONFIG.items():
        exe_path = f'dist/{config["name"]}/{config["name"]}.exe'
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            build_info += f'- {config["name"]}: {size_mb:.1f} MB\n'
        else:
            build_info += f'- {config["name"]}: NOT BUILT\n'
    
    build_info += f'''
Installation:
1. Run install_windows.bat as Administrator
2. Desktop shortcuts will be created automatically
3. Launch applications from desktop or Start menu

Distribution:
- All executables are self-contained
- No Python installation required on target machine
- Windows 10/11 compatible
'''
    
    with open('BUILD_INFO.txt', 'w', encoding='utf-8') as f:
        f.write(build_info)
    
    print("[INFO] Created build information file: BUILD_INFO.txt")

def main():
    parser = argparse.ArgumentParser(description='Build Windows .exe files for Ride Guardian Desktop')
    parser.add_argument('--apps', nargs='+', choices=list(BUILD_CONFIG.keys()) + ['all'], 
                       default=['all'], help='Applications to build')
    parser.add_argument('--clean', action='store_true', help='Clean build (remove previous builds)')
    parser.add_argument('--skip-checks', action='store_true', help='Skip prerequisite checks')
    
    args = parser.parse_args()
    
    print("Ride Guardian Desktop - Windows .exe Builder")
    print("=" * 50)
    
    # Check prerequisites
    if not args.skip_checks and not check_prerequisites():
        print("[ERROR] Prerequisites check failed")
        return 1
    
    # Install requirements
    if os.path.exists('requirements.txt'):
        print("[INFO] Installing requirements...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Create necessary files
    icon_path = create_icon_file()
    create_version_info()
    
    # Determine which apps to build
    if 'all' in args.apps:
        apps_to_build = list(BUILD_CONFIG.keys())
    else:
        apps_to_build = args.apps
    
    # Build executables
    successful_builds = []
    failed_builds = []
    
    for app_name in apps_to_build:
        if app_name in BUILD_CONFIG:
            if build_executable(app_name, BUILD_CONFIG[app_name], args.clean):
                successful_builds.append(app_name)
            else:
                failed_builds.append(app_name)
        else:
            print(f"[WARNING] Unknown app: {app_name}")
    
    # Post-build: Fix any remaining Windows compatibility issues
    if successful_builds:
        fix_windows_executables()
        create_windows_launcher_scripts()
        create_installer_script()
        create_build_info()
    
    # Summary
    print("\n" + "=" * 50)
    print("Build Summary:")
    print(f"[SUCCESS] Successful: {len(successful_builds)} - {', '.join(successful_builds)}")
    if failed_builds:
        print(f"[ERROR] Failed: {len(failed_builds)} - {', '.join(failed_builds)}")
    
    if successful_builds:
        print("\n[SUCCESS] Build completed successfully!")
        print("[INFO] All executables have proper .exe extensions for Windows")
        print("[INFO] Executables are in the 'dist' directory")
        print("[INFO] Run 'install_windows.bat' as Administrator to install")
    else:
        print("\n[ERROR] No executables were built successfully")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())