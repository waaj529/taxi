"""
Excel Workbook Logic Implementation
Replicates all formulas, calculations, validations, and automatic features
from the "Fahrtenbuch V6-2.xlsm" reference workbook
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from core.database import get_db_connection, get_company_config
from core.google_maps import GoogleMapsIntegration
from core.translation_manager import tr

class ExcelWorkbookLogic:
    """
    Implements the Excel workbook logic for automatic calculations,
    validations, and data pre-filling found in the reference workbook
    """
    
    def __init__(self, company_id: int = 1):
        self.company_id = company_id
        self.db_conn = get_db_connection()
        self.maps_api = GoogleMapsIntegration()
        
        # Load configuration values (equivalent to Excel named ranges/constants)
        self.config = self._load_configuration()
        
        # Track state for auto-fill functionality
        self._previous_destinations = {}  # Per driver
        self._current_shift_data = {}
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration values that would be constants in Excel"""
        
        config = {
            # Fuel and cost calculations
            'fuel_consumption_l_per_100km': float(get_company_config(self.company_id, 'default_fuel_consumption') or 8.5),
            'fuel_cost_per_liter': float(get_company_config(self.company_id, 'fuel_cost_per_liter') or 1.45),
            'default_speed_kmh': 50.0,  # For time estimation
            
            # Distance and time tolerances
            'max_distance_deviation_km': 5.0,
            'time_tolerance_minutes': 10,
            
            # Payroll calculations
            'standard_hourly_rate': float(get_company_config(self.company_id, 'minimum_wage_hourly') or 12.41),
            'night_shift_bonus': 0.15,  # 15% bonus
            'overtime_multiplier': 1.5,
            'standard_work_hours_per_day': 8.0,
            
            # Break time calculations
            'mandatory_break_after_hours': 6.0,
            'mandatory_break_duration_minutes': 30,
            
            # Company information
            'headquarters_address': get_company_config(self.company_id, 'headquarters_address') or 'Muster Str 1, 45451 MusterStadt',
            'company_name': get_company_config(self.company_id, 'company_name') or 'Muster GmbH',
        }
        
        return config
    
    def auto_fill_start_location(self, driver_id: int, current_ride_data: Dict) -> str:
        """
        Automatically fill starting location from previous destination
        Implements Excel auto-fill logic
        """
        
        # Get the last destination for this driver
        previous_destination = self._get_last_destination(driver_id)
        
        if previous_destination:
            # Check if it's reasonable (within same city/region)
            current_pickup = current_ride_data.get('pickup_location', '')
            
            if self._is_reasonable_continuation(previous_destination, current_pickup):
                return previous_destination
        
        # Default to headquarters if no reasonable previous destination
        return self.config['headquarters_address']
    
    def _get_last_destination(self, driver_id: int) -> Optional[str]:
        """Get the last destination for a driver from the database"""
        
        cursor = self.db_conn.cursor()
        
        cursor.execute("""
            SELECT destination, zielort
            FROM rides 
            WHERE driver_id = ? AND company_id = ?
                AND dropoff_time IS NOT NULL
            ORDER BY dropoff_time DESC
            LIMIT 1
        """, [driver_id, self.company_id])
        
        result = cursor.fetchone()
        
        if result:
            return result['zielort'] or result['destination']
        
        return None
    
    def _is_reasonable_continuation(self, previous_dest: str, current_pickup: str) -> bool:
        """Check if current pickup is a reasonable continuation from previous destination"""
        
        if not previous_dest or not current_pickup:
            return False
        
        try:
            # Use cached distance calculation
            distance_km, duration_min = self.maps_api.calculate_distance_and_duration(
                previous_dest, current_pickup, use_cache=True
            )
            
            # If distance is less than 20km, it's reasonable
            return distance_km < 20.0
        except:
            return False
    
    def calculate_distance_and_time(self, pickup_location: str, destination: str) -> Tuple[float, float]:
        """
        Calculate distance and time using Google Maps API with fallback formulas
        Implements Excel distance calculation logic
        """
        
        try:
            # Try Google Maps API first (with caching)
            distance_km, duration_min = self.maps_api.calculate_distance_and_duration(
                pickup_location, destination, use_cache=True
            )
            
            return distance_km, duration_min
            
        except Exception:
            # Fallback calculation (Excel-like formula)
            return self._fallback_distance_calculation(pickup_location, destination)
    
    def _fallback_distance_calculation(self, pickup: str, destination: str) -> Tuple[float, float]:
        """
        Fallback distance calculation when Google Maps API is not available
        Uses simplified formula similar to Excel approximation
        """
        
        # Simple estimation based on string similarity and common patterns
        if not pickup or not destination:
            return 0.0, 0.0
        
        # Basic estimation: assume 10km for local trips, more for different cities
        pickup_parts = pickup.lower().split()
        dest_parts = destination.lower().split()
        
        # Check for common city indicators
        pickup_city = self._extract_city_from_address(pickup)
        dest_city = self._extract_city_from_address(destination)
        
        if pickup_city == dest_city:
            # Same city - estimate 5-15km
            base_distance = 10.0
        else:
            # Different cities - estimate 30-100km  
            base_distance = 50.0
        
        # Add variation based on address complexity
        distance_km = base_distance + len(destination.split()) * 2
        
        # Calculate time (assuming average speed)
        duration_min = (distance_km / self.config['default_speed_kmh']) * 60
        
        return distance_km, duration_min
    
    def _extract_city_from_address(self, address: str) -> str:
        """Extract city name from address string"""
        
        # Simple heuristic: look for postal code + city pattern
        import re
        
        # German postal code pattern
        match = re.search(r'\d{5}\s+([A-ZÄÖÜa-zäöüß]+)', address)
        if match:
            return match.group(1).lower()
        
        # Fallback: take last word before common address endings
        words = address.replace(',', '').split()
        for i, word in enumerate(words):
            if word.lower() in ['str', 'straße', 'weg', 'platz', 'gasse']:
                if i > 0:
                    return words[i-1].lower()
        
        return address.split()[-1].lower() if words else ''
    
    def calculate_fuel_consumption_and_cost(self, distance_km: float) -> Dict[str, float]:
        """
        Calculate fuel consumption and costs using Excel formulas
        Implements the fuel calculation logic from the reference workbook
        """
        
        fuel_consumption_liters = (distance_km * self.config['fuel_consumption_l_per_100km']) / 100
        fuel_cost_euros = fuel_consumption_liters * self.config['fuel_cost_per_liter']
        
        return {
            'fuel_consumption_liters': round(fuel_consumption_liters, 2),
            'fuel_cost_euros': round(fuel_cost_euros, 2),
            'distance_km': round(distance_km, 2)
        }
    
    def calculate_shift_hours_and_pay(self, shift_data: Dict) -> Dict[str, Any]:
        """
        Calculate shift hours, breaks, and pay using Excel formulas
        Implements timesheet calculation logic
        """
        
        start_time = self._parse_time(shift_data.get('start_time'))
        end_time = self._parse_time(shift_data.get('end_time'))
        
        if not start_time or not end_time:
            return self._empty_shift_calculation()
        
        # Calculate total work time
        total_duration = end_time - start_time
        total_hours = total_duration.total_seconds() / 3600
        
        # Calculate break time (Excel logic)
        break_minutes = self._calculate_mandatory_break(total_hours)
        actual_work_hours = total_hours - (break_minutes / 60)
        
        # Determine shift types (Excel formulas)
        night_hours = self._calculate_night_shift_hours(start_time, end_time)
        early_hours = self._calculate_early_shift_hours(start_time, end_time)
        regular_hours = actual_work_hours - night_hours - early_hours
        
        # Calculate pay (Excel formulas)
        base_pay = actual_work_hours * self.config['standard_hourly_rate']
        night_bonus = night_hours * self.config['standard_hourly_rate'] * self.config['night_shift_bonus']
        overtime_pay = self._calculate_overtime_pay(actual_work_hours)
        
        total_pay = base_pay + night_bonus + overtime_pay
        
        return {
            'total_work_hours': round(total_hours, 2),
            'break_minutes': break_minutes,
            'actual_work_hours': round(actual_work_hours, 2),
            'night_hours': round(night_hours, 2),
            'early_hours': round(early_hours, 2),
            'regular_hours': round(regular_hours, 2),
            'base_pay': round(base_pay, 2),
            'night_bonus': round(night_bonus, 2),
            'overtime_pay': round(overtime_pay, 2),
            'total_pay': round(total_pay, 2)
        }
    
    def _parse_time(self, time_str: Any) -> Optional[datetime]:
        """Parse time string in various formats"""
        
        if not time_str:
            return None
        
        if isinstance(time_str, datetime):
            return time_str
        
        try:
            # Try ISO format
            return datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
        except:
            # Try other formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M', '%H:%M']:
                try:
                    if ':' in str(time_str) and len(str(time_str)) < 10:
                        # Just time, assume today's date
                        today = datetime.now().date()
                        time_obj = datetime.strptime(str(time_str), '%H:%M').time()
                        return datetime.combine(today, time_obj)
                    else:
                        return datetime.strptime(str(time_str), fmt)
                except:
                    continue
        
        return None
    
    def _calculate_mandatory_break(self, work_hours: float) -> int:
        """Calculate mandatory break time based on work hours (Excel logic)"""
        
        if work_hours >= self.config['mandatory_break_after_hours']:
            return self.config['mandatory_break_duration_minutes']
        elif work_hours >= 4.0:
            return 15  # Short break for 4-6 hour shifts
        else:
            return 0
    
    def _calculate_night_shift_hours(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate night shift hours (22:00 - 06:00) using Excel logic"""
        
        night_start = 22  # 22:00
        night_end = 6     # 06:00
        
        total_night_hours = 0.0
        current_time = start_time
        
        while current_time < end_time:
            hour = current_time.hour
            
            # Check if current hour is in night time
            if hour >= night_start or hour < night_end:
                # Calculate how much of this hour is worked
                next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                hour_end = min(next_hour, end_time)
                
                hour_duration = (hour_end - current_time).total_seconds() / 3600
                total_night_hours += hour_duration
            
            # Move to next hour
            current_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
        return total_night_hours
    
    def _calculate_early_shift_hours(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate early shift hours (05:00 - 09:00) using Excel logic"""
        
        early_start = 5   # 05:00
        early_end = 9     # 09:00
        
        total_early_hours = 0.0
        current_time = start_time
        
        while current_time < end_time:
            hour = current_time.hour
            
            # Check if current hour is in early time
            if early_start <= hour < early_end:
                # Calculate how much of this hour is worked
                next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                hour_end = min(next_hour, end_time)
                
                hour_duration = (hour_end - current_time).total_seconds() / 3600
                total_early_hours += hour_duration
            
            # Move to next hour
            current_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
        return total_early_hours
    
    def _calculate_overtime_pay(self, actual_work_hours: float) -> float:
        """Calculate overtime pay using Excel logic"""
        
        if actual_work_hours > self.config['standard_work_hours_per_day']:
            overtime_hours = actual_work_hours - self.config['standard_work_hours_per_day']
            return overtime_hours * self.config['standard_hourly_rate'] * (self.config['overtime_multiplier'] - 1)
        
        return 0.0
    
    def _empty_shift_calculation(self) -> Dict[str, Any]:
        """Return empty shift calculation for invalid data"""
        
        return {
            'total_work_hours': 0.0,
            'break_minutes': 0,
            'actual_work_hours': 0.0,
            'night_hours': 0.0,
            'early_hours': 0.0,
            'regular_hours': 0.0,
            'base_pay': 0.0,
            'night_bonus': 0.0,
            'overtime_pay': 0.0,
            'total_pay': 0.0
        }
    
    def validate_ride_data(self, ride_data: Dict) -> Dict[str, Any]:
        """
        Validate ride data using Excel validation rules
        Implements data validation logic from the reference workbook
        """
        
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Required field validation
        required_fields = ['pickup_time', 'pickup_location', 'destination', 'driver_id']
        for field in required_fields:
            if not ride_data.get(field):
                validation_result['errors'].append(f"Required field missing: {tr(field)}")
                validation_result['is_valid'] = False
        
        # Distance validation
        distance = ride_data.get('gefahrene_kilometer', 0)
        if distance:
            pickup = ride_data.get('pickup_location', '')
            destination = ride_data.get('destination', '')
            
            if pickup and destination:
                api_distance, _ = self.calculate_distance_and_time(pickup, destination)
                
                if abs(distance - api_distance) > self.config['max_distance_deviation_km']:
                    validation_result['warnings'].append(
                        f"Distance deviation: Entered {distance}km, calculated {api_distance:.1f}km"
                    )
        
        # Time validation
        pickup_time = self._parse_time(ride_data.get('pickup_time'))
        dropoff_time = self._parse_time(ride_data.get('dropoff_time'))
        
        if pickup_time and dropoff_time:
            if dropoff_time <= pickup_time:
                validation_result['errors'].append("Dropoff time must be after pickup time")
                validation_result['is_valid'] = False
        
        # Auto-fill suggestions
        driver_id = ride_data.get('driver_id')
        if driver_id and not ride_data.get('standort_auftragsuebermittlung'):
            suggested_start = self.auto_fill_start_location(driver_id, ride_data)
            validation_result['suggestions'].append(
                f"Suggested start location: {suggested_start}"
            )
        
        return validation_result
    
    def generate_monthly_summary(self, driver_id: int, month: int, year: int) -> Dict[str, Any]:
        """
        Generate monthly summary using Excel aggregation formulas
        Implements summary calculations from the reference workbook
        """
        
        cursor = self.db_conn.cursor()
        
        # Get all shifts for the month
        first_day = f"{year}-{month:02d}-01"
        import calendar
        last_day = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
        
        cursor.execute("""
            SELECT * FROM shifts 
            WHERE driver_id = ? AND company_id = ?
                AND shift_date BETWEEN ? AND ?
            ORDER BY shift_date
        """, [driver_id, self.company_id, first_day, last_day])
        
        shifts = cursor.fetchall()
        
        # Calculate totals using Excel formulas
        total_hours = 0.0
        total_night_hours = 0.0
        total_early_hours = 0.0
        total_break_minutes = 0
        total_pay = 0.0
        
        for shift in shifts:
            shift_calc = self.calculate_shift_hours_and_pay(dict(shift))
            total_hours += shift_calc['actual_work_hours']
            total_night_hours += shift_calc['night_hours']
            total_early_hours += shift_calc['early_hours']
            total_break_minutes += shift_calc['break_minutes']
            total_pay += shift_calc['total_pay']
        
        # Get ride statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rides,
                SUM(gefahrene_kilometer) as total_distance,
                SUM(kosten_euro) as total_costs
            FROM rides 
            WHERE driver_id = ? AND company_id = ?
                AND DATE(pickup_time) BETWEEN ? AND ?
        """, [driver_id, self.company_id, first_day, last_day])
        
        ride_stats = cursor.fetchone()
        
        return {
            'month': month,
            'year': year,
            'total_shifts': len(shifts),
            'total_work_hours': round(total_hours, 2),
            'total_night_hours': round(total_night_hours, 2),
            'total_early_hours': round(total_early_hours, 2),
            'total_break_minutes': total_break_minutes,
            'total_gross_pay': round(total_pay, 2),
            'total_rides': ride_stats['total_rides'] or 0,
            'total_distance': round(ride_stats['total_distance'] or 0, 2),
            'total_costs': round(ride_stats['total_costs'] or 0, 2),
            'hourly_average': round(total_pay / total_hours if total_hours > 0 else 0, 2)
        }
    
    def apply_excel_formulas_to_ride(self, ride_data: Dict) -> Dict:
        """
        Apply all Excel formulas to a single ride entry
        This implements the comprehensive logic from the reference workbook
        """
        
        enhanced_ride = ride_data.copy()
        
        # Auto-fill start location if not provided
        if not enhanced_ride.get('standort_auftragsuebermittlung') and enhanced_ride.get('driver_id'):
            enhanced_ride['standort_auftragsuebermittlung'] = self.auto_fill_start_location(
                enhanced_ride['driver_id'], enhanced_ride
            )
        
        # Calculate distance and time if not provided
        pickup = enhanced_ride.get('pickup_location', '')
        destination = enhanced_ride.get('destination', '')
        
        if pickup and destination and not enhanced_ride.get('gefahrene_kilometer'):
            distance, duration = self.calculate_distance_and_time(pickup, destination)
            enhanced_ride['gefahrene_kilometer'] = distance
            enhanced_ride['estimated_duration_minutes'] = duration
        
        # Calculate fuel consumption and costs
        distance = enhanced_ride.get('gefahrene_kilometer', 0)
        if distance:
            fuel_calc = self.calculate_fuel_consumption_and_cost(distance)
            enhanced_ride.update(fuel_calc)
        
        # Validation
        validation = self.validate_ride_data(enhanced_ride)
        enhanced_ride['validation_result'] = validation
        
        return enhanced_ride 