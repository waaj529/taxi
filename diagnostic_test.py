#!/usr/bin/env python3
"""
Ride Guardian Desktop - Diagnostic Test Script

This script tests the functionality of key features to identify what needs to be restored.
It performs non-destructive tests and reports the status of each feature.
"""

import os
import sys
import sqlite3
import time
from datetime import datetime, timedelta

# Ensure project root in PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import core modules - will capture ImportError if modules are missing
try:
    from core.database import get_db_connection, DATABASE_PATH
    from core.google_maps import GoogleMapsIntegration
    from core.translation_manager import translation_manager, tr
    from core.ride_validator import RideValidator
    from core.payroll_calculator import PayrollCalculator
    
    # Try to import export modules
    try:
        from core.enhanced_fahrtenbuch_export import EnhancedFahrtenbuchExporter
        fahrtenbuch_exporter_available = True
    except ImportError:
        fahrtenbuch_exporter_available = False
        
    # Check for API cache indicator
    try:
        from ui.components.api_cache_indicator import APICacheIndicator
        api_indicator_available = True
    except ImportError:
        api_indicator_available = False
        
    imports_successful = True
except ImportError as e:
    imports_successful = False
    import_error = str(e)

# Test results container
test_results = {
    "imports": {"status": "unknown", "details": "Not tested yet"},
    "database": {"status": "unknown", "details": "Not tested yet"},
    "translations": {"status": "unknown", "details": "Not tested yet"},
    "google_maps_api": {"status": "unknown", "details": "Not tested yet"},
    "google_maps_cache": {"status": "unknown", "details": "Not tested yet"},
    "ride_rules": {"status": "unknown", "details": "Not tested yet"},
    "payroll_calculation": {"status": "unknown", "details": "Not tested yet"},
    "export_functionality": {"status": "unknown", "details": "Not tested yet"},
}

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {text} ".center(80, "="))
    print("="*80)

def print_result(feature, status, details=None):
    """Print a test result with color coding"""
    status_map = {
        "pass": "\033[92mPASS\033[0m",  # Green
        "fail": "\033[91mFAIL\033[0m",  # Red
        "warning": "\033[93mWARNING\033[0m",  # Yellow
        "unknown": "\033[94mUNKNOWN\033[0m",  # Blue
    }
    
    status_str = status_map.get(status.lower(), status)
    print(f"  {feature:<30}: {status_str}")
    if details:
        print(f"    {details}")
    
    # Update test results
    test_results[feature] = {"status": status.lower(), "details": details or ""}

def test_imports():
    """Test if all required modules can be imported"""
    print_header("Testing Module Imports")
    
    if imports_successful:
        print_result("imports", "pass", "All core modules imported successfully")
    else:
        print_result("imports", "fail", f"Import error: {import_error}")
        
    # Test specific modules
    if fahrtenbuch_exporter_available:
        print_result("fahrtenbuch_exporter", "pass", "Enhanced Fahrtenbuch exporter available")
    else:
        print_result("fahrtenbuch_exporter", "fail", "Enhanced Fahrtenbuch exporter missing")
        
    if api_indicator_available:
        print_result("api_cache_indicator", "pass", "API Cache Indicator component available")
    else:
        print_result("api_cache_indicator", "fail", "API Cache Indicator component missing")

