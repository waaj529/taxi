# Ride Guardian Desktop - Executable Distribution

## Available Executables

### 1. RideGuardian-SingleCompany.exe
- **Purpose**: Single company fleet management
- **Features**: Simplified interface for one company
- **Best for**: Small taxi companies, individual operators

### 2. RideGuardian-MultiCompany.exe  
- **Purpose**: Multi-company fleet management
- **Features**: Company selection, data isolation, company management
- **Best for**: Fleet management companies, multi-location operations

### 3. RideGuardian-Launcher.exe
- **Purpose**: Mode selection launcher
- **Features**: Choose between single/multi-company modes
- **Best for**: Users who want flexibility to switch modes

## System Requirements

- Windows 10 or later (64-bit recommended)
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Internet connection (for Google Maps integration)

## Installation

1. Extract all files to a folder
2. Run the desired executable directly
3. Or use the provided batch files for convenience

## First Run

- Single Company: Automatically creates default company
- Multi-Company: Shows company selection dialog
- Launcher: Choose your preferred mode

## Database

- SQLite database file (ride_guardian.db) is created automatically
- Contains all your fleet data (rides, drivers, vehicles, etc.)
- Backup this file regularly

## Support

For issues or questions, refer to the documentation included with the application.

## Version Information

Built with:
- PyQt6 (GUI Framework)
- Python 3.x
- SQLite (Database)
- Various data processing libraries

Generated on: {import datetime; datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
