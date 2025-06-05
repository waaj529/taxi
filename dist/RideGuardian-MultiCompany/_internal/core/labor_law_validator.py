"""
German Labor Law Validation System
Implements comprehensive violation detection for German driving service laws
Based on Arbeitszeitgesetz (ArbZG) and Fahrpersonalverordnung
"""

import sqlite3
from datetime import datetime, timedelta, time as time_obj
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from core.database import get_db_connection
import json

@dataclass
class WorkTimeViolation:
    """Represents a work time violation"""
    violation_type: str
    severity: str  # 'high', 'medium', 'low'
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    driver_id: int
    shift_id: Optional[int] = None
    ride_id: Optional[int] = None

class GermanLaborLawValidator:
    """
    Comprehensive German Labor Law Validator
    Implements all requirements from client specification
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection or get_db_connection()
        
        # German Labor Law Constants
        self.BREAK_RULES = {
            6: 30,   # 6-9 hours: 30 min break
            9: 45    # 9+ hours: 45 min break
        }
        self.MIN_BREAK_INTERVAL = 15  # Minimum 15 minutes per break
        self.MIN_DAILY_REST = 11      # 11 consecutive hours
        self.MAX_SHIFT_HOURS = 10     # Maximum 10 hours per shift
        self.MAX_WEEKLY_HOURS = 60    # Maximum 60 hours per week
        self.WEEKLY_AVERAGE_LIMIT = 48  # Average 48 hours per week over time
        
    def validate_shift_compliance(self, shift_id: int) -> List[WorkTimeViolation]:
        """
        Validate a complete shift for all labor law violations
        """
        violations = []
        
        shift_data = self._get_shift_data(shift_id)
        if not shift_data:
            return violations
            
        # 1. Check maximum shift duration (10 hours)
        violations.extend(self._check_max_shift_duration(shift_data))
        
        # 2. Check mandatory break requirements
        violations.extend(self._check_break_requirements(shift_data))
        
        # 3. Check minimum rest period between shifts
        violations.extend(self._check_daily_rest_period(shift_data))
        
        # 4. Check weekly working time limits
        violations.extend(self._check_weekly_working_time(shift_data))
        
        return violations
    
    def validate_driver_weekly_compliance(self, driver_id: int, week_start: datetime) -> List[WorkTimeViolation]:
        """
        Validate driver's entire week for compliance
        """
        violations = []
        
        week_data = self._get_weekly_data(driver_id, week_start)
        
        # Check total weekly hours
        total_hours = sum(shift['total_hours'] for shift in week_data['shifts'])
        
        if total_hours > self.MAX_WEEKLY_HOURS:
            violations.append(WorkTimeViolation(
                violation_type='weekly_overtime_limit',
                severity='high',
                message=f'Wöchentliche Arbeitszeit überschritten: {total_hours:.1f}h (max. {self.MAX_WEEKLY_HOURS}h)',
                details={
                    'actual_hours': total_hours,
                    'limit': self.MAX_WEEKLY_HOURS,
                    'excess_hours': total_hours - self.MAX_WEEKLY_HOURS,
                    'week_start': week_start.isoformat()
                },
                timestamp=datetime.now(),
                driver_id=driver_id
            ))
            
        # Check for insufficient rest periods between shifts
        violations.extend(self._check_weekly_rest_periods(week_data))
        
        return violations
    
    def _parse_datetime_safely(self, date_str: str, time_str: str) -> datetime:
        """
        Safely parse datetime from potentially inconsistent database formats
        """
        try:
            # If time_str already contains date and time, parse it directly
            if ' ' in time_str and len(time_str) > 10:
                return datetime.fromisoformat(time_str)
            # Otherwise combine date and time
            else:
                return datetime.fromisoformat(f"{date_str} {time_str}")
        except ValueError:
            # Fallback: try parsing time_str as time-only and combine with date
            try:
                # Handle time-only format like "06:14:35"
                if ':' in time_str and len(time_str) <= 8:
                    return datetime.fromisoformat(f"{date_str} {time_str}")
                else:
                    raise ValueError(f"Cannot parse datetime from date='{date_str}' time='{time_str}'")
            except ValueError as e:
                print(f"DateTime parsing failed: {e}")
                # Return a default datetime to prevent crashes
                return datetime.fromisoformat(f"{date_str} 00:00:00")

    def _check_max_shift_duration(self, shift_data: Dict) -> List[WorkTimeViolation]:
        """
        Check if shift exceeds maximum 10 hours
        """
        violations = []
        
        start_time = self._parse_datetime_safely(shift_data['shift_date'], shift_data['start_time'])
        end_time = self._parse_datetime_safely(shift_data['shift_date'], shift_data['end_time'])
        
        total_duration = (end_time - start_time).total_seconds() / 3600
        
        if total_duration > self.MAX_SHIFT_HOURS:
            violations.append(WorkTimeViolation(
                violation_type='max_shift_exceeded',
                severity='high',
                message=f'Maximale Schichtdauer überschritten: {total_duration:.1f}h (max. {self.MAX_SHIFT_HOURS}h)',
                details={
                    'actual_hours': total_duration,
                    'limit': self.MAX_SHIFT_HOURS,
                    'excess_hours': total_duration - self.MAX_SHIFT_HOURS,
                    'shift_start': start_time.isoformat(),
                    'shift_end': end_time.isoformat()
                },
                timestamp=datetime.now(),
                driver_id=shift_data['driver_id'],
                shift_id=shift_data['id']
            ))
            
        return violations

    def _check_break_requirements(self, shift_data: Dict) -> List[WorkTimeViolation]:
        """
        Check mandatory break requirements:
        - 6-9 hours: 30 min break
        - 9+ hours: 45 min break
        - Breaks in minimum 15-minute intervals
        """
        violations = []
        
        start_time = self._parse_datetime_safely(shift_data['shift_date'], shift_data['start_time'])
        end_time = self._parse_datetime_safely(shift_data['shift_date'], shift_data['end_time'])
        
        total_duration = (end_time - start_time).total_seconds() / 3600
        
        # Determine required break time
        required_break = 0
        if total_duration >= 9:
            required_break = 45
        elif total_duration >= 6:
            required_break = 30
            
        if required_break > 0:
            # Get actual break time from shift data
            actual_break = shift_data.get('pause_min', 0) or 0
            
            if actual_break < required_break:
                violations.append(WorkTimeViolation(
                    violation_type='insufficient_break',
                    severity='high',
                    message=f'Unzureichende Pausenzeit: {actual_break}min (benötigt: {required_break}min)',
                    details={
                        'actual_break_minutes': actual_break,
                        'required_break_minutes': required_break,
                        'shift_duration_hours': total_duration,
                        'break_deficit': required_break - actual_break
                    },
                    timestamp=datetime.now(),
                    driver_id=shift_data['driver_id'],
                    shift_id=shift_data['id']
                ))
                
            # Check if breaks are in proper intervals (15+ minutes each)
            violations.extend(self._check_break_intervals(shift_data))
            
        return violations
    
    def _check_break_intervals(self, shift_data: Dict) -> List[WorkTimeViolation]:
        """
        Check if breaks are taken in proper intervals (minimum 15 minutes each)
        """
        violations = []
        
        # Get rides for this shift to analyze break patterns
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT pickup_time, dropoff_time 
            FROM rides 
            WHERE shift_id = ? 
            ORDER BY pickup_time
        """, (shift_data['id'],))
        
        rides = cursor.fetchall()
        
        if len(rides) < 2:
            return violations
            
        # Analyze gaps between rides to identify breaks
        break_periods = []
        for i in range(1, len(rides)):
            prev_end = datetime.fromisoformat(rides[i-1]['dropoff_time'])
            curr_start = datetime.fromisoformat(rides[i]['pickup_time'])
            gap_minutes = (curr_start - prev_end).total_seconds() / 60
            
            # Consider gaps > 10 minutes as potential breaks
            if gap_minutes > 10:
                break_periods.append(gap_minutes)
                
        # Check if any individual break is less than 15 minutes
        short_breaks = [b for b in break_periods if 5 < b < self.MIN_BREAK_INTERVAL]
        
        if short_breaks:
            violations.append(WorkTimeViolation(
                violation_type='short_break_intervals',
                severity='medium',
                message=f'Pausenintervalle zu kurz: {len(short_breaks)} Pausen unter {self.MIN_BREAK_INTERVAL} Minuten',
                details={
                    'short_breaks': short_breaks,
                    'min_interval': self.MIN_BREAK_INTERVAL,
                    'break_periods': break_periods
                },
                timestamp=datetime.now(),
                driver_id=shift_data['driver_id'],
                shift_id=shift_data['id']
            ))
            
        return violations
    
    def _check_daily_rest_period(self, shift_data: Dict) -> List[WorkTimeViolation]:
        """
        Check minimum 11 consecutive hours rest between shifts
        """
        violations = []
        
        cursor = self.db.cursor()
        
        # Get previous shift for this driver
        cursor.execute("""
            SELECT shift_date, end_time 
            FROM shifts 
            WHERE driver_id = ? AND shift_date < ? 
            ORDER BY shift_date DESC, end_time DESC 
            LIMIT 1
        """, (shift_data['driver_id'], shift_data['shift_date']))
        
        prev_shift = cursor.fetchone()
        
        if prev_shift:
            # Calculate rest period - handle different datetime formats
            try:
                # Try to parse end_time directly if it's already a full datetime
                if ' ' in prev_shift['end_time'] and len(prev_shift['end_time']) > 10:
                    prev_end = datetime.fromisoformat(prev_shift['end_time'])
                else:
                    # Standard format: combine date and time
                    prev_end = datetime.fromisoformat(f"{prev_shift['shift_date']} {prev_shift['end_time']}")
                
                if ' ' in shift_data['start_time'] and len(shift_data['start_time']) > 10:
                    curr_start = datetime.fromisoformat(shift_data['start_time'])
                else:
                    curr_start = datetime.fromisoformat(f"{shift_data['shift_date']} {shift_data['start_time']}")
                
            except ValueError as e:
                print(f"DateTime parsing error: {e}")
                return violations
            
            # Handle day transitions
            if curr_start < prev_end:
                curr_start += timedelta(days=1)
                
            rest_hours = (curr_start - prev_end).total_seconds() / 3600
            
            if rest_hours < self.MIN_DAILY_REST:
                violations.append(WorkTimeViolation(
                    violation_type='insufficient_daily_rest',
                    severity='high',
                    message=f'Unzureichende Ruhezeit: {rest_hours:.1f}h (min. {self.MIN_DAILY_REST}h)',
                    details={
                        'actual_rest_hours': rest_hours,
                        'required_rest_hours': self.MIN_DAILY_REST,
                        'rest_deficit': self.MIN_DAILY_REST - rest_hours,
                        'previous_shift_end': prev_end.isoformat(),
                        'current_shift_start': curr_start.isoformat()
                    },
                    timestamp=datetime.now(),
                    driver_id=shift_data['driver_id'],
                    shift_id=shift_data['id']
                ))
                
        return violations
    
    def _check_weekly_working_time(self, shift_data: Dict) -> List[WorkTimeViolation]:
        """
        Check weekly working time compliance
        """
        violations = []
        
        # Get shift start date
        shift_date = datetime.fromisoformat(shift_data['shift_date'])
        
        # Calculate week boundaries (Monday to Sunday)
        week_start = shift_date - timedelta(days=shift_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get all shifts for this week
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT shift_date, start_time, end_time 
            FROM shifts 
            WHERE driver_id = ? 
            AND shift_date BETWEEN ? AND ?
            AND status != 'Cancelled'
        """, (shift_data['driver_id'], week_start.date().isoformat(), week_end.date().isoformat()))
        
        week_shifts = cursor.fetchall()
        
        total_weekly_hours = 0
        for shift in week_shifts:
            try:
                start = self._parse_datetime_safely(shift['shift_date'], shift['start_time'])
                end = self._parse_datetime_safely(shift['shift_date'], shift['end_time'])
                shift_hours = (end - start).total_seconds() / 3600
                total_weekly_hours += shift_hours
            except Exception as e:
                print(f"Error parsing shift times: {e}")
                continue
            
        if total_weekly_hours > self.MAX_WEEKLY_HOURS:
            violations.append(WorkTimeViolation(
                violation_type='weekly_hours_exceeded',
                severity='high',
                message=f'Wöchentliche Arbeitszeit überschritten: {total_weekly_hours:.1f}h (max. {self.MAX_WEEKLY_HOURS}h)',
                details={
                    'actual_hours': total_weekly_hours,
                    'limit': self.MAX_WEEKLY_HOURS,
                    'excess_hours': total_weekly_hours - self.MAX_WEEKLY_HOURS,
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    'shifts_count': len(week_shifts)
                },
                timestamp=datetime.now(),
                driver_id=shift_data['driver_id'],
                shift_id=shift_data['id']
            ))
            
        return violations
    
    def _check_weekly_rest_periods(self, week_data: Dict) -> List[WorkTimeViolation]:
        """
        Check rest periods between all shifts in a week
        """
        violations = []
        shifts = sorted(week_data['shifts'], key=lambda x: (x['shift_date'], x['start_time']))
        
        for i in range(1, len(shifts)):
            prev_shift = shifts[i-1]
            curr_shift = shifts[i]
            
            # Use safe datetime parser for consistent handling
            prev_end = self._parse_datetime_safely(prev_shift['shift_date'], prev_shift['end_time'])
            curr_start = self._parse_datetime_safely(curr_shift['shift_date'], curr_shift['start_time'])
            
            # Handle day transitions
            if curr_start <= prev_end:
                curr_start += timedelta(days=1)
                
            rest_hours = (curr_start - prev_end).total_seconds() / 3600
            
            if rest_hours < self.MIN_DAILY_REST:
                violations.append(WorkTimeViolation(
                    violation_type='insufficient_rest_between_shifts',
                    severity='high',
                    message=f'Unzureichende Ruhezeit zwischen Schichten: {rest_hours:.1f}h',
                    details={
                        'actual_rest_hours': rest_hours,
                        'required_rest_hours': self.MIN_DAILY_REST,
                        'previous_shift_id': prev_shift['id'],
                        'current_shift_id': curr_shift['id']
                    },
                    timestamp=datetime.now(),
                    driver_id=week_data['driver_id']
                ))
                
        return violations
    
    def calculate_required_break_time(self, shift_duration_hours: float) -> int:
        """
        Calculate required break time based on shift duration
        """
        if shift_duration_hours >= 9:
            return 45
        elif shift_duration_hours >= 6:
            return 30
        else:
            return 0
    
    def validate_break_distribution(self, shift_id: int) -> List[WorkTimeViolation]:
        """
        Validate that breaks are properly distributed throughout the shift
        """
        violations = []
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT pickup_time, dropoff_time, driver_id
            FROM rides 
            WHERE shift_id = ? 
            ORDER BY pickup_time
        """, (shift_id,))
        
        rides = cursor.fetchall()
        
        if len(rides) < 2:
            return violations
            
        # Check for continuous work periods > 6 hours without break
        continuous_work_start = datetime.fromisoformat(rides[0]['pickup_time'])
        
        for i in range(1, len(rides)):
            prev_end = datetime.fromisoformat(rides[i-1]['dropoff_time'])
            curr_start = datetime.fromisoformat(rides[i]['pickup_time'])
            gap_minutes = (curr_start - prev_end).total_seconds() / 60
            
            # If gap > 15 minutes, consider it a break
            if gap_minutes >= 15:
                # Check if continuous work period was too long
                continuous_hours = (prev_end - continuous_work_start).total_seconds() / 3600
                
                if continuous_hours > 6:
                    violations.append(WorkTimeViolation(
                        violation_type='continuous_work_too_long',
                        severity='high',
                        message=f'Kontinuierliche Arbeitszeit zu lang: {continuous_hours:.1f}h ohne Pause',
                        details={
                            'continuous_hours': continuous_hours,
                            'max_continuous': 6,
                            'work_start': continuous_work_start.isoformat(),
                            'work_end': prev_end.isoformat()
                        },
                        timestamp=datetime.now(),
                        driver_id=rides[0]['driver_id'],
                        shift_id=shift_id
                    ))
                    
                # Reset continuous work counter
                continuous_work_start = curr_start
                
        return violations
    
    def get_driver_weekly_summary(self, driver_id: int, week_start: datetime) -> Dict:
        """
        Get comprehensive weekly summary for a driver
        """
        week_data = self._get_weekly_data(driver_id, week_start)
        violations = self.validate_driver_weekly_compliance(driver_id, week_start)
        
        return {
            'driver_id': driver_id,
            'week_start': week_start.isoformat(),
            'total_hours': sum(s['total_hours'] for s in week_data['shifts']),
            'shifts_count': len(week_data['shifts']),
            'violations': [self._violation_to_dict(v) for v in violations],
            'compliance_rate': self._calculate_compliance_rate(violations),
            'next_available': self._calculate_next_available_time(week_data)
        }
    
    def _get_shift_data(self, shift_id: int) -> Optional[Dict]:
        """Get complete shift data"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM shifts WHERE id = ?
        """, (shift_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def _get_weekly_data(self, driver_id: int, week_start: datetime) -> Dict:
        """Get weekly data for a driver"""
        week_end = week_start + timedelta(days=6)
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM shifts 
            WHERE driver_id = ? 
            AND shift_date BETWEEN ? AND ?
            AND status != 'Cancelled'
            ORDER BY shift_date, start_time
        """, (driver_id, week_start.date().isoformat(), week_end.date().isoformat()))
        
        shifts = []
        for row in cursor.fetchall():
            shift_dict = dict(row)
            
            # Calculate total hours using the safe datetime parser
            try:
                start = self._parse_datetime_safely(shift_dict['shift_date'], shift_dict['start_time'])
                end = self._parse_datetime_safely(shift_dict['shift_date'], shift_dict['end_time'])
                shift_dict['total_hours'] = (end - start).total_seconds() / 3600
            except Exception as e:
                print(f"Error calculating shift hours: {e}")
                shift_dict['total_hours'] = 0
            
            shifts.append(shift_dict)
            
        return {
            'driver_id': driver_id,
            'week_start': week_start,
            'shifts': shifts
        }
    
    def _violation_to_dict(self, violation: WorkTimeViolation) -> Dict:
        """Convert violation to dictionary for JSON serialization"""
        return {
            'type': violation.violation_type,
            'severity': violation.severity,
            'message': violation.message,
            'details': violation.details,
            'timestamp': violation.timestamp.isoformat(),
            'driver_id': violation.driver_id,
            'shift_id': violation.shift_id,
            'ride_id': violation.ride_id
        }
    
    def _calculate_compliance_rate(self, violations: List[WorkTimeViolation]) -> float:
        """Calculate compliance rate based on violations"""
        if not violations:
            return 100.0
            
        # Weight violations by severity
        severity_weights = {'high': 3, 'medium': 2, 'low': 1}
        total_weight = sum(severity_weights[v.severity] for v in violations)
        
        # Calculate compliance (0-100%)
        max_possible_weight = len(violations) * 3  # All high severity
        compliance = max(0, 100 - (total_weight / max_possible_weight * 100))
        
        return round(compliance, 1)
    
    def _calculate_next_available_time(self, week_data: Dict) -> Optional[str]:
        """Calculate when driver will next be available"""
        if not week_data['shifts']:
            return None
            
        last_shift = max(week_data['shifts'], key=lambda x: (x['shift_date'], x['end_time']))
        last_end = datetime.fromisoformat(f"{last_shift['shift_date']} {last_shift['end_time']}")
        
        # Add minimum rest period
        next_available = last_end + timedelta(hours=self.MIN_DAILY_REST)
        
        return next_available.isoformat()

    def store_violation(self, violation: WorkTimeViolation) -> int:
        """Store violation in database and return violation ID"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            INSERT INTO labor_law_violations 
            (driver_id, shift_id, ride_id, violation_type, severity, message, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            violation.driver_id,
            violation.shift_id,
            violation.ride_id,
            violation.violation_type,
            violation.severity,
            violation.message,
            json.dumps(violation.details),
            violation.timestamp.isoformat()
        ))
        
        violation_id = cursor.lastrowid
        self.db.commit()
        return violation_id

    def create_labor_law_tables(self):
        """Create tables for labor law violations tracking"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS labor_law_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                shift_id INTEGER,
                ride_id INTEGER,
                violation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT, -- JSON
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                resolution_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (driver_id) REFERENCES drivers (id),
                FOREIGN KEY (shift_id) REFERENCES shifts (id),
                FOREIGN KEY (ride_id) REFERENCES rides (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_compliance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                week_start TEXT NOT NULL,
                total_hours REAL,
                violations_count INTEGER,
                compliance_rate REAL,
                report_data TEXT, -- JSON
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(driver_id, week_start),
                FOREIGN KEY (driver_id) REFERENCES drivers (id)
            )
        """)
        
        self.db.commit()