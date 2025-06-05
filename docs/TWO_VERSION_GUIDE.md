# Ride Guardian Desktop - Two-Version Software Documentation

## Overview

This document describes the implementation of Ride Guardian Desktop in two distinct versions:

1. **Single Company Version** (`main_single_company.py`) - Simplified interface for managing one company's fleet
2. **Multi-Company Version** (`main_multi_company.py`) - Advanced interface for managing multiple companies

Both versions share the same core functionality but differ in their user interface and company management capabilities.

## Architecture Overview

### Core Components

- **`core/company_manager.py`** - Manages company operations and application modes
- **`core/database.py`** - Database operations and schema management
- **`core/translation_manager.py`** - Internationalization and German translations
- **`ui/views/`** - All user interface views (dashboard, rides, drivers, etc.)

### Key Features

- Fleet management (rides, drivers, vehicles)
- Payroll calculation and reporting
- Data import/export capabilities
- Violation tracking and alerts
- Multi-language support (German/English)
- Database management tools

## Version Differences

| Feature | Single Company | Multi-Company |
|---------|----------------|---------------|
| Company Selection | Automatic (default) | Manual selection dialog |
| Company Management | Hidden/Simplified | Full CRUD operations |
| Company Switching | Not available | Switch between companies |
| Interface Complexity | Simplified | Advanced with company bar |
| Database Mode | Single company data | Multi-company data isolation |
| Navigation | Standard sidebar | Extended with company info |

## Installation and Setup

### Prerequisites

```bash
# Required Python packages
pip install PyQt6
pip install openpyxl
pip install requests
pip install matplotlib
```

### Database Setup

The application automatically creates and initializes the SQLite database on first run:
- Database file: `ride_guardian.db`
- Automatic schema creation with enhanced company support
- Default company creation in single-company mode

## Usage Instructions

### Single Company Version

```bash
# Run the single company version
python main_single_company.py
```

**Features:**
- Simplified interface focused on one company
- No company selection dialogs
- Streamlined navigation
- All features available for the default company
- Company information displayed in header

**First-time Setup:**
1. Application creates default company automatically
2. Start adding drivers and vehicles
3. Begin recording rides and managing fleet

### Multi-Company Version

```bash
# Run the multi-company version
python main_multi_company.py
```

**Features:**
- Company selection dialog on startup
- Full company management (add, edit, delete companies)
- Switch between companies during operation
- Company information bar with statistics
- Separate data isolation per company

**First-time Setup:**
1. Application shows company selection dialog
2. Add new companies or use default company
3. Select active company to manage
4. All data is company-specific

## Company Management (Multi-Company Only)

### Adding Companies

1. Click "Manage Companies" button
2. Click "Add Company" in the management dialog
3. Fill in company details:
   - Company name (required)
   - Address
   - Phone number
   - Email address
4. Save the company

### Switching Companies

1. Click "Switch Company" button in the info bar
2. Select different company from the list
3. All views refresh with new company data
4. Statistics update automatically

### Company Data Isolation

- Each company maintains separate:
  - Driver records
  - Vehicle information
  - Ride history
  - Payroll data
  - Rules and configurations

## Technical Implementation

### Company Manager

The `CompanyManager` class handles:
- Application mode detection and storage
- Company CRUD operations
- Current company state management
- Data isolation between companies

```python
# Example usage
from core.company_manager import company_manager

# Check current mode
if company_manager.is_single_company_mode():
    # Single company logic
    pass
elif company_manager.is_multi_company_mode():
    # Multi-company logic
    pass

# Get current company
current_company = company_manager.get_current_company()
```

### Database Schema Enhancements

All major tables include `company_id` field for data isolation:
- `rides` table: Links to specific company
- `drivers` table: Company-specific drivers
- `vehicles` table: Company-specific vehicles
- `companies` table: Company master data

### Mode Persistence

Application mode is stored in the database configuration:
- `app_mode`: 'single' or 'multi'
- Persists between application sessions
- Can be changed through company manager

## User Interface Components

### Single Company Interface

- **Header**: Company name and basic statistics
- **Navigation**: Standard sidebar with main functions
- **Content**: Full-width content area
- **No company controls**: Streamlined for single company use

### Multi-Company Interface

- **Company Bar**: Current company info and switching controls
- **Navigation**: Standard sidebar with main functions
- **Company Management**: Add, edit, delete companies
- **Context Awareness**: All data filtered by current company

## Development Guidelines

### Adding New Features

1. **Single Company**: Implement directly in views
2. **Multi-Company**: Ensure company_id filtering in all database queries

### Database Queries

Always include company context in multi-company mode:

```python
# Example query with company filtering
cursor.execute("""
    SELECT * FROM rides 
    WHERE company_id = ? 
    ORDER BY pickup_time DESC
""", (company_manager.current_company_id,))
```

### View Refreshing

When switching companies, ensure all views refresh:

```python
def refresh_all_views(self):
    for i in range(self.stacked_widget.count()):
        widget = self.stacked_widget.widget(i)
        if hasattr(widget, 'company_id'):
            widget.company_id = company_manager.current_company_id
        if hasattr(widget, 'refresh_data'):
            widget.refresh_data()
```

## Configuration and Customization

### Language Settings

The application supports German by default with English fallback:
- Translation files in `translations/` directory
- Automatic language detection
- Runtime language switching capability

### Company Configuration

Each company can have specific settings:
- Payroll calculation rules
- Violation thresholds
- Reporting preferences
- Export formats

## Deployment

### Single Company Deployment

Ideal for:
- Small taxi companies
- Individual fleet operators
- Simple fleet management needs
- Users who want minimal complexity

### Multi-Company Deployment

Ideal for:
- Fleet management companies
- Multi-location operations
- Consulting firms managing multiple clients
- Large organizations with multiple subsidiaries

## File Structure

```
desktop_app/
├── main_single_company.py      # Single company entry point
├── main_multi_company.py       # Multi-company entry point
├── main.py                     # Original main file
├── core/
│   ├── company_manager.py      # Company management system
│   ├── database.py             # Database operations
│   └── translation_manager.py  # Internationalization
├── ui/
│   └── views/                  # All UI components
└── docs/
    └── TWO_VERSION_GUIDE.md    # This documentation
```

## Troubleshooting

### Common Issues

1. **Database locked**: Ensure no other instances are running
2. **Company not found**: Check company_id in database
3. **Translation missing**: Verify translation files exist
4. **Mode confusion**: Check stored app_mode in database

### Reset Application Mode

```python
# Reset to single company mode
from core.company_manager import company_manager
company_manager.save_app_mode('single')

# Reset to multi-company mode
company_manager.save_app_mode('multi')
```

## Future Enhancements

### Planned Features

1. **Cloud Synchronization**: Sync data between instances
2. **Advanced Reporting**: Cross-company analytics in multi-company mode
3. **User Management**: Different access levels per company
4. **API Integration**: RESTful API for external integrations
5. **Mobile App**: Companion mobile application

### Migration Path

Users can migrate between versions:
- Single → Multi: Enable multi-company mode, existing data becomes default company
- Multi → Single: Disable multi-company mode, select one company as default

## Support and Maintenance

### Version Control

Both versions share:
- Core business logic
- Database schema
- Translation system
- Most UI components

### Updates

Updates can be applied to both versions simultaneously since they share the core codebase. Only the main entry points and company management differ.

## Conclusion

The two-version approach provides flexibility for different user needs while maintaining a shared codebase. Users can choose the appropriate version based on their complexity requirements and easily upgrade from single to multi-company mode when needed.