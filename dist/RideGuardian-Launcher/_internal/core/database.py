import sqlite3
import os

DATABASE_NAME = "ride_guardian.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', DATABASE_NAME) # Place DB in the main app directory

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Companies Table for multi-company support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            address TEXT,
            headquarters_address TEXT DEFAULT 'Headquarters, Main Street 1, City',
            phone TEXT,
            email TEXT,
            tax_number TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );
    """)

    # Address Cache Table for Google Maps API optimization
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS address_cache (
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

    # Enhanced Drivers Table with company reference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            vehicle TEXT,
            status TEXT DEFAULT 'Active', -- e.g., Active, Inactive
            hourly_rate REAL DEFAULT 12.41,
            bonus_multiplier REAL DEFAULT 1.0,
            hire_date TEXT DEFAULT CURRENT_TIMESTAMP,
            license_number TEXT,
            phone TEXT,
            email TEXT,
            personalnummer TEXT,
            UNIQUE(company_id, name),
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
    """)

    # Enhanced Vehicles Table with company reference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            plate_number TEXT NOT NULL,
            make TEXT,
            model TEXT,
            year INTEGER,
            color TEXT,
            status TEXT DEFAULT 'Available', -- Available, In Use, Maintenance
            current_driver_id INTEGER,
            total_km REAL DEFAULT 0,
            last_maintenance_date TEXT,
            next_maintenance_km REAL,
            insurance_expiry TEXT,
            registration_expiry TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, plate_number),
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (current_driver_id) REFERENCES drivers (id)
        );
    """)

    # Enhanced Rides Table with company reference and German logbook fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            driver_id INTEGER,
            shift_id INTEGER,
            fahrtenbuch_nummer TEXT, -- German: Logbook number
            pickup_time TEXT NOT NULL, -- ISO 8601 format recommended (YYYY-MM-DD HH:MM:SS)
            dropoff_time TEXT, -- When ride was completed
            pickup_location TEXT,
            destination TEXT,
            standort_auftragsuebermittlung TEXT, -- Location where job was received
            abholort TEXT, -- Pickup location (German)
            zielort TEXT, -- Destination (German)
            gefahrene_kilometer REAL, -- Distance driven
            verbrauch_liter REAL, -- Fuel consumption in liters
            kosten_euro REAL, -- Costs in Euro
            reisezweck TEXT, -- Purpose of trip
            status TEXT DEFAULT 'Pending', -- e.g., Pending, In Progress, Completed, Violation
            violations TEXT, -- Store JSON array of rule violations
            revenue REAL,
            distance_km REAL, -- Actual distance traveled
            duration_minutes REAL, -- Actual ride duration
            vehicle_plate TEXT,
            passengers INTEGER DEFAULT 1,
            is_reserved BOOLEAN DEFAULT 0, -- Reserved rides exempt from pickup distance rule
            assigned_during_ride BOOLEAN DEFAULT 0, -- For Rule 5 validation
            current_route_destination TEXT, -- For route logic validation
            fare_type TEXT DEFAULT 'Standard', -- Standard, Premium, etc.
            payment_method TEXT, -- Cash, Card, etc.
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (driver_id) REFERENCES drivers (id),
            FOREIGN KEY (shift_id) REFERENCES shifts (id)
        );
    """)

    # Rules Table - Enhanced with categories and validation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            rule_name TEXT NOT NULL, -- e.g., 'max_pickup_distance_minutes'
            rule_value TEXT, -- Store value as text, parse as needed
            rule_type TEXT DEFAULT 'distance', -- distance, time, bonus, pay
            description TEXT,
            enabled INTEGER DEFAULT 1, -- 1 for true, 0 for false
            driver_specific INTEGER DEFAULT 0, -- Can be overridden per driver
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, rule_name),
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
    """)

    # Payroll Table - Enhanced with company reference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            driver_id INTEGER,
            period_start_date TEXT NOT NULL,
            period_end_date TEXT NOT NULL,
            regular_hours REAL DEFAULT 0,
            night_hours REAL DEFAULT 0,
            weekend_hours REAL DEFAULT 0,
            holiday_hours REAL DEFAULT 0,
            total_hours REAL DEFAULT 0,
            base_pay REAL DEFAULT 0,
            night_bonus REAL DEFAULT 0,
            weekend_bonus REAL DEFAULT 0,
            holiday_bonus REAL DEFAULT 0,
            performance_bonus REAL DEFAULT 0,
            total_bonuses REAL DEFAULT 0,
            total_pay REAL DEFAULT 0,
            compliance_status TEXT DEFAULT 'Pending', -- Compliant, Violation, Pending
            minimum_wage_check REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        );
    """)

    # Enhanced Shifts Table with company reference and German fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            driver_id INTEGER,
            schicht_id TEXT, -- German shift ID like "2-1(2)" from examples
            shift_date TEXT NOT NULL,
            start_time TEXT, -- Dienstbeginn
            end_time TEXT, -- Dienstende
            start_location TEXT DEFAULT 'Headquarters',
            end_location TEXT,
            taetigkeit TEXT DEFAULT 'Fahrtätigkeit', -- Activity type (driving activity)
            datum_uhrzeit_schichtbeginn TEXT, -- Start date/time
            datum_uhrzeit_schichtende TEXT, -- End date/time
            gesamte_arbeitszeit_std REAL, -- Total work time in hours
            pause_min REAL, -- Break time in minutes
            reale_arbeitszeit_std REAL, -- Actual work time in hours
            fruehschicht_std REAL, -- Early shift hours
            nachtschicht_std REAL, -- Night shift hours
            status TEXT DEFAULT 'Active', -- Active, Completed, Cancelled
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        );
    """)

    # Configuration table for system settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            key TEXT NOT NULL,
            value TEXT,
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, key),
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
    """)

    # Fahrtenbuch export templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fahrtenbuch_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER DEFAULT 1,
            template_name TEXT NOT NULL,
            template_type TEXT DEFAULT 'excel', -- excel, pdf
            column_mapping TEXT, -- JSON mapping of database fields to export columns
            formatting_rules TEXT, -- JSON formatting rules
            header_info TEXT, -- JSON header information
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
    """)

    conn.commit()
    conn.close()
    print(f"Enhanced database tables created at {DATABASE_PATH}")

def initialize_default_rules():
    """Initialize default rules in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Initialize default company first
    cursor.execute("""
        INSERT OR IGNORE INTO companies (id, name, headquarters_address)
        VALUES (1, 'Muster GmbH', 'Muster Str 1, 45451 MusterStadt')
    """)

    default_rules = [
        # Distance Rules
        ('max_pickup_distance_minutes', '24', 'distance', 'Maximale Abholentfernung in Minuten vom aktuellen Standort'),
        ('max_next_job_distance_minutes', '30', 'distance', 'Maximale Entfernung zum nächsten Auftrag nach aktueller Fahrt'),
        ('max_previous_dest_minutes', '18', 'distance', 'Maximale Zeit vom aktuellen Standort zum vorherigen Ziel'),
        ('max_hq_deviation_km', '7', 'distance', 'Maximale Abweichung von der Zentrale Route in km'),
        
        # Time Rules
        ('time_tolerance_minutes', '10', 'time', 'Zeittoleranz für Fahrtenplanung in Minuten'),
        ('night_start_hour', '22', 'time', 'Stunde des Nachtschichtbeginns (24-Stunden-Format)'),
        ('night_end_hour', '6', 'time', 'Stunde des Nachtschichtendes (24-Stunden-Format)'),
        ('break_duration_minutes', '30', 'time', 'Obligatorische Pausendauer für lange Schichten'),
        ('max_continuous_hours', '8', 'time', 'Maximale kontinuierliche Arbeitszeit ohne Pause'),
        
        # Pay Rules
        ('minimum_wage_hourly', '12.41', 'pay', 'Mindestlohn pro Stunde'),
        ('overtime_threshold_hours', '40', 'pay', 'Wöchentliche Stundenschwelle für Überstunden'),
        ('overtime_rate_multiplier', '1.5', 'pay', 'Überstundenlohn-Multiplikator'),
        
        # Bonus Rules
        ('night_bonus_rate', '15.0', 'bonus', 'Nachtschicht-Bonus-Prozentsatz'),
        ('weekend_bonus_rate', '10.0', 'bonus', 'Wochenendarbeit-Bonus-Prozentsatz'),
        ('holiday_bonus_rate', '25.0', 'bonus', 'Feiertagsarbeit-Bonus-Prozentsatz'),
        ('performance_bonus_threshold', '95.0', 'bonus', 'Compliance-Rate-Schwelle für Leistungsbonus'),
        ('performance_bonus_rate', '5.0', 'bonus', 'Leistungsbonus-Prozentsatz des Umsatzes'),
    ]

    for rule_name, rule_value, rule_type, description in default_rules:
        cursor.execute("""
            INSERT OR IGNORE INTO rules (company_id, rule_name, rule_value, rule_type, description)
            VALUES (1, ?, ?, ?, ?)
        """, (rule_name, rule_value, rule_type, description))

    conn.commit()
    conn.close()
    print("Default rules initialized with German descriptions")

