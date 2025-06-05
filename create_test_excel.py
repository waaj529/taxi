#!/usr/bin/env python3
"""
Excel Test Data Generator for Ride Guardian
Creates comprehensive test data in Excel format for frontend testing
"""

import pandas as pd
import random
from datetime import datetime, timedelta

class ExcelTestDataGenerator:
    def __init__(self):
        # Sample driver data
        self.drivers = [
            {"id": 1, "name": "Max Mueller", "vehicle": "Toyota Camry - ABC-123"},
            {"id": 2, "name": "Anna Schmidt", "vehicle": "Honda Accord - DEF-456"},
            {"id": 3, "name": "Thomas Weber", "vehicle": "Nissan Altima - GHI-789"},
            {"id": 4, "name": "Sarah Johnson", "vehicle": "Ford Fusion - JKL-012"},
            {"id": 5, "name": "Mike Davis", "vehicle": "Chevrolet Malibu - MNO-345"},
            {"id": 6, "name": "Lisa Brown", "vehicle": "Hyundai Sonata - PQR-678"},
            {"id": 7, "name": "Robert Wilson", "vehicle": "Volkswagen Passat - STU-901"},
            {"id": 8, "name": "Emma Taylor", "vehicle": "Mazda 6 - VWX-234"},
        ]
        
        # Diverse locations
        self.locations = [
            "Headquarters, 123 Main St, Downtown",
            "Central Train Station, Station Square 1",
            "City Hospital, 456 Health Ave",
            "Shopping Mall, 789 Commerce Blvd",
            "Airport Terminal, 321 Flight Way",
            "University Campus, 654 Education St",
            "Business District, 987 Corporate Ave",
            "Residential Area North, 147 Oak St",
            "Residential Area South, 258 Pine Ave",
            "Hotel District, 369 Hospitality Rd",
            "Sports Complex, 159 Athletic Way",
            "Park & Recreation, 753 Green Path",
            "Medical Center, 159 Wellness Way",
            "Convention Center, 753 Event Plaza",
            "Industrial Park, 357 Factory Road",
        ]
        
        # Violation types
        self.violation_types = [
            "RULE_1: Shift must start at depot location",
            "RULE_2: Pickup too far from previous location",
            "RULE_3: Route logic violation",
            "RULE_4: Time gap between rides too large",
            "RULE_5: Assignment during active ride",
        ]
        
        # Payment methods and fare types
        self.payment_methods = ["Cash", "Credit Card", "Debit Card", "Mobile Payment", "Corporate Account"]
        self.fare_types = ["Standard", "Premium", "Economy", "Corporate", "Airport"]
        self.ride_statuses = ["Completed", "In Progress", "Cancelled", "Violation"]
    
    def generate_realistic_ride_time(self, date):
        """Generate realistic ride times based on traffic patterns"""
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
    
    def calculate_revenue(self, distance_km, duration_minutes, pickup_time):
        """Calculate realistic revenue based on fare structure"""
        base_fare = random.uniform(3.50, 5.00)
        distance_rate = random.uniform(1.20, 2.00)
        time_rate = random.uniform(0.25, 0.45)
        
        hour = pickup_time.hour
        if hour in [7, 8, 17, 18, 19]:  # Rush hours
            multiplier = random.uniform(1.2, 1.5)
        elif hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Night
            multiplier = random.uniform(1.1, 1.3)
        else:
            multiplier = 1.0
        
        revenue = (base_fare + (distance_km * distance_rate) + (duration_minutes * time_rate)) * multiplier
        return round(revenue, 2)
    
    def calculate_duration(self, distance_km, pickup_time):
        """Calculate realistic duration based on distance and time of day"""
        hour = pickup_time.hour
        
        if hour in [7, 8, 17, 18, 19]:  # Rush hours
            mins_per_km = random.uniform(6, 10)
        elif hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Night
            mins_per_km = random.uniform(2, 4)
        else:  # Regular hours
            mins_per_km = random.uniform(3, 6)
        
        duration = int(distance_km * mins_per_km)
        return max(5, duration)  # Minimum 5 minutes
    
    def determine_ride_outcome(self):
        """Determine ride status and violations"""
        rand = random.random()
        
        if rand < 0.85:  # 85% completed successfully
            return "Completed", ""
        elif rand < 0.92:  # 7% completed with violations
            violations = []
            num_violations = random.randint(1, 2)
            selected_violations = random.sample(self.violation_types, num_violations)
            return "Violation", "; ".join(selected_violations)
        elif rand < 0.97:  # 5% in progress
            return "In Progress", ""
        else:  # 3% cancelled
            return "Cancelled", ""
    
    def generate_rides_data(self, days=30, rides_per_day_range=(25, 45)):
        """Generate comprehensive ride data"""
        print(f"Generating rides data for {days} days...")
        
        rides_data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        ride_id = 1
        
        while current_date <= end_date:
            # Adjust ride volume based on day of week
            is_weekend = current_date.weekday() >= 5
            is_friday = current_date.weekday() == 4
            
            if is_weekend:
                daily_rides = random.randint(15, 25)
            elif is_friday:
                daily_rides = random.randint(35, 50)
            else:
                daily_rides = random.randint(*rides_per_day_range)
            
            for _ in range(daily_rides):
                # Select driver
                driver = random.choice(self.drivers)
                
                # Generate ride time
                pickup_time = self.generate_realistic_ride_time(current_date)
                
                # Select locations
                pickup_location = random.choice(self.locations)
                destination = random.choice([loc for loc in self.locations if loc != pickup_location])
                
                # Calculate metrics
                distance_km = round(random.uniform(2.0, 25.0), 2)
                duration_minutes = self.calculate_duration(distance_km, pickup_time)
                dropoff_time = pickup_time + timedelta(minutes=duration_minutes)
                revenue = self.calculate_revenue(distance_km, duration_minutes, pickup_time)
                
                # Determine outcome
                status, violations = self.determine_ride_outcome()
                
                # Additional details
                passengers = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
                payment_method = random.choice(self.payment_methods)
                fare_type = random.choice(self.fare_types)
                vehicle_plate = driver["vehicle"].split(" - ")[-1] if " - " in driver["vehicle"] else f"TMP-{random.randint(100,999)}"
                
                ride_data = {
                    "ride_id": ride_id,
                    "driver_id": driver["id"],
                    "driver_name": driver["name"],
                    "pickup_time": pickup_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "dropoff_time": dropoff_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "pickup_location": pickup_location,
                    "destination": destination,
                    "distance_km": distance_km,
                    "duration_minutes": duration_minutes,
                    "revenue": revenue,
                    "status": status,
                    "violations": violations,
                    "vehicle_plate": vehicle_plate,
                    "passengers": passengers,
                    "payment_method": payment_method,
                    "fare_type": fare_type,
                    "is_reserved": random.choice([True, False]),
                    "notes": random.choice(["", "Customer requested specific route", "Traffic delay", "Customer was late", ""]),
                }
                
                rides_data.append(ride_data)
                ride_id += 1
            
            current_date += timedelta(days=1)
        
        return rides_data
    
    def generate_drivers_data(self):
        """Generate driver summary data"""
        print("Generating drivers data...")
        
        drivers_data = []
        for driver in self.drivers:
            drivers_data.append({
                "driver_id": driver["id"],
                "name": driver["name"],
                "vehicle": driver["vehicle"],
                "status": random.choice(["Active", "Inactive"]) if random.random() < 0.1 else "Active",
                "total_hours": round(random.uniform(120, 200), 2),
                "total_rides": random.randint(80, 150),
                "total_earnings": round(random.uniform(1500, 2500), 2),
                "violations": random.randint(0, 5),
                "shift": random.choice(["Morning", "Evening", "Night", "Flexible"]),
                "hire_date": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d"),
                "phone": f"+1-555-{random.randint(1000, 9999)}",
                "email": f"{driver['name'].lower().replace(' ', '.')}@email.com",
            })
        
        return drivers_data
    
    def generate_payroll_data(self):
        """Generate payroll data"""
        print("Generating payroll data...")
        
        payroll_data = []
        end_date = datetime.now()
        
        for week in range(4):  # Last 4 weeks
            week_start = end_date - timedelta(weeks=week+1)
            week_end = week_start + timedelta(days=6)
            
            for driver in self.drivers:
                regular_hours = round(random.uniform(35, 40), 2)
                night_hours = round(random.uniform(5, 15), 2)
                weekend_hours = round(random.uniform(8, 16), 2)
                holiday_hours = round(random.uniform(0, 8), 2) if random.random() < 0.2 else 0
                
                total_hours = regular_hours + night_hours + weekend_hours + holiday_hours
                hourly_rate = 12.41
                
                base_pay = round(regular_hours * hourly_rate, 2)
                night_bonus = round(night_hours * hourly_rate * 0.15, 2)
                weekend_bonus = round(weekend_hours * hourly_rate * 0.10, 2)
                holiday_bonus = round(holiday_hours * hourly_rate * 0.25, 2)
                performance_bonus = round(base_pay * 0.05, 2) if random.random() < 0.3 else 0
                
                total_bonuses = night_bonus + weekend_bonus + holiday_bonus + performance_bonus
                total_pay = base_pay + total_bonuses
                
                payroll_data.append({
                    "driver_id": driver["id"],
                    "driver_name": driver["name"],
                    "period_start": week_start.strftime("%Y-%m-%d"),
                    "period_end": week_end.strftime("%Y-%m-%d"),
                    "regular_hours": regular_hours,
                    "night_hours": night_hours,
                    "weekend_hours": weekend_hours,
                    "holiday_hours": holiday_hours,
                    "total_hours": round(total_hours, 2),
                    "hourly_rate": hourly_rate,
                    "base_pay": base_pay,
                    "night_bonus": night_bonus,
                    "weekend_bonus": weekend_bonus,
                    "holiday_bonus": holiday_bonus,
                    "performance_bonus": performance_bonus,
                    "total_bonuses": round(total_bonuses, 2),
                    "total_pay": round(total_pay, 2),
                    "compliance_status": random.choice(["Compliant", "Violation"]) if random.random() < 0.15 else "Compliant",
                })
        
        return payroll_data
    
    def create_excel_file(self, filename="ride_guardian_test_data.xlsx"):
        """Create comprehensive Excel file with multiple sheets"""
        print("Creating Excel file with test data...")
        
        # Generate all data
        rides_data = self.generate_rides_data(days=30)
        drivers_data = self.generate_drivers_data()
        payroll_data = self.generate_payroll_data()
        
        # Create DataFrames
        rides_df = pd.DataFrame(rides_data)
        drivers_df = pd.DataFrame(drivers_data)
        payroll_df = pd.DataFrame(payroll_data)
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Rides data (main sheet for import testing)
            rides_df.to_excel(writer, sheet_name='Rides', index=False)
            
            # Drivers data
            drivers_df.to_excel(writer, sheet_name='Drivers', index=False)
            
            # Payroll data
            payroll_df.to_excel(writer, sheet_name='Payroll', index=False)
            
            # Summary statistics
            summary_data = {
                "Metric": [
                    "Total Rides",
                    "Completed Rides",
                    "Rides with Violations",
                    "Total Revenue",
                    "Average Revenue per Ride",
                    "Total Drivers",
                    "Active Drivers",
                    "Total Payroll Records"
                ],
                "Value": [
                    len(rides_data),
                    len([r for r in rides_data if r["status"] == "Completed"]),
                    len([r for r in rides_data if r["violations"]]),
                    f"${sum(r['revenue'] for r in rides_data):,.2f}",
                    f"${sum(r['revenue'] for r in rides_data) / len(rides_data):,.2f}",
                    len(drivers_data),
                    len([d for d in drivers_data if d["status"] == "Active"]),
                    len(payroll_data)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        return filename, len(rides_data), len(drivers_data), len(payroll_data)

def main():
    """Main function to generate Excel test data"""
    print("🚗 Ride Guardian - Excel Test Data Generator")
    print("=" * 55)
    
    generator = ExcelTestDataGenerator()
    
    try:
        filename, rides_count, drivers_count, payroll_count = generator.create_excel_file()
        
        print(f"\n✅ Excel Test Data Generated Successfully!")
        print("=" * 45)
        print(f"📄 File: {filename}")
        print(f"📊 Sheets Created:")
        print(f"  • Rides: {rides_count} records")
        print(f"  • Drivers: {drivers_count} records") 
        print(f"  • Payroll: {payroll_count} records")
        print(f"  • Summary: Statistics overview")
        
        print(f"\n💡 How to use:")
        print(f"  1. Open the Excel file: {filename}")
        print(f"  2. Use the 'Rides' sheet for main data import testing")
        print(f"  3. Use other sheets for comprehensive testing")
        print(f"  4. Test various scenarios including violations and edge cases")
        
    except Exception as e:
        print(f"❌ Error generating Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

import pandas as pd
import random
from datetime import datetime, timedelta

# Sample data
drivers = ["John Smith", "Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "David Kim"]
vehicles = ["ABC123", "XYZ789", "DEF456", "GHI012", "JKL345"]
locations = [
    "123 Main St, Downtown",
    "456 Oak Ave, Midtown", 
    "789 Pine Rd, Uptown",
    "321 Elm St, Suburbs",
    "654 Maple Dr, Airport"
]

# Generate test data
test_data = []
base_date = datetime.now() - timedelta(days=30)

for i in range(100):
    ride_date = base_date + timedelta(
        days=random.randint(0, 30),
        hours=random.randint(6, 23),
        minutes=random.randint(0, 59)
    )
    
    test_data.append({
        "Driver Name": random.choice(drivers),  # Changed from driver_name
        "Date/Time": ride_date.strftime("%Y-%m-%d %H:%M:%S"),  # Changed from pickup_time
        "Pickup Address": random.choice(locations),  # Changed from pickup_location
        "Destination": random.choice(locations),
        "Vehicle Plate": random.choice(vehicles),  # Changed from vehicle_plate
        "Fare": round(random.uniform(15.0, 75.0), 2),
        "Reserved": random.choice([True, False])
    })

# Create DataFrame and save to Excel
df = pd.DataFrame(test_data)
df.to_excel("ride_guardian_test_data.xlsx", index=False)
print("Test Excel file created: ride_guardian_test_data.xlsx")
print(f"Generated {len(test_data)} test rides")
print(f"Column names: {list(df.columns)}")