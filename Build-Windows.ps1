# Ride Guardian Desktop - Advanced Windows Build Script
# PowerShell version with better error handling and progress tracking

param(
    [string[]]$Apps = @("all"),
    [switch]$Clean,
    [switch]$SkipChecks,
    [switch]$CreateInstaller
)

Write-Host "🚗 Ride Guardian Desktop - Windows .exe Builder" -ForegroundColor Blue
Write-Host "=" * 50 -ForegroundColor Blue

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check prerequisites
if (-not $SkipChecks) {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Python
    if (-not (Test-Command "python")) {
        Write-Host "❌ Python not found in PATH" -ForegroundColor Red
        Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
        exit 1
    }
    
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
    
    # Check pip
    if (-not (Test-Command "pip")) {
        Write-Host "❌ pip not found" -ForegroundColor Red
        Write-Host "Please reinstall Python with pip included" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ pip available" -ForegroundColor Green
    
    # Check if we're on Windows (for building Windows executables)
    if ($IsLinux -or $IsMacOS) {
        Write-Host "⚠️  Warning: Building Windows executables on non-Windows platform" -ForegroundColor Yellow
        Write-Host "   The executables may not work properly on Windows systems" -ForegroundColor Yellow
        Write-Host "   Consider using a Windows machine or virtual machine for production builds" -ForegroundColor Yellow
    }
}

# Install/upgrade dependencies
Write-Host "📦 Installing/upgrading dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip | Out-Null
    if (Test-Path "requirements.txt") {
        python -m pip install -r requirements.txt | Out-Null
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No requirements.txt found, installing basic dependencies..." -ForegroundColor Yellow
        python -m pip install PyQt6 pyinstaller pandas numpy openpyxl reportlab matplotlib pillow requests | Out-Null
    }
} catch {
    Write-Host "⚠️  Warning: Some dependencies may not have installed correctly" -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Build arguments
$buildArgs = @("--apps") + $Apps
if ($Clean) { $buildArgs += "--clean" }
if ($SkipChecks) { $buildArgs += "--skip-checks" }

# Run the build
Write-Host "🚀 Starting build process..." -ForegroundColor Yellow
Write-Host "Command: python build_windows_exe.py $($buildArgs -join ' ')" -ForegroundColor Cyan

try {
    & python "build_windows_exe.py" @buildArgs
    $buildResult = $LASTEXITCODE
    
    if ($buildResult -eq 0) {
        Write-Host "✅ Build completed successfully!" -ForegroundColor Green
        
        # List created executables
        if (Test-Path "dist") {
            Write-Host "`n📁 Created executables:" -ForegroundColor Yellow
            Get-ChildItem "dist" -Directory | ForEach-Object {
                $exePath = Join-Path $_.FullName "$($_.Name).exe"
                if (Test-Path $exePath) {
                    $sizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
                    Write-Host "  • $($_.Name).exe ($sizeMB MB)" -ForegroundColor White
                }
            }
        }
        
        # Create installer if requested
        if ($CreateInstaller -and (Test-Path "install_windows.bat")) {
            Write-Host "`n💿 Windows installer created: install_windows.bat" -ForegroundColor Green
            Write-Host "   Run as Administrator to install system-wide" -ForegroundColor Cyan
        }
        
        # Cross-platform notes
        if ($IsLinux -or $IsMacOS) {
            Write-Host "`n📝 Cross-platform build notes:" -ForegroundColor Yellow
            Write-Host "   • Test executables on actual Windows systems before distribution" -ForegroundColor Cyan
            Write-Host "   • Some Windows-specific features may not work correctly" -ForegroundColor Cyan
            Write-Host "   • Consider using Wine or a Windows VM for thorough testing" -ForegroundColor Cyan
        }
        
        Write-Host "`n🎉 All done! Your Windows executables are ready." -ForegroundColor Green
        
    } else {
        Write-Host "❌ Build failed with exit code $buildResult" -ForegroundColor Red
        exit $buildResult
    }
    
} catch {
    Write-Host "❌ Build process failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Cross-platform compatibility note
Write-Host "`n💡 Platform Information:" -ForegroundColor Cyan
if ($IsWindows) {
    Write-Host "   Running on Windows - executables should work properly" -ForegroundColor Green
} elseif ($IsMacOS) {
    Write-Host "   Running on macOS - cross-compiling for Windows" -ForegroundColor Yellow
    Write-Host "   Consider testing on Windows before distribution" -ForegroundColor Yellow
} elseif ($IsLinux) {
    Write-Host "   Running on Linux - cross-compiling for Windows" -ForegroundColor Yellow
    Write-Host "   Consider testing on Windows before distribution" -ForegroundColor Yellow
} else {
    Write-Host "   Unknown platform - results may vary" -ForegroundColor Yellow
}

# Pause if running interactively
if ($Host.Name -eq "ConsoleHost") {
    Write-Host "`nPress any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}