def initialize_config():
    """Initialize system configuration"""
    conn = get_db_connection()
    cursor = conn.cursor()

    config_items = [
        ('headquarters_address', 'Muster Str 1, 45451 MusterStadt', 'Standard-Zentrale-Adresse'),
        ('google_maps_api_key', '', 'Google Maps API-Schlüssel für Entfernungsberechnungen'),
        ('company_name', 'Muster GmbH', 'Firmenname für Berichte'),
        ('timezone', 'Europe/Berlin', 'System-Zeitzone'),
        ('currency', 'EUR', 'Währung für Lohnberechnungen'),
        ('app_mode', 'single', 'Anwendungsmodus: single oder multi'),
        ('default_fuel_consumption', '8.5', 'Standard-Kraftstoffverbrauch L/100km'),
        ('fuel_cost_per_liter', '1.45', 'Kraftstoffkosten pro Liter'),
    ]

    for key, value, description in config_items:
        cursor.execute("""
            INSERT OR IGNORE INTO config (company_id, key, value, description)
            VALUES (1, ?, ?, ?)
        """, (key, value, description))

    conn.commit()
    conn.close()
    print("System configuration initialized with German descriptions")

def initialize_fahrtenbuch_templates():
    """Initialize default German Fahrtenbuch export templates"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Excel template based on the provided examples
    excel_column_mapping = {
        "Datum_Fahrtbeginn": "DATE(pickup_time)",
        "Uhrzeit_Fahrtbeginn": "TIME(pickup_time)", 
        "Standort_Auftragsuebermittlung": "standort_auftragsuebermittlung",
        "Ist_Reserve": "is_reserved",
        "Abholort": "abholort",
        "Zielort": "zielort",
        "gefahrene_Kilometer": "gefahrene_kilometer",
        "Datum_Fahrtende": "DATE(dropoff_time)",
        "Uhrzeit_Fahrtende": "TIME(dropoff_time)",
        "Fahrtende": "destination",
        "Kennzeichen": "vehicle_plate"
    }

    excel_header_info = {
        "title": "Fahrtenbuch",
        "company_field": "Betriebssitz des Unternehmens:",
        "vehicle_field": "Fahrzeug",
        "driver_field": "Fahrer", 
        "personnel_field": "Personalnummer"
    }

    excel_formatting = {
        "date_format": "DD.MM.YYYY",
        "time_format": "HH:MM",
        "decimal_places": 2,
        "currency_symbol": "€"
    }

    cursor.execute("""
        INSERT OR IGNORE INTO fahrtenbuch_templates 
        (company_id, template_name, template_type, column_mapping, formatting_rules, header_info)
        VALUES (1, 'Standard Fahrtenbuch Excel', 'excel', ?, ?, ?)
    """, (str(excel_column_mapping), str(excel_formatting), str(excel_header_info)))

    # PDF template with same structure
    cursor.execute("""
        INSERT OR IGNORE INTO fahrtenbuch_templates 
        (company_id, template_name, template_type, column_mapping, formatting_rules, header_info)
        VALUES (1, 'Standard Fahrtenbuch PDF', 'pdf', ?, ?, ?)
    """, (str(excel_column_mapping), str(excel_formatting), str(excel_header_info)))

    conn.commit()
    conn.close()
    print("Fahrtenbuch templates initialized")

def get_address_cache(origin: str, destination: str):
    """Get cached distance and duration for address pair"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT distance_km, duration_minutes, use_count
        FROM address_cache 
        WHERE origin_address = ? AND destination_address = ?
    """, (origin.strip(), destination.strip()))
    
    result = cursor.fetchone()
    
    if result:
        # Update usage statistics
        cursor.execute("""
            UPDATE address_cache 
            SET last_used = CURRENT_TIMESTAMP, use_count = use_count + 1
            WHERE origin_address = ? AND destination_address = ?
        """, (origin.strip(), destination.strip()))
        conn.commit()
        conn.close()
        return result['distance_km'], result['duration_minutes']
    
    conn.close()
    return None, None

def cache_address_result(origin: str, destination: str, distance_km: float, duration_minutes: float):
    """Cache the result of a Google Maps API call"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO address_cache 
        (origin_address, destination_address, distance_km, duration_minutes)
        VALUES (?, ?, ?, ?)
    """, (origin.strip(), destination.strip(), distance_km, duration_minutes))
    
    conn.commit()
    conn.close()

def get_company_config(company_id: int, key: str):
    """Get configuration value for a specific company"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT value FROM config 
        WHERE company_id = ? AND key = ?
    """, (company_id, key))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['value'] if result else None

def set_company_config(company_id: int, key: str, value: str):
    """Set configuration value for a specific company"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO config (company_id, key, value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (company_id, key, value))
    
    conn.commit()
    conn.close()

