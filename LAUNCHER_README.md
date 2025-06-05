# Ride Guardian Desktop - Launcher Usage Guide

## Quick Start

The application now includes a unified launcher that lets you choose between two versions:

### Running the Launcher

```bash
# Start the launcher to choose your version
python launcher.py
```

### Version Options

1. **Single Company Mode** (`main_single_company.py`)
   - Simplified interface for one company
   - Automatic setup with default company
   - Streamlined navigation
   - Perfect for small taxi companies

2. **Multi-Company Mode** (`main_multi_company.py`)
   - Advanced interface for multiple companies
   - Company selection and management
   - Data isolation between companies
   - Ideal for fleet management companies

### Direct Launch (Alternative)

You can still launch versions directly:

```bash
# Single company version
python main_single_company.py

# Multi-company version
python main_multi_company.py

# Original main file
python main.py
```

## Launcher Features

- **Visual Selection**: Choose between modes with radio buttons
- **Detailed Descriptions**: Get information about each version
- **Remember Choice**: Save your preference for future launches
- **Help System**: Built-in help with feature comparisons
- **Auto-Launch**: Automatically launch preferred version if remembered
- **German Interface**: Fully translated German interface

## First-Time Setup

1. Run `python launcher.py`
2. Select your preferred version:
   - **Single Company**: For simple fleet management
   - **Multi-Company**: For managing multiple companies
3. Check "Remember Choice" if you want to skip the launcher next time
4. Click "Launch Application"

## Switching Between Versions

You can always change your choice by:
1. Running `python launcher.py` again
2. Selecting a different version
3. Optionally updating your saved preference

## Configuration

The launcher saves your preference in `.launcher_config` file:
- To reset: Delete `.launcher_config` file
- To force launcher: Run with any command line argument

## Troubleshooting

### Launcher Won't Start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that PyQt6 is properly installed
- Verify you're in the correct directory

### Application Won't Launch
- Check console output for error messages
- Ensure target script files exist
- Verify database permissions

### Database Issues
- Both versions share the same database
- Company data is automatically separated
- Database is created automatically on first run

## Technical Notes

- All versions share the same core functionality
- Database schema supports both single and multi-company modes
- Translation system provides German localization
- Launcher uses subprocess to start the selected application
- Configuration is persisted between sessions