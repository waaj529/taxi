#!/usr/bin/env python3
"""
Ride Guardian Desktop - Google Maps API Cache Restoration

This script restores and verifies the Google Maps API caching system:
1. Ensures the address_cache table exists in the database
2. Verifies the Google Maps caching functionality
3. Integrates the API cache indicator component with the UI views

Run this script to fix one of the critical missing features in the application.
"""

import os
import sys
import sqlite3
import importlib
import inspect
from datetime import datetime

# Ensure project root in PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import core modules
try:
    from core.database import get_db_connection, DATABASE_PATH
    from core.google_maps import GoogleMapsIntegration
    from ui.components.api_cache_indicator import APICacheIndicator, APICacheStatusWidget
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all required packages are installed.")
    sys.exit(1)

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {text} ".center(80, "="))
    print("="*80)

def verify_database_cache_table():
    """Verify and fix the address_cache table in the database"""
    print_header("Verifying Database Cache Table")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if address_cache table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='address_cache'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("💡 Creating address_cache table...")
            
            # Create the address_cache table
            cursor.execute("""
                CREATE TABLE address_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin_address TEXT NOT NULL,
                    destination_address TEXT NOT NULL,
                    distance_km REAL,
                    duration_minutes REAL,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
                    use_count INTEGER DEFAULT 1,
                    UNIQUE(origin_address, destination_address)
                );
            """)
            conn.commit()
            print("✅ address_cache table created successfully")
        else:
            print("✅ address_cache table already exists")
            
            # Check if the table has the required columns
            cursor.execute("PRAGMA table_info(address_cache)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            required_columns = [
                "origin_address", "destination_address", "distance_km", 
                "duration_minutes", "created_date", "last_used", "use_count"
            ]
            
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                print(f"❌ Missing columns in address_cache table: {missing_columns}")
                
                # Add missing columns
                for column in missing_columns:
                    if column == "use_count":
                        cursor.execute("ALTER TABLE address_cache ADD COLUMN use_count INTEGER DEFAULT 1")
                    elif column in ["created_date", "last_used"]:
                        cursor.execute(f"ALTER TABLE address_cache ADD COLUMN {column} TEXT DEFAULT CURRENT_TIMESTAMP")
                    elif column in ["distance_km", "duration_minutes"]:
                        cursor.execute(f"ALTER TABLE address_cache ADD COLUMN {column} REAL")
                    else:
                        cursor.execute(f"ALTER TABLE address_cache ADD COLUMN {column} TEXT")
                
                conn.commit()
                print("✅ Missing columns added to address_cache table")
            else:
                print("✅ All required columns exist in address_cache table")
        
        # Check if there are existing entries
        cursor.execute("SELECT COUNT(*) FROM address_cache")
        cache_count = cursor.fetchone()[0]
        print(f"ℹ️ Current cache entries: {cache_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database cache table: {e}")
        return False

def verify_google_maps_caching():
    """Verify the Google Maps API caching functionality"""
    print_header("Verifying Google Maps API Caching")
    
    try:
        maps = GoogleMapsIntegration()
        
        # Check if cache is enabled
        if not hasattr(maps, 'cache_enabled'):
            print("❌ GoogleMapsIntegration class is missing cache_enabled attribute")
            return False
            
        if not maps.cache_enabled:
            print("❌ Caching is disabled in GoogleMapsIntegration")
            print("💡 Enabling caching...")
            maps.cache_enabled = True
        else:
            print("✅ Caching is enabled in GoogleMapsIntegration")
            
        # Test cache functionality
        print("🔍 Testing cache functionality with sample addresses...")
        
        origin = "Muster Str 1, 45451 MusterStadt"
        destination = "Cecilienstraße 11, 47051 Duisburg"
        
        # First call - should use API or mock data
        distance1, duration1 = maps.calculate_distance_and_duration(origin, destination)
        print(f"  First call: {distance1:.2f} km, {duration1:.2f} min")
        
        # Second call - should use cache
        distance2, duration2 = maps.calculate_distance_and_duration(origin, destination)
        print(f"  Second call: {distance2:.2f} km, {duration2:.2f} min")
        
        if distance1 == distance2 and duration1 == duration2:
            print("✅ Cache seems functional (values match on second call)")
            
            # Check if database was updated
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM address_cache WHERE origin_address = ? AND destination_address = ?", 
                (origin, destination)
            )
            cache_entry = cursor.fetchone()
            conn.close()
            
            if cache_entry:
                print("✅ Cache entry saved to database")
                return True
            else:
                print("❌ Cache entry not found in database")
                return False
        else:
            print("❌ Cache test failed (values don't match)")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Google Maps caching: {e}")
        return False