def get_companies():
    """Get list of all active companies"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, headquarters_address, phone, email
        FROM companies 
        WHERE is_active = 1
        ORDER BY name
    """)
    
    companies = cursor.fetchall()
    conn.close()
    
    return companies

def migrate_existing_data():
    """Migrate existing data to new schema if needed"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if companies table exists, create if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
        if not cursor.fetchone():
            print("Creating companies table...")
            cursor.execute("""
                CREATE TABLE companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    address TEXT,
                    headquarters_address TEXT DEFAULT 'Headquarters, Main Street 1, City',
                    phone TEXT,
                    email TEXT,
                    tax_number TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                );
            """)
            # Insert default company
            cursor.execute("""
                INSERT INTO companies (id, name, headquarters_address)
                VALUES (1, 'Muster GmbH', 'Muster Str 1, 45451 MusterStadt')
            """)
            
        # Check if address_cache table exists, create if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='address_cache'")
        if not cursor.fetchone():
            print("Creating address_cache table...")
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
            
        # Check if fahrtenbuch_templates table exists, create if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fahrtenbuch_templates'")
        if not cursor.fetchone():
            print("Creating fahrtenbuch_templates table...")
            cursor.execute("""
                CREATE TABLE fahrtenbuch_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER DEFAULT 1,
                    template_name TEXT NOT NULL,
                    template_type TEXT DEFAULT 'excel',
                    column_mapping TEXT,
                    formatting_rules TEXT,
                    header_info TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                );
            """)

        # Check and update rides table
        cursor.execute("PRAGMA table_info(rides)")
        ride_columns = [row[1] for row in cursor.fetchall()]
        
        new_ride_columns = [
            ('company_id', 'INTEGER DEFAULT 1'),
            ('shift_id', 'INTEGER'),
            ('fahrtenbuch_nummer', 'TEXT'),
            ('dropoff_time', 'TEXT'),
            ('standort_auftragsuebermittlung', 'TEXT'),
            ('abholort', 'TEXT'),
            ('zielort', 'TEXT'),
            ('gefahrene_kilometer', 'REAL'),
            ('verbrauch_liter', 'REAL'),
            ('kosten_euro', 'REAL'),
            ('reisezweck', 'TEXT'),
            ('distance_km', 'REAL'),
            ('duration_minutes', 'REAL'),
            ('passengers', 'INTEGER DEFAULT 1'),
            ('is_reserved', 'BOOLEAN DEFAULT 0'),
            ('assigned_during_ride', 'BOOLEAN DEFAULT 0'),
            ('current_route_destination', 'TEXT'),
            ('fare_type', 'TEXT DEFAULT "Standard"'),
            ('payment_method', 'TEXT'),
            ('notes', 'TEXT'),
            ('created_at', 'TEXT DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TEXT DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for col_name, col_type in new_ride_columns:
            if col_name not in ride_columns:
                cursor.execute(f"ALTER TABLE rides ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to rides table")

        # Check and update drivers table
        cursor.execute("PRAGMA table_info(drivers)")
        driver_columns = [row[1] for row in cursor.fetchall()]
        
        driver_new_columns = [
            ('company_id', 'INTEGER DEFAULT 1'),
            ('personalnummer', 'TEXT'),
        ]
        
        for col_name, col_type in driver_new_columns:
            if col_name not in driver_columns:
                cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to drivers table")

        # Check and update vehicles table
        cursor.execute("PRAGMA table_info(vehicles)")
        vehicle_columns = [row[1] for row in cursor.fetchall()]
        
        if 'company_id' not in vehicle_columns:
            cursor.execute("ALTER TABLE vehicles ADD COLUMN company_id INTEGER DEFAULT 1")
            print("Added company_id column to vehicles table")

        # Handle rules table - this is more complex as we need to change the structure
        cursor.execute("PRAGMA table_info(rules)")
        rules_columns = [row[1] for row in cursor.fetchall()]
        
        if 'company_id' not in rules_columns:
            print("Migrating rules table to new schema...")
            # Create new rules table with proper schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER DEFAULT 1,
                    rule_name TEXT NOT NULL,
                    rule_value TEXT,
                    rule_type TEXT DEFAULT 'distance',
                    description TEXT,
                    enabled INTEGER DEFAULT 1,
                    driver_specific INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, rule_name),
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                );
            """)
            
            # Copy existing rules to new table
            cursor.execute("""
                INSERT INTO rules_new (rule_name, rule_value, rule_type, description, enabled, driver_specific)
                SELECT rule_name, rule_value, rule_type, description, enabled, driver_specific FROM rules
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE rules")
            cursor.execute("ALTER TABLE rules_new RENAME TO rules")

        # Handle config table
        cursor.execute("PRAGMA table_info(config)")
        config_columns = [row[1] for row in cursor.fetchall()]
        
        if 'company_id' not in config_columns:
            print("Migrating config table to new schema...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER DEFAULT 1,
                    key TEXT NOT NULL,
                    value TEXT,
                    description TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, key),
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                );
            """)
            
            # Copy existing config to new table
            cursor.execute("""
                INSERT INTO config_new (key, value, description)
                SELECT key, value, description FROM config
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE config")
            cursor.execute("ALTER TABLE config_new RENAME TO config")

        # Check and update shifts table
        cursor.execute("PRAGMA table_info(shifts)")
        shift_columns = [row[1] for row in cursor.fetchall()]
        
        shift_new_columns = [
            ('company_id', 'INTEGER DEFAULT 1'),
            ('schicht_id', 'TEXT'),
            ('taetigkeit', 'TEXT DEFAULT "Fahrtätigkeit"'),
            ('datum_uhrzeit_schichtbeginn', 'TEXT'),
            ('datum_uhrzeit_schichtende', 'TEXT'),
            ('gesamte_arbeitszeit_std', 'REAL'),
            ('pause_min', 'REAL'),
            ('reale_arbeitszeit_std', 'REAL'),
            ('fruehschicht_std', 'REAL'),
            ('nachtschicht_std', 'REAL'),
        ]
        
        for col_name, col_type in shift_new_columns:
            if col_name not in shift_columns:
                cursor.execute(f"ALTER TABLE shifts ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to shifts table")

        # Check and update payroll table
        cursor.execute("PRAGMA table_info(payroll)")
        payroll_columns = [row[1] for row in cursor.fetchall()]
        
        if 'company_id' not in payroll_columns:
            cursor.execute("ALTER TABLE payroll ADD COLUMN company_id INTEGER DEFAULT 1")
            print("Added company_id column to payroll table")

        conn.commit()
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
        
    finally:
        conn.close()

# --- Example Usage & Initialization ---
def initialize_database():
    """Initializes the database by creating tables and default data."""
    create_tables()
    migrate_existing_data()  # Migrate before inserting default data
    initialize_default_rules()
    initialize_config()
    initialize_fahrtenbuch_templates()
    
    # Initialize labor law tables
    from core.labor_law_validator import GermanLaborLawValidator
    labor_validator = GermanLaborLawValidator()
    labor_validator.create_labor_law_tables()
    
    # Add enhanced labor law rules
    initialize_enhanced_labor_rules()

def initialize_enhanced_labor_rules():
    """Initialize enhanced labor law rules"""
    conn = get_db_connection()
    cursor = conn.cursor()

    enhanced_rules = [
        # Enhanced Labor Law Rules based on German requirements
        ('max_shift_duration_hours', '10', 'time', 'Maximale Schichtdauer in Stunden'),
        ('min_break_6_hours', '30', 'time', 'Mindestpause für 6-9 Stunden Arbeitszeit (Minuten)'),
        ('min_break_9_hours', '45', 'time', 'Mindestpause für 9+ Stunden Arbeitszeit (Minuten)'),
        ('min_break_interval', '15', 'time', 'Mindestzeit pro Pausenintervall (Minuten)'),
        ('min_daily_rest_hours', '11', 'time', 'Mindesttagsruhezeit zwischen Schichten (Stunden)'),
        ('max_weekly_hours', '60', 'time', 'Maximale wöchentliche Arbeitszeit (Stunden)'),
        ('weekly_average_limit', '48', 'time', 'Durchschnittliche wöchentliche Arbeitszeit (Stunden)'),
        ('max_continuous_work_hours', '6', 'time', 'Maximale kontinuierliche Arbeitszeit ohne Pause (Stunden)'),
        
        # Violation severity settings
        ('high_severity_threshold', '3', 'system', 'Schwellenwert für schwerwiegende Verstöße'),
        ('medium_severity_threshold', '2', 'system', 'Schwellenwert für mittlere Verstöße'),
        ('auto_resolve_violations', '0', 'system', 'Automatische Behebung von Verstößen aktivieren'),
        
        # Compliance reporting
        ('compliance_report_frequency', 'weekly', 'system', 'Häufigkeit der Compliance-Berichte'),
        ('min_compliance_rate', '85.0', 'system', 'Mindest-Compliance-Rate (%)'),
        ('violation_alert_enabled', '1', 'system', 'Verstößwarnungen aktiviert'),
    ]

    for rule_name, rule_value, rule_type, description in enhanced_rules:
        cursor.execute("""
            INSERT OR IGNORE INTO rules (company_id, rule_name, rule_value, rule_type, description)
            VALUES (1, ?, ?, ?, ?)
        """, (rule_name, rule_value, rule_type, description))

    conn.commit()
    conn.close()
    print("Enhanced labor law rules initialized")

if __name__ == "__main__":
    # This allows running the script directly to initialize the DB
    print("Initializing database...")
    initialize_database()
    print("Database initialization complete.")


