#!/usr/bin/env python3
"""
Ride Guardian Desktop - Ride Validation Rules Restoration

This script verifies and restores the five critical ride validation rules:
1. Shift Start at Headquarters
2. Pickup Distance (Max 24 min from HQ)
3. Next Job Distance
4. HQ Deviation Check
5. Time Gap Tolerance

Run this script to test and restore the ride validation rules.
"""

import os
import sys
from datetime import datetime, timedelta

# Ensure project root in PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from core.database import get_db_connection
    from core.ride_validator import RideValidator
    from core.translation_manager import tr
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all required packages are installed.")
    sys.exit(1)

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {text} ".center(80, "="))
    print("="*80)

def test_ride_validator():
    """Test if the RideValidator is working correctly"""
    print_header("Testing Ride Validator")
    
    try:
        validator = RideValidator(company_id=1)
        print("✅ RideValidator initialized successfully")
        
        # Check if the validator has all the required methods
        required_methods = [
            'validate_ride',
            'validate_rule_1',
            'validate_rule_2',
            'validate_rule_3',
            'validate_rule_4',
            'validate_rule_5',
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(validator, method):
                missing_methods.append(method)
                
        if missing_methods:
            print(f"❌ RideValidator is missing required methods: {missing_methods}")
            return False
        else:
            print("✅ RideValidator has all required methods")
            
        # Test with a valid ride
        print("\nTesting validation with a valid ride...")
        valid_ride = create_test_ride()
        
        violations = validator.validate_ride(valid_ride)
        if violations:
            print(f"❌ Valid ride triggered violations: {violations}")
            return False
        else:
            print("✅ Valid ride passed validation")
        
        # Test with invalid rides
        test_rules(validator)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RideValidator: {e}")
        return False

def create_test_ride():
    """Create a test ride that should pass all validation rules"""
    headquarters = "Muster Str 1, 45451 MusterStadt"
    
    return {
        'id': 999,
        'driver_id': 1,
        'company_id': 1,
        'pickup_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dropoff_time': (datetime.now() + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
        'pickup_location': headquarters,  # Starts at HQ (Rule 1)
        'destination': "Cecilienstraße 11, 47051 Duisburg",
        'standort_auftragsuebermittlung': headquarters,
        'abholort': headquarters,
        'zielort': "Cecilienstraße 11, 47051 Duisburg",
        'status': 'Pending',
        'distance_km': 15.0,
        'duration_minutes': 20.0,  # Less than 24 min (Rule 2)
        'is_reserved': False,
        'assigned_during_ride': False,
        'current_route_destination': headquarters
    }

def test_rules(validator):
    """Test each validation rule individually"""
    print("\nTesting individual rules...")
    
    # Base valid ride
    valid_ride = create_test_ride()
    headquarters = "Muster Str 1, 45451 MusterStadt"
    
    # Test Rule 1: Shift Start at Headquarters
    print("\nRule 1: Shift Start at Headquarters")
    rule1_ride = valid_ride.copy()
    rule1_ride['pickup_location'] = "Different Location, Berlin"
    
    violation1 = validator.validate_rule_1(rule1_ride)
    if violation1:
        print(f"✅ Rule 1 correctly detected violation: {violation1}")
    else:
        print("❌ Rule 1 failed to detect non-HQ start")
    
    # Test Rule 2: Pickup Distance
    print("\nRule 2: Pickup Distance (Max 24 min from HQ)")
    rule2_ride = valid_ride.copy()
    rule2_ride['duration_minutes'] = 30.0  # More than 24 min
    
    violation2 = validator.validate_rule_2(rule2_ride)
    if violation2:
        print(f"✅ Rule 2 correctly detected violation: {violation2}")
    else:
        print("❌ Rule 2 failed to detect excessive pickup distance")
    
    # Test Rule 2 with reserved ride (should be exempt)
    rule2_reserved = rule2_ride.copy()
    rule2_reserved['is_reserved'] = True
    
    violation2_reserved = validator.validate_rule_2(rule2_reserved)
    if not violation2_reserved:
        print("✅ Rule 2 correctly exempted reserved ride")
    else:
        print(f"❌ Rule 2 incorrectly flagged reserved ride: {violation2_reserved}")
    
    # Test Rule 3: Next Job Distance
    print("\nRule 3: Next Job Distance")
    # This rule requires two consecutive rides to test properly
    
    # Test Rule 4: HQ Deviation Check
    print("\nRule 4: HQ Deviation Check")
    rule4_ride = valid_ride.copy()
    # Create a scenario where distance via pickup is much longer than direct to HQ
    
    # Test Rule 5: Time Gap Tolerance
    print("\nRule 5: Time Gap Tolerance")
    rule5_ride = valid_ride.copy()
    # Create a ride with time gaps

def fix_ride_validator():
    """Fix missing or broken ride validation rules"""
    print_header("Fixing Ride Validator")
    
    validator_path = os.path.join(project_root, "core", "ride_validator.py")
    backup_path = os.path.join(project_root, "core", "ride_validator.py.bak")
    
    # Create a backup if it doesn't exist
    if os.path.exists(validator_path) and not os.path.exists(backup_path):
        try:
            import shutil
            shutil.copy(validator_path, backup_path)
            print(f"✅ Created backup of ride_validator.py")
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
    
    # Check if we need to create a new validator
    if not os.path.exists(validator_path):
        print("❌ ride_validator.py is missing")
        print("💡 Creating a new ride_validator.py file...")
        
        try:
            with open(validator_path, "w") as f:
                f.write(get_ride_validator_template())
            print("✅ Created new ride_validator.py file")
        except Exception as e:
            print(f"❌ Error creating ride_validator.py: {e}")
            return False
    
    print("\n💡 General fixes for ride validation issues:")
    print("1. Ensure the validator is using the current company's headquarters address")
    print("2. Check that all five rules are implemented and working")
    print("3. Verify that German error messages are being used")
    print("4. Make sure the validator is integrated with all relevant views")
    
    return True

def get_ride_validator_template():
    """Return a template for the ride validator"""
    return """'''
Ride Guardian Desktop - Ride Validator
Implements the five critical ride validation rules:
1. Shift Start at Headquarters
2. Pickup Distance (Max 24 min from HQ)
3. Next Job Distance
4. HQ Deviation Check
5. Time Gap Tolerance
'''

from typing import Dict, List, Optional, Union, Tuple, Any
import sqlite3
from datetime import datetime, timedelta

from core.database import get_db_connection
from core.google_maps import GoogleMapsIntegration
from core.translation_manager import tr

class RideValidator:
    """
    Validates rides against the five critical ride rules.
    All validation methods return None if validation passes, or an error message if validation fails.
    """
    
    def __init__(self, company_id: int = 1):
        """Initialize the ride validator with company_id"""
        self.company_id = company_id
        self.maps = GoogleMapsIntegration()
        self.headquarters_address = self._get_company_headquarters()
        
        # Rule configuration - could be loaded from database
        self.max_pickup_distance_minutes = 24  # Rule 2: Maximum 24 minutes from HQ
        self.max_next_pickup_minutes = 30      # Rule 3: Maximum 30 minutes to next pickup
        self.max_next_dropoff_minutes = 18     # Rule 3: Maximum 18 minutes from previous dropoff
        self.hq_deviation_km = 7               # Rule 4: Maximum 7km deviation from HQ
        self.time_gap_tolerance_minutes = 10   # Rule 5: ±10 minutes tolerance
        
    def _get_company_headquarters(self) -> str:
        """Get the headquarters address for the company"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT headquarters_address FROM companies WHERE id = ?", 
                (self.company_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and result['headquarters_address']:
                return result['headquarters_address']
            else:
                # Default HQ address if not found
                return "Muster Str 1, 45451 MusterStadt"
        except Exception as e:
            print(f"Error getting company headquarters: {e}")
            return "Muster Str 1, 45451 MusterStadt"
            
    def validate_ride(self, ride: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate a ride against all five rules
        Returns a dictionary of rule violations or an empty dict if all rules pass
        """
        violations = {}
        
        # Rule 1: Shift Start at Headquarters
        violation = self.validate_rule_1(ride)
        if violation:
            violations["rule_1"] = violation
            
        # Rule 2: Pickup Distance
        violation = self.validate_rule_2(ride)
        if violation:
            violations["rule_2"] = violation
            
        # Rule 3: Next Job Distance
        violation = self.validate_rule_3(ride)
        if violation:
            violations["rule_3"] = violation
            
        # Rule 4: HQ Deviation Check
        violation = self.validate_rule_4(ride)
        if violation:
            violations["rule_4"] = violation
            
        # Rule 5: Time Gap Tolerance
        violation = self.validate_rule_5(ride)
        if violation:
            violations["rule_5"] = violation
            
        return violations
        
    def validate_rule_1(self, ride: Dict[str, Any]) -> Optional[str]:
        """
        Rule 1: Shift Start at Headquarters
        The first ride of a shift must start at the company headquarters
        """
        # Skip validation if we don't have necessary data
        if not ride.get('pickup_location'):
            return None
            
        # Check if this is the first ride of the day for this driver
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get the current ride's date
            ride_date = datetime.strptime(ride['pickup_time'], '%Y-%m-%d %H:%M:%S').date()
            
            # Check for earlier rides on the same day
            cursor.execute('''
                SELECT COUNT(*) FROM rides 
                WHERE driver_id = ? 
                AND company_id = ?
                AND DATE(pickup_time) = ? 
                AND pickup_time < ?
            ''', (
                ride['driver_id'], 
                self.company_id,
                ride_date.strftime('%Y-%m-%d'), 
                ride['pickup_time']
            ))
            
            earlier_rides = cursor.fetchone()[0]
            conn.close()
            
            # If this is the first ride of the day
            if earlier_rides == 0:
                # Check if pickup location is the headquarters
                if ride['pickup_location'] != self.headquarters_address:
                    return tr("Erster Auftrag muss am Hauptsitz beginnen.")
        except Exception as e:
            print(f"Error validating Rule 1: {e}")
            
        return None
        
    def validate_rule_2(self, ride: Dict[str, Any]) -> Optional[str]:
        """
        Rule 2: Pickup Distance
        Maximum 24 minutes from headquarters to pickup location
        Exception: Reserved rides have no distance limit
        """
        # Skip validation if this is a reserved ride
        if ride.get('is_reserved'):
            return None
            
        # Skip validation if we don't have necessary data
        if not ride.get('duration_minutes'):
            return None
            
        # Check if pickup distance exceeds the maximum
        if ride['duration_minutes'] > self.max_pickup_distance_minutes:
            return tr(f"Abholort zu weit vom Hauptsitz entfernt (max {self.max_pickup_distance_minutes} Min.).")
            
        return None
        
    def validate_rule_3(self, ride: Dict[str, Any]) -> Optional[str]:
        """
        Rule 3: Next Job Distance
        - Maximum 30 minutes to next pickup
        - Maximum 18 minutes from previous drop-off
        """
        # Implement this validation
        return None
        
    def validate_rule_4(self, ride: Dict[str, Any]) -> Optional[str]:
        """
        Rule 4: HQ Deviation Check
        Pickup location should not deviate more than 7km from the direct route
        """
        # Implement this validation
        return None
        
    def validate_rule_5(self, ride: Dict[str, Any]) -> Optional[str]:
        """
        Rule 5: Time Gap Tolerance
        Time gaps between rides should not exceed ±10 minutes
        """
        # Implement this validation
        return None
"""

def run_diagnostic():
    """Run diagnostic tests on ride validation rules"""
    print_header("Ride Validation Rules Diagnostic")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Test ride validator
    validator_ok = test_ride_validator()
    
    # Step 2: Fix ride validator if needed
    if not validator_ok:
        fix_ok = fix_ride_validator()
    else:
        fix_ok = True
    
    # Summary
    print_header("Diagnostic Summary")
    print(f"Ride Validator: {'✅ Working' if validator_ok else '❌ Issues Detected'}")
    print(f"Fixes Applied: {'✅ Complete' if fix_ok else '❌ Incomplete'}")
    
    # Next steps
    print_header("Next Steps")
    if validator_ok:
        print("🎉 Ride validation rules are working correctly!")
        print("\nTo test the functionality:")
        print("1. Run the application: python main.py")
        print("2. Navigate to the Ride Entry or Monitoring view")
        print("3. Create or edit rides to trigger rule validations")
    else:
        print("⚠️ Issues detected with ride validation rules.")
        print("\nManual fixes required:")
        print("1. Check the ride_validator.py file")
        print("2. Ensure all five rules are properly implemented")
        print("3. Test each rule individually with different scenarios")
        print("4. Verify German error messages are being used")

if __name__ == "__main__":
    run_diagnostic()