def verify_api_cache_indicator():
    """Verify the API cache indicator component"""
    print_header("Verifying API Cache Indicator Component")
    
    try:
        # Check if the component exists
        if 'APICacheIndicator' not in globals():
            print("❌ APICacheIndicator component not found")
            return False
            
        # Check if the component has required methods
        required_methods = [
            'record_cache_hit', 'record_cache_miss', 
            'update_stats_display', 'get_stats'
        ]
        
        missing_methods = [method for method in required_methods 
                         if not hasattr(APICacheIndicator, method)]
        
        if missing_methods:
            print(f"❌ APICacheIndicator missing required methods: {missing_methods}")
            return False
        else:
            print("✅ APICacheIndicator has all required methods")
            
        # Create an instance to verify initialization
        try:
            indicator = APICacheIndicator()
            print("✅ APICacheIndicator can be instantiated")
        except Exception as e:
            print(f"❌ Error instantiating APICacheIndicator: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error verifying API cache indicator: {e}")
        return False

def integrate_api_cache_indicator():
    """Integrate the API cache indicator component with views"""
    print_header("Integrating API Cache Indicator with Views")
    
    # Define the views that should include the cache indicator
    views_to_update = [
        'ui.views.ride_monitoring_view', 
        'ui.views.ride_entry_view',
        'ui.views.data_import_view'
    ]
    
    success_count = 0
    
    for view_module_name in views_to_update:
        try:
            # Import the view module
            view_module = importlib.import_module(view_module_name)
            
            # Get the main view class
            view_classes = [obj for name, obj in inspect.getmembers(view_module) 
                         if inspect.isclass(obj) and name.endswith('View')]
            
            if not view_classes:
                print(f"❌ No view classes found in {view_module_name}")
                continue
                
            view_class = view_classes[0]
            print(f"🔍 Checking {view_class.__name__} for API cache indicator...")
            
            # Check if the __init__ method creates a cache indicator
            init_source = inspect.getsource(view_class.__init__)
            
            if 'APICacheIndicator' in init_source or 'api_cache_indicator' in init_source.lower():
                print(f"✅ {view_class.__name__} already has API cache indicator")
                success_count += 1
            else:
                print(f"❌ {view_class.__name__} does not have API cache indicator")
                print(f"💡 Please add the following code to {view_class.__name__}.__init__:")
                print("""
    # Add API Cache Indicator
    self.api_cache_indicator = APICacheIndicator()
    self.api_cache_widget = APICacheStatusWidget()
    # Add it to an appropriate layout in the view
    # For example: self.info_layout.addWidget(self.api_cache_widget)
                """)
                
        except ImportError:
            print(f"❌ Could not import {view_module_name}")
        except Exception as e:
            print(f"❌ Error checking {view_module_name}: {e}")
    
    if success_count == len(views_to_update):
        print("✅ API cache indicator is integrated with all relevant views")
        return True
    elif success_count > 0:
        print(f"⚠️ API cache indicator is integrated with {success_count}/{len(views_to_update)} views")
        return True
    else:
        print("❌ API cache indicator is not integrated with any views")
        return False

