# Ride Guardian Desktop - Windows .exe Build Guide

This guide explains how to create Windows executable (.exe) files for all Ride Guardian Desktop applications. **Now supports cross-platform building** - build Windows executables from macOS, Linux, or Windows!

## 📋 Prerequisites

- **Python 3.8+** installed and added to PATH
- **Git** (optional, for version control)
- At least **2GB free disk space** for build process
- **Windows 10/11** (for final testing of executables)

## 🚀 Quick Start

### Option 1: Simple Build (Recommended)
```bash
# On any platform (Windows/macOS/Linux)
python build_windows_exe.py
```

### Option 2: Batch Script (Windows or compatible shell)
```bash
# Double-click this file or run from command prompt
./build_windows.bat
```

### Option 3: PowerShell Build (Cross-platform PowerShell)
```powershell
# Works on Windows, macOS, and Linux with PowerShell Core
./Build-Windows.ps1

# Or with specific options
./Build-Windows.ps1 -Apps launcher,single -Clean -CreateInstaller
```

### Option 4: Manual Python Build (Full Control)
```bash
# Build all applications
python build_windows_exe.py --apps all

# Build specific applications
python build_windows_exe.py --apps launcher single

# Clean build (remove previous builds)
python build_windows_exe.py --clean

# Skip prerequisite checks (faster subsequent builds)
python build_windows_exe.py --skip-checks
```

## 🖥️ Cross-Platform Building

### Building from macOS (Your Current Setup)
```bash
# Install Python dependencies
python -m pip install -r requirements.txt

# Build Windows executables
python build_windows_exe.py --clean --apps all

# The script will warn about cross-compilation
# Executables will be created but should be tested on Windows
```

### Building from Linux
```bash
# Same process as macOS
python build_windows_exe.py --clean --apps all
```

### Building from Windows (Native)
```cmd
# Native Windows building - best compatibility
python build_windows_exe.py --clean --apps all
```

## ⚠️ Cross-Platform Considerations

When building from **macOS or Linux**:
- ✅ Executables will be created successfully
- ⚠️ **Must test on actual Windows systems** before distribution
- ⚠️ Some Windows-specific features may not work correctly
- 💡 Consider using Wine, Parallels, VMware, or Windows VM for testing

**Recommendation**: Build on your macOS for development, but test thoroughly on Windows before final distribution.

## 📦 What Gets Built

The build process creates executable files for:

1. **RideGuardian-Launcher.exe** - Application launcher/selector
2. **RideGuardian-SingleCompany.exe** - Single company mode
3. **RideGuardian-MultiCompany.exe** - Multi-company mode  
4. **RideGuardian-Main.exe** - Main application (legacy)

Each executable is:
- **Self-contained** - No Python installation needed on target machine
- **Optimized** - Includes only necessary dependencies
- **Windows-native** - Proper Windows integration with icons and version info

## 📁 Output Structure

After building, you'll find:

```
dist/
├── RideGuardian-Launcher/
│   ├── RideGuardian-Launcher.exe    # Main executable
│   ├── _internal/                   # Dependencies
│   └── ...
├── RideGuardian-SingleCompany/
│   ├── RideGuardian-SingleCompany.exe
│   └── ...
├── RideGuardian-MultiCompany/
│   ├── RideGuardian-MultiCompany.exe
│   └── ...
└── RideGuardian-Main/
    ├── RideGuardian-Main.exe
    └── ...

install_windows.bat              # Windows installer script
BUILD_INFO.txt                  # Build information
assets/ride_guardian_icon.ico   # Generated icon file
```

## 💿 Installation & Testing

### For End Users (Windows)
1. Run `install_windows.bat` **as Administrator**
2. Applications will be installed to `C:\Program Files\RideGuardian\`
3. Desktop shortcuts will be created automatically

### For Developers/Testing
- **Cross-platform testing**: Run executables directly from `dist/` folders
- **Windows testing**: Transfer `dist/` folder to Windows machine and test
- **No installation required** for testing

## 🛠️ Build Configuration

### Applications Built

| Application | Script | Description | Build Priority |
|-------------|--------|-------------|----------------|
| Launcher | `launcher.py` | User-friendly application selector | High |
| Single Company | `main_single_company.py` | Single company fleet management | High |
| Multi Company | `main_multi_company.py` | Multi-company fleet management | High |
| Main | `main.py` | Legacy main application | Low |

### Build Options

```bash
# Build specific applications only
python build_windows_exe.py --apps launcher single

# Clean build (removes previous builds)
python build_windows_exe.py --clean

