#!/usr/bin/env python3
"""
Ride Guardian Desktop - Feature Restoration Tool

This script coordinates the restoration of all missing features:
1. Runs diagnostic tests to identify missing or broken features
2. Runs individual restoration scripts for each feature
3. Verifies the success of the restoration process

Run this script to restore all missing features in the application.
"""

import os
import sys
import subprocess
from datetime import datetime

# Ensure project root in PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {text} ".center(80, "="))
    print("="*80)

def run_diagnostic_test():
    """Run diagnostic tests to identify missing features"""
    print_header("Running Diagnostic Tests")
    
    try:
        result = subprocess.run(
            ["python", "diagnostic_test.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"⚠️ Diagnostic tests exited with code {result.returncode}")
        
        # Capture only the summary part
        output = result.stdout
        if "Test Summary" in output:
            summary_start = output.find("Test Summary")
            summary_end = output.find("Restoration Recommendations")
            if summary_end == -1:
                summary_end = len(output)
            
            print(output[summary_start:summary_end])
        else:
            print("⚠️ Could not find test summary in diagnostic output")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running diagnostic tests: {e}")
        return False

def restore_api_cache():
    """Restore Google Maps API caching"""
    print_header("Restoring Google Maps API Caching")
    
    try:
        result = subprocess.run(
            ["python", "restore_api_cache.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"⚠️ API cache restoration exited with code {result.returncode}")
        
        # Capture only the summary part
        output = result.stdout
        if "Restoration Summary" in output:
            summary_start = output.find("Restoration Summary")
            summary_end = output.find("Next Steps")
            if summary_end == -1:
                summary_end = len(output)
            
            print(output[summary_start:summary_end])
        else:
            print("⚠️ Could not find restoration summary in API cache output")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error restoring API cache: {e}")
        return False

def restore_excel_export():
    """Restore Excel export functionality"""
    print_header("Restoring Excel Export Functionality")
    
    try:
        result = subprocess.run(
            ["python", "restore_excel_export.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"⚠️ Excel export restoration exited with code {result.returncode}")
        
        # Capture only the summary part
        output = result.stdout
        if "Restoration Summary" in output:
            summary_start = output.find("Restoration Summary")
            summary_end = output.find("Next Steps")
            if summary_end == -1:
                summary_end = len(output)
            
            print(output[summary_start:summary_end])
        else:
            print("⚠️ Could not find restoration summary in Excel export output")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error restoring Excel export: {e}")
        return False

def restore_ride_validation():
    """Restore ride validation rules"""
    print_header("Restoring Ride Validation Rules")
    
    try:
        result = subprocess.run(
            ["python", "restore_ride_validation.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"⚠️ Ride validation restoration exited with code {result.returncode}")
        
        # Capture only the summary part
        output = result.stdout
        if "Diagnostic Summary" in output:
            summary_start = output.find("Diagnostic Summary")
            summary_end = output.find("Next Steps")
            if summary_end == -1:
                summary_end = len(output)
            
            print(output[summary_start:summary_end])
        else:
            print("⚠️ Could not find diagnostic summary in ride validation output")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error restoring ride validation: {e}")
        return False

def run_final_diagnostic():
    """Run a final diagnostic test after all restorations"""
    print_header("Running Final Diagnostic Tests")
    
    try:
        result = subprocess.run(
            ["python", "diagnostic_test.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Capture only the summary part
        output = result.stdout
        if "Test Summary" in output:
            summary_start = output.find("Test Summary")
            if "Restoration Recommendations" in output:
                summary_end = output.find("Restoration Recommendations")
            else:
                summary_end = len(output)
            
            print(output[summary_start:summary_end])
        else:
            print("⚠️ Could not find test summary in final diagnostic output")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running final diagnostic tests: {e}")
        return False

def main():
    """Main restoration function"""
    print_header("Ride Guardian Desktop - Feature Restoration Tool")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ask for confirmation
    print("\nThis tool will attempt to restore missing features in the application.")
    print("It is recommended to backup your files before continuing.")
    print("\nFeatures that will be restored:")
    print("1. Google Maps API Caching")
    print("2. Excel/PDF Export Functionality")
    print("3. Ride Validation Rules")
    
    confirmation = input("\nDo you want to continue with the restoration process? (y/n): ")
    if confirmation.lower() != 'y':
        print("Restoration process cancelled.")
        return
    
    # Step 1: Run diagnostic test
    print_header("Step 1: Initial Diagnostic")
    initial_diagnostic = run_diagnostic_test()
    
    # Step 2: Restore API cache
    print_header("Step 2: Restore Google Maps API Caching")
    api_cache_restored = restore_api_cache()
    
    # Step 3: Restore Excel export
    print_header("Step 3: Restore Excel Export")
    excel_export_restored = restore_excel_export()
    
    # Step 4: Restore ride validation
    print_header("Step 4: Restore Ride Validation")
    ride_validation_restored = restore_ride_validation()
    
    # Step 5: Run final diagnostic
    print_header("Step 5: Final Diagnostic")
    final_diagnostic = run_final_diagnostic()
    
    # Summary
    print_header("Restoration Summary")
    print(f"Google Maps API Caching: {'✅ Restored' if api_cache_restored else '❌ Not Restored'}")
    print(f"Excel Export Functionality: {'✅ Restored' if excel_export_restored else '❌ Not Restored'}")
    print(f"Ride Validation Rules: {'✅ Restored' if ride_validation_restored else '❌ Not Restored'}")
    print(f"Overall Restoration: {'✅ Complete' if all([api_cache_restored, excel_export_restored, ride_validation_restored]) else '⚠️ Partial'}")
    
    # Next steps
    print_header("Next Steps")
    if all([api_cache_restored, excel_export_restored, ride_validation_restored]):
        print("🎉 All features have been successfully restored!")
        print("\nTo verify the restoration:")
        print("1. Run the application: python main.py")
        print("2. Test each restored feature individually")
        print("3. Check for any remaining issues in the application")
    else:
        print("⚠️ Some features could not be fully restored.")
        print("\nManual fixes required:")
        
        if not api_cache_restored:
            print("- Check Google Maps API caching system")
            print("  Refer to the API cache restoration output for details")
            
        if not excel_export_restored:
            print("- Fix Excel export functionality")
            print("  Refer to the Excel export restoration output for details")
            
        if not ride_validation_restored:
            print("- Implement ride validation rules")
            print("  Refer to the ride validation restoration output for details")
            
        print("\nTry running the individual restoration scripts manually to fix specific issues.")

if __name__ == "__main__":
    main() 