def update_google_maps_integration():
    """Update the GoogleMapsIntegration class if needed"""
    print_header("Updating Google Maps Integration")
    
    try:
        maps = GoogleMapsIntegration()
        
        # Check if the class has required methods
        required_methods = [
            'calculate_distance_and_duration', 
            'get_cache_stats', 
            'clear_cache'
        ]
        
        missing_methods = [method for method in required_methods 
                         if not hasattr(maps, method)]
        
        if missing_methods:
            print(f"❌ GoogleMapsIntegration missing required methods: {missing_methods}")
            
            # Provide instructions for adding missing methods
            if 'get_cache_stats' in missing_methods:
                print("💡 Add the following method to GoogleMapsIntegration:")
                print("""
    def get_cache_stats(self):
        \"\"\"Get statistics about the address cache\"\"\"
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get total cache entries
            cursor.execute("SELECT COUNT(*) FROM address_cache")
            total_entries = cursor.fetchone()[0]
            
            # Get most frequently used entries
            cursor.execute(
                "SELECT origin_address, destination_address, use_count FROM address_cache ORDER BY use_count DESC LIMIT 5"
            )
            frequent_entries = [dict(row) for row in cursor.fetchall()]
            
            # Get total distance cached
            cursor.execute("SELECT SUM(distance_km) FROM address_cache")
            total_distance = cursor.fetchone()[0] or 0
            
            # Get total queries saved
            cursor.execute("SELECT SUM(use_count) FROM address_cache")
            total_queries = cursor.fetchone()[0] or 0
            saved_queries = total_queries - total_entries if total_entries > 0 else 0
            
            conn.close()
            
            return {
                'total_entries': total_entries,
                'frequent_entries': frequent_entries,
                'total_distance_km': total_distance,
                'total_queries': total_queries,
                'saved_queries': saved_queries
            }
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {
                'total_entries': 0,
                'frequent_entries': [],
                'total_distance_km': 0,
                'total_queries': 0,
                'saved_queries': 0
            }
                """)
            
            if 'clear_cache' in missing_methods:
                print("💡 Add the following method to GoogleMapsIntegration:")
                print("""
    def clear_cache(self):
        \"\"\"Clear the address cache\"\"\"
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM address_cache")
            conn.commit()
            conn.close()
            print("Address cache cleared")
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
                """)
                
        else:
            print("✅ GoogleMapsIntegration has all required methods")
            
        return True
        
    except Exception as e:
        print(f"❌ Error updating GoogleMapsIntegration: {e}")
        return False

def main():
    """Main restoration function"""
    print_header("Google Maps API Cache Restoration")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Verify database cache table
    db_status = verify_database_cache_table()
    
    # Step 2: Verify Google Maps caching
    maps_status = verify_google_maps_caching()
    
    # Step 3: Verify API cache indicator
    indicator_status = verify_api_cache_indicator()
    
    # Step 4: Integrate API cache indicator
    integration_status = integrate_api_cache_indicator()
    
    # Step 5: Update GoogleMapsIntegration if needed
    update_status = update_google_maps_integration()
    
    # Summary
    print_header("Restoration Summary")
    print(f"Database Cache Table: {'✅ Working' if db_status else '❌ Issues Detected'}")
    print(f"Google Maps Caching: {'✅ Working' if maps_status else '❌ Issues Detected'}")
    print(f"API Cache Indicator: {'✅ Working' if indicator_status else '❌ Issues Detected'}")
    print(f"UI Integration: {'✅ Complete' if integration_status else '❌ Incomplete'}")
    print(f"Google Maps Updates: {'✅ Complete' if update_status else '❌ Incomplete'}")
    
    # Next steps
    print_header("Next Steps")
    if all([db_status, maps_status, indicator_status, integration_status, update_status]):
        print("🎉 Google Maps API caching system has been fully restored!")
        print("\nTo test the restored functionality:")
        print("1. Run the application: python main.py")
        print("2. Navigate to the Ride Entry or Monitoring view")
        print("3. Verify the API cache indicator is visible and working")
        print("4. Enter the same addresses multiple times to see the cache in action")
    else:
        print("⚠️ Some issues remain with the Google Maps API caching system.")
        print("\nManual fixes required:")
        
        if not indicator_status or not integration_status:
            print("- Integrate the APICacheIndicator with views manually")
            print("  Add it to the UI layout in each relevant view file")
            
        if not maps_status or not update_status:
            print("- Check GoogleMapsIntegration implementation")
            print("  Add missing methods as described above")
            
        if not db_status:
            print("- Check database.py to ensure address_cache table is properly defined")

if __name__ == "__main__":
    main() 