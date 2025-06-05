#!/usr/bin/env python3
"""
German Labor Law Violation System Demo
Demonstrates the comprehensive violation detection system for German driving services
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import json
from core.database import initialize_database, get_db_connection
from core.labor_law_validator import GermanLaborLawValidator
from core.enhanced_ride_validator import EnhancedRideValidator

def create_demo_data():
    """Create demo data to test the violation system"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Creating demo data for violation testing...")
    
    # Create demo drivers
    demo_drivers = [
        ("Max Mustermann", "12345", "Active"),
        ("Anna Schmidt", "67890", "Active"),
        ("Hans Mueller", "11111", "Active")
    ]
    
    for name, license_num, status in demo_drivers:
        cursor.execute("""
            INSERT OR IGNORE INTO drivers (company_id, name, license_number, status, hourly_rate)
            VALUES (1, ?, ?, ?, 12.41)
        """, (name, license_num, status))
    
    # Get driver IDs
    cursor.execute("SELECT id, name FROM drivers WHERE company_id = 1")
    drivers = cursor.fetchall()
    
    # Create shifts with various violation scenarios
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Scenario 1: Max Mustermann - Excessive shift duration (12 hours)
    cursor.execute("""
        INSERT OR IGNORE INTO shifts 
        (company_id, driver_id, shift_date, start_time, end_time, status, pause_min)
        VALUES (1, ?, ?, '08:00', '20:00', 'Active', 20)
    """, (drivers[0]['id'], today.isoformat()))
    
    # Scenario 2: Anna Schmidt - Insufficient break for 8-hour shift
    cursor.execute("""
        INSERT OR IGNORE INTO shifts 
        (company_id, driver_id, shift_date, start_time, end_time, status, pause_min)
        VALUES (1, ?, ?, '09:00', '17:00', 'Active', 10)
    """, (drivers[1]['id'], today.isoformat()))
    
    # Scenario 3: Hans Mueller - Insufficient rest period (worked yesterday until 23:00, starts today at 08:00)
    cursor.execute("""
        INSERT OR IGNORE INTO shifts 
        (company_id, driver_id, shift_date, start_time, end_time, status, pause_min)
        VALUES (1, ?, ?, '06:00', '23:00', 'Completed', 45)
    """, (drivers[2]['id'], yesterday.isoformat()))
    
    cursor.execute("""
        INSERT OR IGNORE INTO shifts 
        (company_id, driver_id, shift_date, start_time, end_time, status, pause_min)
        VALUES (1, ?, ?, '08:00', '16:00', 'Active', 30)
    """, (drivers[2]['id'], today.isoformat()))
    
    # Create some rides for break analysis
    shift_ids = []
    cursor.execute("SELECT id, driver_id FROM shifts WHERE shift_date = ?", (today.isoformat(),))
    for shift in cursor.fetchall():
        shift_ids.append((shift['id'], shift['driver_id']))
    
    # Add rides for Max (long shift with insufficient breaks)
    ride_times = [
        ("08:30", "09:15"),
        ("09:20", "10:05"),
        ("10:10", "10:55"), # Only 5-minute breaks
        ("11:00", "11:45"),
        ("11:50", "12:35"),
        ("12:40", "13:25"),
        ("13:30", "14:15"),
        ("14:20", "15:05"),
        ("15:10", "15:55"),
        ("16:00", "16:45"),
        ("16:50", "17:35"),
        ("17:40", "18:25"),
        ("18:30", "19:15"),
        ("19:20", "19:50")
    ]
    
    for i, (pickup, dropoff) in enumerate(ride_times):
        cursor.execute("""
            INSERT OR IGNORE INTO rides 
            (company_id, driver_id, shift_id, pickup_time, dropoff_time, 
             pickup_location, destination, distance_km, status)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, 'Completed')
        """, (
            drivers[0]['id'], 
            shift_ids[0][0], 
            f"{today} {pickup}:00",
            f"{today} {dropoff}:00",
            f"Pickup Location {i+1}",
            f"Destination {i+1}",
            5.5,
        ))
    
    conn.commit()
    conn.close()
    print("Demo data created successfully!")