def test_database():
    """Test database connection and key tables"""
    print_header("Testing Database")
    
    try:
        if not os.path.exists(DATABASE_PATH):
            print_result("database", "fail", f"Database file not found at {DATABASE_PATH}")
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check key tables
        tables_to_check = [
            "companies", "drivers", "vehicles", "rides", "shifts", 
            "address_cache", "rules", "payroll"
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print_result(f"table_{table}", "pass", f"Table exists with {count} records")
            except sqlite3.Error as e:
                print_result(f"table_{table}", "fail", f"Error: {e}")
                
        # Check address cache specifically
        try:
            cursor.execute("SELECT COUNT(*) FROM address_cache")
            cache_count = cursor.fetchone()[0]
            if cache_count > 0:
                cursor.execute("SELECT * FROM address_cache LIMIT 1")
                sample = cursor.fetchone()
                print_result("address_cache", "pass", f"Cache has {cache_count} entries. Sample: {dict(sample)}")
            else:
                print_result("address_cache", "warning", "Address cache table exists but has no entries")
        except sqlite3.Error as e:
            print_result("address_cache", "fail", f"Error accessing address cache: {e}")
            
        conn.close()
        print_result("database", "pass", "Database connection successful")
    except Exception as e:
        print_result("database", "fail", f"Database test failed: {e}")

def test_translations():
    """Test translation functionality"""
    print_header("Testing Translations")
    
    try:
        # Test some key translations
        translations_to_test = [
            "Monitoring", "Drivers", "Vehicles", "Reports", 
            "Fahrtenbuch", "Stundenzettel", "Yes", "No"
        ]
        
        for text in translations_to_test:
            translated = tr(text)
            print_result(f"tr_{text}", "pass" if translated != text else "warning", 
                       f"'{text}' → '{translated}'")
            
        # Check if German translations are loaded
        translation_count = len(translation_manager.translations.get('de', {}))
        if translation_count > 0:
            print_result("translations", "pass", f"Found {translation_count} German translations")
        else:
            print_result("translations", "fail", "No German translations found")
            
    except Exception as e:
        print_result("translations", "fail", f"Translation test failed: {e}")

def test_google_maps():
    """Test Google Maps API integration and caching"""
    print_header("Testing Google Maps API and Caching")
    
    try:
        maps = GoogleMapsIntegration()
        
        # Test basic distance calculation
        origin = "Muster Str 1, 45451 MusterStadt"
        destination = "Goetheplatz 4, 45468 Mülheim an der Ruhr"
        
        print("Testing distance calculation...")
        distance1, duration1 = maps.calculate_distance_and_duration(origin, destination)
        print(f"First call: {distance1:.2f} km, {duration1:.2f} min")
        
        # Test caching - second call should use cache
        print("Testing cache (second call should be faster)...")
        start_time = time.time()
        distance2, duration2 = maps.calculate_distance_and_duration(origin, destination)
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Second call: {distance2:.2f} km, {duration2:.2f} min (took {execution_time:.5f} seconds)")
        
        # Check if results match (cached)
        if distance1 == distance2 and duration1 == duration2:
            if execution_time < 0.01:  # Very fast execution suggests cache hit
                print_result("google_maps_cache", "pass", 
                           f"Cache seems to be working (execution: {execution_time:.5f}s)")
            else:
                print_result("google_maps_cache", "warning", 
                           f"Results match but execution time suspicious: {execution_time:.5f}s")
        else:
            print_result("google_maps_cache", "fail", 
                       f"Cache test failed: different results {distance1} vs {distance2}")
            
        # Test if API is functional by forcing a new address
        unique_addr = f"Test Street {datetime.now().strftime('%H%M%S')}, Berlin"
        try:
            distance3, duration3 = maps.calculate_distance_and_duration(origin, unique_addr, use_cache=False)
            print(f"Unique address call: {distance3:.2f} km, {duration3:.2f} min")
            print_result("google_maps_api", "pass", "API returned results for a unique address")
        except Exception as e:
            print_result("google_maps_api", "warning", f"API call with unique address failed: {e}")
            
    except Exception as e:
        print_result("google_maps_api", "fail", f"Google Maps test failed: {e}")
        print_result("google_maps_cache", "fail", "Cache test skipped due to API failure")

def test_ride_rules():
    """Test ride validation rules"""
    print_header("Testing Ride Validation Rules")
    
    try:
        validator = RideValidator(company_id=1)
        
        # Create test ride data
        headquarters = "Muster Str 1, 45451 MusterStadt"
        
        # Test ride that should pass all rules
        valid_ride = {
            'id': 999,
            'driver_id': 1,
            'pickup_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pickup_location': headquarters,  # Starts at HQ (Rule 1)
            'destination': "Cecilienstraße 11, 47051 Duisburg",
            'standort_auftragsuebermittlung': headquarters,
            'abholort': headquarters,
            'zielort': "Cecilienstraße 11, 47051 Duisburg",
            'status': 'Pending',
            'distance_km': 15.0,
            'duration_minutes': 20.0,
            'is_reserved': False
        }
        
        # Test each rule
        rule_results = validator.validate_ride(valid_ride)
        
        if rule_results:
            print_result("ride_rules", "fail", f"Valid ride failed validation: {rule_results}")
            
            # Print details for each rule
            for rule_name, violation in rule_results.items():
                print_result(f"rule_{rule_name}", "fail", violation)
        else:
            print_result("ride_rules", "pass", "Valid ride passed all validation rules")
            
            # Test individual rules with invalid data
            # Rule 1: Shift Start at HQ
            invalid_ride = valid_ride.copy()
            invalid_ride['pickup_location'] = "Wrong Starting Point, Berlin"
            rule1_results = validator.validate_rule_1(invalid_ride)
            print_result("rule_1_hq_start", "pass" if rule1_results else "fail", 
                       "Rule 1 correctly identified non-HQ start" if rule1_results else "Rule 1 failed to detect violation")
            
            # Rule 2: Pickup Distance
            invalid_ride = valid_ride.copy()
            invalid_ride['distance_km'] = 30.0
            invalid_ride['duration_minutes'] = 35.0  # > 24 minutes
            rule2_results = validator.validate_rule_2(invalid_ride)
            print_result("rule_2_pickup_distance", "pass" if rule2_results else "fail", 
                       "Rule 2 correctly identified excessive pickup distance" if rule2_results else "Rule 2 failed to detect violation")
            
    except Exception as e:
        print_result("ride_rules", "fail", f"Ride rules test failed: {e}")

def test_payroll_calculation():
    """Test payroll calculation features"""
    print_header("Testing Payroll Calculation")
    
    try:
        calculator = PayrollCalculator(company_id=1)
        
        # Test basic pay calculation
        driver_id = 1
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        try:
            payroll_data = calculator.calculate_driver_payroll(
                driver_id=driver_id,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            print_result("payroll_calculation", "pass", f"Payroll calculation completed: {payroll_data}")
            
            # Test specific payroll components
            if 'base_pay' in payroll_data:
                print_result("payroll_base_pay", "pass", f"Base pay: {payroll_data['base_pay']}")
            else:
                print_result("payroll_base_pay", "fail", "Base pay calculation missing")
                
            if 'night_bonus' in payroll_data:
                print_result("payroll_night_bonus", "pass", f"Night bonus: {payroll_data['night_bonus']}")
            else:
                print_result("payroll_night_bonus", "fail", "Night bonus calculation missing")
                
        except Exception as e:
            print_result("payroll_calculation", "fail", f"Payroll calculation failed: {e}")
            
    except Exception as e:
        print_result("payroll_calculation", "fail", f"Payroll module test failed: {e}")

def test_export_functionality():
    """Test export functionality"""
    print_header("Testing Export Functionality")
    
    if not fahrtenbuch_exporter_available:
        print_result("export_functionality", "fail", "Enhanced Fahrtenbuch exporter not available")
        return
        
    try:
        exporter = EnhancedFahrtenbuchExporter(company_id=1)
        
        # Test Fahrtenbuch export
        driver_id = 1
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        test_file = os.path.join(project_root, "test_export_fahrtenbuch.xlsx")
        
        try:
            result = exporter.export_fahrtenbuch_excel_enhanced(
                driver_id=driver_id,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                output_path=test_file
            )
            
            if os.path.exists(test_file):
                file_size = os.path.getsize(test_file)
                print_result("fahrtenbuch_export", "pass", 
                           f"Fahrtenbuch exported successfully: {test_file} ({file_size} bytes)")
                # Clean up test file
                os.remove(test_file)
            else:
                print_result("fahrtenbuch_export", "fail", 
                           f"Export function returned success but file not found: {test_file}")
                
        except Exception as e:
            print_result("fahrtenbuch_export", "fail", f"Fahrtenbuch export failed: {e}")
            
        # Test Stundenzettel export
        test_file = os.path.join(project_root, "test_export_stundenzettel.xlsx")
        
        try:
            result = exporter.export_stundenzettel_excel(
                driver_id=driver_id,
                month=datetime.now().month,
                year=datetime.now().year,
                output_path=test_file
            )
            
            if os.path.exists(test_file):
                file_size = os.path.getsize(test_file)
                print_result("stundenzettel_export", "pass", 
                           f"Stundenzettel exported successfully: {test_file} ({file_size} bytes)")
                # Clean up test file
                os.remove(test_file)
            else:
                print_result("stundenzettel_export", "fail", 
                           f"Export function returned success but file not found: {test_file}")
                
        except Exception as e:
            print_result("stundenzettel_export", "fail", f"Stundenzettel export failed: {e}")
            
        print_result("export_functionality", "pass", "Export tests completed")
            
    except Exception as e:
        print_result("export_functionality", "fail", f"Export module test failed: {e}")

def run_all_tests():
    """Run all diagnostic tests"""
    print_header("Ride Guardian Diagnostic Tests")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Run tests in sequence
    test_imports()
    test_database()
    test_translations()
    test_google_maps()
    test_ride_rules()
    test_payroll_calculation()
    test_export_functionality()
    
    # Print summary
    print_header("Test Summary")
    
    pass_count = sum(1 for result in test_results.values() if result["status"] == "pass")
    fail_count = sum(1 for result in test_results.values() if result["status"] == "fail")
    warning_count = sum(1 for result in test_results.values() if result["status"] == "warning")
    
    print(f"Passed: {pass_count}")
    print(f"Failed: {fail_count}")
    print(f"Warnings: {warning_count}")
    
    print("\nFeatures needing restoration:")
    for feature, result in test_results.items():
        if result["status"] in ["fail", "warning"]:
            print(f"- {feature}: {result['details']}")
            
    print("\nWorking features:")
    for feature, result in test_results.items():
        if result["status"] == "pass":
            print(f"- {feature}")
            
    # Generate recommendations
    print_header("Restoration Recommendations")
    
    if test_results["google_maps_cache"]["status"] != "pass":
        print("1. Restore Google Maps API caching system:")
        print("   - Check implementation in core/google_maps.py")
        print("   - Verify address_cache table in database")
        print("   - Ensure APICacheIndicator is integrated in views\n")
        
    if test_results["export_functionality"]["status"] != "pass":
        print("2. Fix Excel/PDF export functionality:")
        print("   - Check EnhancedFahrtenbuchExporter implementation")
        print("   - Verify German templates are being followed")
        print("   - Test with sample data\n")
        
    if test_results["ride_rules"]["status"] != "pass":
        print("3. Restore ride validation rules:")
        print("   - Fix RideValidator implementation")
        print("   - Test each rule individually")
        print("   - Ensure German error messages are displayed\n")
        
    if test_results["payroll_calculation"]["status"] != "pass":
        print("4. Fix payroll calculation:")
        print("   - Check PayrollCalculator implementation")
        print("   - Verify bonus calculations")
        print("   - Test with different scenarios\n")

if __name__ == "__main__":
    run_all_tests() 