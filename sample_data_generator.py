#!/usr/bin/env python3
"""
Comprehensive Sample Data Generator for Ride Guardian
Creates realistic test data for all tables and testing scenarios
"""

import sqlite3
import random
from datetime import datetime, timedelta, time
import json
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from core.database import get_db_connection

class ComprehensiveDataGenerator:
    def __init__(self):
        self.db = get_db_connection()
        self.cursor = self.db.cursor()
        
        # Sample driver data with actual schema fields
        self.drivers = [
            {"name": "Max Mueller", "vehicle": "Toyota Camry - ABC-123"},
            {"name": "Anna Schmidt", "vehicle": "Honda Accord - DEF-456"},
            {"name": "Thomas Weber", "vehicle": "Nissan Altima - GHI-789"},
            {"name": "Sarah Johnson", "vehicle": "Ford Fusion - JKL-012"},
            {"name": "Mike Davis", "vehicle": "Chevrolet Malibu - MNO-345"},
            {"name": "Lisa Brown", "vehicle": "Hyundai Sonata - PQR-678"},
            {"name": "Robert Wilson", "vehicle": "Volkswagen Passat - STU-901"},
            {"name": "Emma Taylor", "vehicle": "Mazda 6 - VWX-234"},
        ]
        
        # Sample vehicle data
        self.vehicles = [
            {"plate": "ABC-123", "make": "Toyota", "model": "Camry", "year": 2022, "color": "Silver"},
            {"plate": "DEF-456", "make": "Honda", "model": "Accord", "year": 2021, "color": "Black"},
            {"plate": "GHI-789", "make": "Nissan", "model": "Altima", "year": 2023, "color": "White"},
            {"plate": "JKL-012", "make": "Ford", "model": "Fusion", "year": 2020, "color": "Blue"},
            {"plate": "MNO-345", "make": "Chevrolet", "model": "Malibu", "year": 2022, "color": "Red"},
            {"plate": "PQR-678", "make": "Hyundai", "model": "Sonata", "year": 2021, "color": "Gray"},
            {"plate": "STU-901", "make": "Volkswagen", "model": "Passat", "year": 2023, "color": "Green"},
            {"plate": "VWX-234", "make": "Mazda", "model": "6", "year": 2022, "color": "Orange"},
        ]
        
        # Diverse locations across different areas
        self.locations = [
            {"address": "Headquarters, 123 Main St, Downtown", "lat": 40.7128, "lng": -74.0060, "zone": "downtown"},
            {"address": "Central Train Station, Station Square 1", "lat": 40.7505, "lng": -73.9934, "zone": "transport"},
            {"address": "City Hospital, 456 Health Ave", "lat": 40.7831, "lng": -73.9712, "zone": "medical"},
            {"address": "Shopping Mall, 789 Commerce Blvd", "lat": 40.7589, "lng": -73.9851, "zone": "retail"},
            {"address": "Airport Terminal, 321 Flight Way", "lat": 40.6892, "lng": -74.1745, "zone": "airport"},
            {"address": "University Campus, 654 Education St", "lat": 40.7282, "lng": -74.0776, "zone": "education"},
            {"address": "Business District, 987 Corporate Ave", "lat": 40.7614, "lng": -73.9776, "zone": "business"},
            {"address": "Residential Area North, 147 Oak St", "lat": 40.7749, "lng": -73.9442, "zone": "residential"},
            {"address": "Residential Area South, 258 Pine Ave", "lat": 40.6968, "lng": -74.0124, "zone": "residential"},
            {"address": "Hotel District, 369 Hospitality Rd", "lat": 40.7549, "lng": -73.9840, "zone": "hotel"},
            {"address": "Sports Complex, 159 Athletic Way", "lat": 40.7061, "lng": -74.0087, "zone": "sports"},
            {"address": "Park & Recreation, 753 Green Path", "lat": 40.7359, "lng": -73.9911, "zone": "recreation"},
        ]
        
        # Violation scenarios for testing
        self.violation_scenarios = [
            {"type": "RULE_1", "description": "Shift must start at depot location", "probability": 0.05},
            {"type": "RULE_2", "description": "Pickup too far from previous location", "probability": 0.08},
            {"type": "RULE_3", "description": "Route logic violation", "probability": 0.06},
            {"type": "RULE_4", "description": "Time gap between rides too large", "probability": 0.04},
            {"type": "RULE_5", "description": "Assignment during active ride", "probability": 0.03},
        ]
        
        # Payment methods
        self.payment_methods = ["Cash", "Credit Card", "Debit Card", "Mobile Payment", "Corporate Account"]
        
        # Fare types
        self.fare_types = ["Standard", "Premium", "Economy", "Corporate", "Airport"]
    
    def clear_existing_data(self):
        """Clear existing test data (optional)"""
        tables = ['payroll', 'shifts', 'rides', 'vehicles', 'drivers']
        for table in tables:
            try:
                self.cursor.execute(f"DELETE FROM {table}")
            except Exception as e:
                print(f"Note: Could not clear {table} (may not exist): {e}")
        self.db.commit()
        print("Cleared existing test data")
    
    def create_drivers(self):
        """Create comprehensive driver data with actual schema"""
        print("Creating drivers with available fields...")
        
        driver_ids = []
        
        for driver in self.drivers:
            try:
                status = "Active" if random.random() < 0.9 else "Inactive"
                
                # Calculate realistic stats for this driver
                total_hours = round(random.uniform(120, 200), 2)  # Monthly hours
                total_rides = random.randint(80, 150)  # Monthly rides
                total_earnings = round(random.uniform(1500, 2500), 2)  # Monthly earnings
                violations = random.randint(0, 5)  # Violation count
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO drivers (
                        name, vehicle, status, total_hours, total_rides, total_earnings, violations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    driver["name"], driver["vehicle"], status, 
                    total_hours, total_rides, total_earnings, violations
                ))
                
                driver_ids.append(self.cursor.lastrowid)
                
            except Exception as e:
                print(f"Error creating driver {driver['name']}: {e}")
        
        self.db.commit()
        print(f"Created {len(self.drivers)} drivers")
        return driver_ids
    
    def create_vehicles(self, driver_ids):
        """Create vehicle data if vehicles table exists"""
        print("Creating vehicles...")
        
        # Check if vehicles table exists
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if not self.cursor.fetchone():
                print("Vehicles table does not exist, skipping vehicle creation")
                return []
        except Exception as e:
            print(f"Could not check for vehicles table: {e}")
            return []
        
        vehicle_ids = []
        for i, vehicle in enumerate(self.vehicles):
            try:
                current_driver_id = driver_ids[i] if i < len(driver_ids) else None
                status = random.choice(["Available", "In Use"]) if random.random() < 0.2 else "Available"
                total_km = random.randint(15000, 85000)
                
                # Generate maintenance dates
                last_maintenance = datetime.now() - timedelta(days=random.randint(30, 180))
                next_maintenance_km = total_km + random.randint(5000, 15000)
                
                # Generate expiry dates
                insurance_expiry = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
                registration_expiry = (datetime.now() + timedelta(days=random.randint(60, 730))).strftime("%Y-%m-%d")
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO vehicles (
                        plate_number, make, model, year, color, status, current_driver_id,
                        total_km, last_maintenance_date, next_maintenance_km,
                        insurance_expiry, registration_expiry
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle["plate"], vehicle["make"], vehicle["model"], vehicle["year"],
                    vehicle["color"], status, current_driver_id, total_km,
                    last_maintenance.strftime("%Y-%m-%d"), next_maintenance_km,
                    insurance_expiry, registration_expiry
                ))
                
                vehicle_ids.append(self.cursor.lastrowid)
                
            except Exception as e:
                print(f"Error creating vehicle {vehicle['plate']}: {e}")
        
        self.db.commit()
        print(f"Created {len(vehicle_ids)} vehicles")
        return vehicle_ids
    
    def generate_shifts(self, driver_ids, days=30):
        """Generate realistic shift data if shifts table exists"""
        print(f"Generating shifts for {days} days...")
        
        # Check if shifts table exists
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shifts'")
            if not self.cursor.fetchone():
                print("Shifts table does not exist, skipping shift generation")
                return
        except Exception as e:
            print(f"Could not check for shifts table: {e}")
            return
        
        if not driver_ids:
            print("No drivers available for shift generation")
            return
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            # Ensure we don't try to sample more drivers than available
            max_working_drivers = min(len(driver_ids), random.randint(3, 6))
            working_drivers = random.sample(driver_ids, max_working_drivers)
            
            for driver_id in working_drivers:
                # Skip some days randomly
                if random.random() < 0.15:  # 15% chance to skip a day
                    continue
                
                # Generate shift times
                shift_start_hour = random.choice([6, 7, 8, 14, 15, 16])  # Morning or afternoon shifts
                shift_duration = random.randint(6, 10)  # 6-10 hour shifts
                
                start_time = current_date.replace(hour=shift_start_hour, minute=random.randint(0, 30))
                end_time = start_time + timedelta(hours=shift_duration)
                
                # If end time goes to next day, cap it
                if end_time.date() > current_date.date():
                    end_time = current_date.replace(hour=23, minute=59)
                
                try:
                    self.cursor.execute("""
                        INSERT INTO shifts (
                            driver_id, shift_date, start_time, end_time,
                            start_location, end_location, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        driver_id,
                        current_date.strftime("%Y-%m-%d"),
                        start_time.strftime("%H:%M:%S"),
                        end_time.strftime("%H:%M:%S"),
                        "Headquarters",
                        random.choice(self.locations)["address"] if random.random() < 0.3 else "Headquarters",
                        "Completed"
                    ))
                    
                except Exception as e:
                    print(f"Error creating shift: {e}")
            
            current_date += timedelta(days=1)
        
        self.db.commit()
        print("Shifts generated successfully")
    
    def generate_rides(self, driver_ids, days=30):
        """Generate comprehensive ride data with realistic patterns"""
        print(f"Generating rides for {days} days...")
        
        if not driver_ids:
            print("No drivers available for ride generation")
            return
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        total_rides = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Adjust ride volume based on day of week
            is_weekend = current_date.weekday() >= 5
            is_friday = current_date.weekday() == 4
            
            if is_weekend:
                base_rides = random.randint(15, 25)
            elif is_friday:
                base_rides = random.randint(35, 50)
            else:
                base_rides = random.randint(25, 40)
            
            # Generate rides for the day
            daily_rides = self.generate_daily_rides(current_date, driver_ids, base_rides)
            total_rides += daily_rides
            
            current_date += timedelta(days=1)
        
        self.db.commit()
        print(f"Generated {total_rides} rides with realistic patterns")
    
    def generate_daily_rides(self, date, driver_ids, target_rides):
        """Generate rides for a specific day with realistic timing"""
        rides_created = 0
        
        # Get available drivers for this day (80% chance each driver works)
        available_drivers = [d for d in driver_ids if random.random() < 0.8]
        
        if not available_drivers:
            return 0
        
        for _ in range(target_rides):
            driver_id = random.choice(available_drivers)
            
            # Generate realistic ride timing
            ride_time = self.generate_realistic_ride_time(date)
            
            # Create the ride
            if self.create_single_ride(driver_id, ride_time):
                rides_created += 1
        
        return rides_created
    
    def generate_realistic_ride_time(self, date):
        """Generate realistic ride times based on traffic patterns"""
        # Define hourly weights for ride probability
        hourly_weights = {
            5: 0.1, 6: 0.5, 7: 1.8, 8: 2.5, 9: 2.0, 10: 1.2, 11: 1.3, 12: 1.6,
            13: 1.4, 14: 1.1, 15: 1.3, 16: 1.7, 17: 2.3, 18: 2.1, 19: 1.8,
            20: 1.2, 21: 0.9, 22: 0.6, 23: 0.4, 0: 0.2, 1: 0.1, 2: 0.1,
            3: 0.1, 4: 0.1
        }
        
        hour = random.choices(list(hourly_weights.keys()), weights=list(hourly_weights.values()))[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return date.replace(hour=hour, minute=minute, second=second)
    
    def create_single_ride(self, driver_id, pickup_time):
        """Create a single realistic ride with all details"""
        try:
            # Select locations
            pickup_location = random.choice(self.locations)
            destination = random.choice([loc for loc in self.locations if loc != pickup_location])
            
            # Calculate realistic metrics
            distance_km = self.calculate_distance(pickup_location, destination)
            duration_minutes = self.calculate_duration(distance_km, pickup_time)
            dropoff_time = pickup_time + timedelta(minutes=duration_minutes)
            
            # Calculate revenue
            revenue = self.calculate_revenue(distance_km, duration_minutes, pickup_time)
            
            # Determine ride status and violations
            status, violations = self.determine_ride_outcome()
            
            # Get vehicle info
            vehicle_plate = self.get_driver_vehicle_plate(driver_id)
            
            # Additional ride details
            passengers = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
            is_reserved = random.random() < 0.15  # 15% reserved rides
            payment_method = random.choice(self.payment_methods)
            fare_type = random.choice(self.fare_types)
            
            # Check what columns exist in rides table
            self.cursor.execute("PRAGMA table_info(rides)")
            columns = [row[1] for row in self.cursor.fetchall()]
            
            # Build insert query based on available columns
            base_columns = ['driver_id', 'pickup_time', 'pickup_location', 'destination', 'status', 'revenue']
            base_values = [driver_id, pickup_time.isoformat(), pickup_location["address"], 
                          destination["address"], status, revenue]
            
            # Add optional columns if they exist
            optional_fields = {
                'dropoff_time': dropoff_time.isoformat(),
                'distance_km': distance_km,
                'duration_minutes': duration_minutes,
                'violations': json.dumps(violations),
                'vehicle_plate': vehicle_plate,
                'passengers': passengers,
                'is_reserved': is_reserved,
                'payment_method': payment_method,
                'fare_type': fare_type
            }
            
            for col, val in optional_fields.items():
                if col in columns:
                    base_columns.append(col)
                    base_values.append(val)
            
            placeholders = ', '.join(['?' for _ in base_columns])
            columns_str = ', '.join(base_columns)
            
            self.cursor.execute(f"""
                INSERT INTO rides ({columns_str}) VALUES ({placeholders})
            """, base_values)
            
            return True
            
        except Exception as e:
            print(f"Error creating ride: {e}")
            return False
    
    def calculate_distance(self, pickup, destination):
        """Calculate realistic distance between locations"""
        # Simplified distance calculation based on zones
        if pickup["zone"] == destination["zone"]:
            return round(random.uniform(1.5, 4.0), 2)  # Same zone
        elif pickup["zone"] == "airport" or destination["zone"] == "airport":
            return round(random.uniform(15.0, 35.0), 2)  # Airport rides
        else:
            return round(random.uniform(3.0, 18.0), 2)  # Cross-zone
    
    def calculate_duration(self, distance_km, pickup_time):
        """Calculate realistic duration based on distance and time of day"""
        # Base duration: 3-8 minutes per km depending on traffic
        hour = pickup_time.hour
        
        if hour in [7, 8, 17, 18, 19]:  # Rush hours
            mins_per_km = random.uniform(6, 10)
        elif hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Night
            mins_per_km = random.uniform(2, 4)
        else:  # Regular hours
            mins_per_km = random.uniform(3, 6)
        
        duration = int(distance_km * mins_per_km)
        return max(5, duration)  # Minimum 5 minutes
    
    def calculate_revenue(self, distance_km, duration_minutes, pickup_time):
        """Calculate realistic revenue based on fare structure"""
        # Base fare
        base_fare = random.uniform(3.50, 5.00)
        
        # Distance rate
        distance_rate = random.uniform(1.20, 2.00)
        
        # Time rate
        time_rate = random.uniform(0.25, 0.45)
        
        # Peak hour multiplier
        hour = pickup_time.hour
        if hour in [7, 8, 17, 18, 19]:  # Rush hours
            multiplier = random.uniform(1.2, 1.5)
        elif hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Night
            multiplier = random.uniform(1.1, 1.3)
        else:
            multiplier = 1.0
        
        revenue = (base_fare + (distance_km * distance_rate) + (duration_minutes * time_rate)) * multiplier
        return round(revenue, 2)
    
    def determine_ride_outcome(self):
        """Determine ride status and violations"""
        rand = random.random()
        
        if rand < 0.85:  # 85% completed successfully
            return "Completed", []
        elif rand < 0.92:  # 7% completed with violations
            violations = []
            for scenario in self.violation_scenarios:
                if random.random() < scenario["probability"]:
                    violations.append(scenario["type"] + ": " + scenario["description"])
            return "Completed", violations
        elif rand < 0.97:  # 5% in progress
            return "In Progress", []
        else:  # 3% cancelled
            return "Cancelled", []
    
    def get_driver_vehicle_plate(self, driver_id):
        """Get vehicle plate for driver from driver record"""
        try:
            self.cursor.execute("SELECT vehicle FROM drivers WHERE id = ?", (driver_id,))
            result = self.cursor.fetchone()
            if result and result['vehicle']:
                # Extract plate from "Make Model - PLATE" format
                vehicle_info = result['vehicle']
                if ' - ' in vehicle_info:
                    return vehicle_info.split(' - ')[-1]
                else:
                    return f"TMP-{random.randint(100,999)}"
            return f"TMP-{random.randint(100,999)}"
        except Exception as e:
            return f"TMP-{random.randint(100,999)}"
    
    def generate_payroll_data(self, driver_ids, weeks=4):
        """Generate realistic payroll data if payroll table exists"""
        print(f"Generating payroll data for {weeks} weeks...")
        
        # Check if payroll table exists
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payroll'")
            if not self.cursor.fetchone():
                print("Payroll table does not exist, skipping payroll generation")
                return
        except Exception as e:
            print(f"Could not check for payroll table: {e}")
            return
        
        if not driver_ids:
            print("No drivers available for payroll generation")
            return
        
        end_date = datetime.now()
        
        for week in range(weeks):
            week_start = end_date - timedelta(weeks=week+1)
            week_end = week_start + timedelta(days=6)
            
            for driver_id in driver_ids:
                # Skip some drivers occasionally
                if random.random() < 0.1:
                    continue
                
                # Calculate hours worked
                regular_hours = random.uniform(35, 40)
                night_hours = random.uniform(5, 15)
                weekend_hours = random.uniform(8, 16)
                holiday_hours = random.uniform(0, 8) if random.random() < 0.2 else 0
                
                total_hours = regular_hours + night_hours + weekend_hours + holiday_hours
                
                # Use a standard hourly rate
                hourly_rate = 12.41
                
                # Calculate pay components
                base_pay = regular_hours * hourly_rate
                night_bonus = night_hours * hourly_rate * 0.15
                weekend_bonus = weekend_hours * hourly_rate * 0.10
                holiday_bonus = holiday_hours * hourly_rate * 0.25
                performance_bonus = base_pay * 0.05 if random.random() < 0.3 else 0
                
                total_bonuses = night_bonus + weekend_bonus + holiday_bonus + performance_bonus
                total_pay = base_pay + total_bonuses
                
                # Compliance check
                compliance_status = "Compliant" if random.random() < 0.85 else "Violation"
                minimum_wage_check = total_pay / total_hours if total_hours > 0 else 0
                
                try:
                    self.cursor.execute("""
                        INSERT INTO payroll (
                            driver_id, period_start_date, period_end_date,
                            regular_hours, night_hours, weekend_hours, holiday_hours, total_hours,
                            base_pay, night_bonus, weekend_bonus, holiday_bonus, performance_bonus,
                            total_bonuses, total_pay, compliance_status, minimum_wage_check
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        driver_id, week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"),
                        round(regular_hours, 2), round(night_hours, 2), round(weekend_hours, 2),
                        round(holiday_hours, 2), round(total_hours, 2),
                        round(base_pay, 2), round(night_bonus, 2), round(weekend_bonus, 2),
                        round(holiday_bonus, 2), round(performance_bonus, 2),
                        round(total_bonuses, 2), round(total_pay, 2),
                        compliance_status, round(minimum_wage_check, 2)
                    ))
                    
                except Exception as e:
                    print(f"Error creating payroll record: {e}")
        
        self.db.commit()
        print("Payroll data generated successfully")
    
    def generate_complete_dataset(self, days=30):
        """Generate complete test dataset"""
        print("🚗 Generating Comprehensive Test Data")
        print("=" * 50)
        
        # Create base data
        driver_ids = self.create_drivers()
        vehicle_ids = self.create_vehicles(driver_ids)
        
        # Generate operational data
        self.generate_shifts(driver_ids, days)
        self.generate_rides(driver_ids, days)
        self.generate_payroll_data(driver_ids, weeks=days//7)
        
        return driver_ids, vehicle_ids
    
    def print_summary(self):
        """Print comprehensive data summary"""
        print("\n✅ Comprehensive Test Data Generation Complete!")
        print("=" * 50)
        
        # Get counts for existing tables
        tables_to_check = [
            ("drivers", "Drivers"),
            ("vehicles", "Vehicles"),
            ("rides", "Total Rides"),
            ("shifts", "Shifts"),
            ("payroll", "Payroll Records")
        ]
        
        for table, label in tables_to_check:
            try:
                self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = self.cursor.fetchone()['count']
                print(f"📊 {label}: {count}")
            except Exception:
                print(f"📊 {label}: Table not found")
        
        # Revenue summary
        try:
            self.cursor.execute("""
                SELECT 
                    SUM(revenue) as total_revenue,
                    AVG(revenue) as avg_revenue,
                    COUNT(*) as completed_rides
                FROM rides WHERE status = 'Completed'
            """)
            revenue_data = self.cursor.fetchone()
            
            if revenue_data and revenue_data['total_revenue']:
                print(f"💰 Total Revenue: ${revenue_data['total_revenue']:.2f}")
                print(f"💰 Average Ride: ${revenue_data['avg_revenue']:.2f}")
                print(f"🚖 Completed Rides: {revenue_data['completed_rides']}")
        except Exception as e:
            print(f"💰 Revenue data: Could not calculate ({e})")
        
        # Violation summary
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as violation_count 
                FROM rides 
                WHERE violations != '[]' AND violations IS NOT NULL AND violations != ''
            """)
            violations = self.cursor.fetchone()['violation_count']
            print(f"⚠️  Rides with Violations: {violations}")
        except Exception:
            print(f"⚠️  Rides with Violations: Could not calculate")
        
        print(f"\n💡 Test data spans the last 30 days")
        print(f"🔍 Ready for comprehensive testing of all features!")
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

def main():
    """Main function to generate comprehensive test data"""
    print("🚗 Ride Guardian - Comprehensive Test Data Generator")
    print("=" * 60)
    
    generator = ComprehensiveDataGenerator()
    
    try:
        # Check existing data
        generator.cursor.execute("SELECT COUNT(*) as count FROM rides")
        existing_rides = generator.cursor.fetchone()['count']
        
        if existing_rides > 0:
            print(f"\n⚠️  Found {existing_rides} existing rides in database.")
            response = input("Clear existing data and generate fresh dataset? (y/N): ")
            if response.lower() == 'y':
                generator.clear_existing_data()
                print("✅ Existing data cleared.")
            else:
                response = input("Add to existing data? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled.")
                    return
        
        # Generate data
        print("\n🔄 Generating comprehensive test dataset...")
        generator.generate_complete_dataset(days=30)
        
        # Show summary
        generator.print_summary()
        
    except Exception as e:
        print(f"❌ Error generating test data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.close()

if __name__ == "__main__":
    main()