def demonstrate_violation_detection():
    """Demonstrate the violation detection system"""
    print("\n" + "="*60)
    print("GERMAN LABOR LAW VIOLATION DETECTION DEMO")
    print("="*60)
    
    # Initialize validators
    labor_validator = GermanLaborLawValidator()
    enhanced_validator = EnhancedRideValidator()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all active shifts for today
    today = datetime.now().date()
    cursor.execute("""
        SELECT s.id, s.driver_id, d.name, s.shift_date, s.start_time, s.end_time, s.pause_min
        FROM shifts s
        JOIN drivers d ON s.driver_id = d.id
        WHERE s.shift_date = ? AND s.status = 'Active'
    """, (today.isoformat(),))
    
    shifts = cursor.fetchall()
    
    print(f"\nAnalyzing {len(shifts)} active shifts for today ({today}):")
    
    all_violations = []
    
    for shift in shifts:
        print(f"\n--- Fahrer: {shift['name']} ---")
        print(f"Schicht: {shift['start_time']} - {shift['end_time']}")
        print(f"Geplante Pausenzeit: {shift['pause_min']} Minuten")
        
        # Validate shift compliance
        violations = labor_validator.validate_shift_compliance(shift['id'])
        
        if violations:
            print(f"🔴 {len(violations)} Verstöße gefunden:")
            for violation in violations:
                print(f"  • {violation.severity.upper()}: {violation.message}")
                
                # Store violation in database
                violation_id = labor_validator.store_violation(violation)
                all_violations.append(violation)
        else:
            print("✅ Keine Verstöße gefunden")
    
    # Weekly compliance check
    print(f"\n--- WÖCHENTLICHE COMPLIANCE ANALYSE ---")
    
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    
    cursor.execute("SELECT DISTINCT driver_id FROM shifts WHERE shift_date >= ?", 
                   (week_start.date().isoformat(),))
    
    for driver_row in cursor.fetchall():
        driver_id = driver_row['driver_id']
        weekly_violations = labor_validator.validate_driver_weekly_compliance(driver_id, week_start)
        
        if weekly_violations:
            cursor.execute("SELECT name FROM drivers WHERE id = ?", (driver_id,))
            driver_name = cursor.fetchone()['name']
            
            print(f"\n{driver_name} - Wöchentliche Verstöße:")
            for violation in weekly_violations:
                print(f"  • {violation.severity.upper()}: {violation.message}")
                all_violations.append(violation)
    
    # Generate compliance report
    print(f"\n--- COMPLIANCE BERICHT ---")
    
    report = enhanced_validator.generate_compliance_report(period_days=7)
    
    print(f"Berichtszeitraum: {report['report_period']['days']} Tage")
    print(f"Gesamtfahrten: {report['overall_stats']['total_rides']}")
    print(f"Verstöße: {report['overall_stats']['violation_rides']}")
    print(f"Compliance Rate: {report['overall_stats']['compliance_rate']}%")
    
    if report['labor_law_violations']:
        print(f"\nArbeitszeitrechtsverstöße:")
        for violation in report['labor_law_violations']:
            print(f"  • {violation['type']} ({violation['severity']}): {violation['count']}x")
    
    if report['recommendations']:
        print(f"\nEmpfehlungen:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Summary
    print(f"\n--- ZUSAMMENFASSUNG ---")
    print(f"Gesamtverstöße gefunden: {len(all_violations)}")
    
    severity_counts = {}
    for violation in all_violations:
        severity_counts[violation.severity] = severity_counts.get(violation.severity, 0) + 1
    
    for severity, count in severity_counts.items():
        emoji = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
        print(f"{emoji} {severity.capitalize()}: {count}")
    
    conn.close()
    
    return all_violations

def demonstrate_real_time_monitoring():
    """Demonstrate real-time monitoring capabilities"""
    print(f"\n--- ECHTZEIT-MONITORING DEMO ---")
    
    enhanced_validator = EnhancedRideValidator()
    
    # Simulate a new ride being added that might cause violations
    new_ride_data = {
        'driver_id': 1,
        'pickup_time': datetime.now().isoformat(),
        'pickup_location': 'Test Location',
        'destination': 'Test Destination',
        'is_reserved': False
    }
    
    print("Simuliere neue Fahrt...")
    print(f"Fahrer ID: {new_ride_data['driver_id']}")
    print(f"Abholzeit: {new_ride_data['pickup_time']}")
    
    # Validate the ride
    violations = enhanced_validator.validate_ride_comprehensive(new_ride_data)
    
    if violations:
        print("🔴 Verstöße bei neuer Fahrt erkannt:")
        for violation_type, message in violations.items():
            if isinstance(message, str):
                print(f"  • {violation_type}: {message}")
            elif isinstance(message, list):
                for item in message:
                    if isinstance(item, dict):
                        print(f"  • {item.get('type', violation_type)}: {item.get('message', 'Unbekannter Verstoß')}")
    else:
        print("✅ Keine Verstöße bei neuer Fahrt")

def main():
    """Main demonstration function"""
    print("Initializing German Labor Law Violation System...")
    
    # Initialize database and create tables
    initialize_database()
    
    # Create demo data
    create_demo_data()
    
    # Demonstrate violation detection
    violations = demonstrate_violation_detection()
    
    # Demonstrate real-time monitoring
    demonstrate_real_time_monitoring()
    
    print(f"\n" + "="*60)
    print("DEMO ABGESCHLOSSEN")
    print("="*60)
    print(f"Das System hat erfolgreich {len(violations)} Verstöße erkannt.")
    print("Die Verstöße wurden in der Datenbank gespeichert und können")
    print("über die UI-Komponenten angezeigt und verwaltet werden.")
    print("\nDas System überwacht kontinuierlich:")
    print("• Maximale Schichtdauer (10 Stunden)")
    print("• Pausenzeiten (30 Min für 6-9h, 45 Min für 9h+)")
    print("• Pausenintervalle (mindestens 15 Min pro Pause)")
    print("• Tagesruhezeiten (mindestens 11 Stunden)")
    print("• Wöchentliche Arbeitszeit (maximal 60 Stunden)")
    print("• Kontinuierliche Arbeitszeit (maximal 6 Stunden ohne Pause)")

if __name__ == "__main__":
    main()