# Skip prerequisite checks (faster)
python build_windows_exe.py --skip-checks

# Get help and see all options
python build_windows_exe.py --help
```

### PowerShell Options

```powershell
# Clean build
./Build-Windows.ps1 -Clean

# Build specific apps
./Build-Windows.ps1 -Apps launcher,single

# Skip checks for faster builds
./Build-Windows.ps1 -SkipChecks

# Create installer package
./Build-Windows.ps1 -CreateInstaller
```

## 🔧 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
- Make sure Python is added to PATH during installation
- Restart terminal/command prompt after installation

**"PyInstaller not found"**
- Run: `pip install pyinstaller`
- Or let the build script install it automatically

**"Build failed - missing module"**
- Run: `pip install -r requirements.txt`
- Check that all dependencies are installed
- On macOS: `brew install python-tk` if tkinter issues occur

**"Access denied during installation"**
- Run `install_windows.bat` as Administrator on Windows
- Right-click → "Run as administrator"

**Large executable size (50-150MB per exe)**
- This is normal for PyQt6 applications
- The executables are self-contained with all dependencies
- Size is acceptable for desktop applications

**Cross-platform build warnings**
- These are informational - builds will still work
- Test thoroughly on Windows before distribution
- Consider using Windows VM for final validation

### Debug Mode

For detailed error information:
```bash
# Verbose output with error details
python build_windows_exe.py --apps launcher 2>&1 | tee build.log

# On macOS/Linux, check for missing system dependencies
python -c "import PyQt6; print('PyQt6 OK')"
```

### macOS-Specific Issues

```bash
# If you encounter font-related errors
brew install freetype

# If PIL/Pillow has issues
pip install --upgrade Pillow

# If PyQt6 installation fails
pip install --upgrade pip setuptools wheel
pip install PyQt6
```

## 📋 System Requirements

### Build Machine (Your macOS Setup)
- macOS 10.14+ (your current system)
- Python 3.8+
- 4GB RAM (recommended)
- 2GB free disk space
- Xcode command line tools (for some dependencies)

### Target Machines (End Users)
- Windows 10/11 (64-bit)
- No Python installation required
- 100MB free disk space per application

## 🔄 Development Workflow

### Quick Development Cycle (macOS)
1. **Code changes**: Edit Python files
2. **Quick build**: `python build_windows_exe.py --apps launcher --skip-checks`
3. **Test locally**: Run Python script directly for development
4. **Windows testing**: Transfer to Windows VM/machine periodically

### Release Workflow
1. **Full clean build**: `python build_windows_exe.py --clean`
2. **Windows testing**: Test all executables on Windows
3. **Package**: Use `install_windows.bat` for distribution
4. **Document**: Update version in `BUILD_INFO.txt`

## 📊 Build Performance

Typical build times on modern hardware:
- **Launcher**: 2-3 minutes
- **Single Company**: 3-4 minutes  
- **Multi Company**: 3-4 minutes
- **Main**: 3-4 minutes
- **Total (all apps)**: 10-15 minutes

**macOS Cross-compilation**: Same performance as native builds.

## 🔐 Security & Distribution Notes

- Executables are not code-signed by default
- Windows may show "Unknown publisher" warning
- For commercial distribution, consider code signing certificates
- Antivirus software may flag PyInstaller executables (false positive)
- Cross-compiled executables have same security characteristics

## 📝 Version Information

The build process automatically includes:
- Version info in executable properties
- Company name: "Ride Guardian Desktop"
- File description: "Professional Fleet Management Solution"
- Copyright notice
- Product version: 1.0.0.0

## 💡 Tips for macOS Developers

1. **Use Python virtual environments** for clean builds:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Regular Windows testing**: Set up a Windows VM or use cloud Windows instances

3. **Automated testing**: Consider GitHub Actions or similar for Windows builds

4. **Font compatibility**: The build script handles cross-platform font differences automatically

## 🆘 Support & Troubleshooting

If you encounter issues:

1. Check the `BUILD_INFO.txt` file for build details
2. Review console output for error messages
3. Ensure all prerequisites are installed
4. Try a clean build: `python build_windows_exe.py --clean`
5. Test with a simple app first: `python build_windows_exe.py --apps launcher`

### macOS-Specific Support

```bash
# Check Python installation
which python
python --version

# Check installed packages
pip list | grep -E "(PyQt6|pyinstaller|pandas)"

# Test PyQt6 installation
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 working')"
```

---

**Happy Building from macOS! 🚗💨**

*Cross-platform development made easy - build once, run on Windows!*