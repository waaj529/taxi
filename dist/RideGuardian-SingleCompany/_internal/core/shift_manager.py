import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class ShiftManager:
    """Advanced shift management with conflict detection and revenue preservation"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_shift(self, driver_id: int, shift_date: str, start_time: str, 
                    end_time: str, shift_type: str = "Day") -> Dict:
        """Create a new shift with conflict detection"""
        # Check for vehicle conflicts
        conflicts = self.detect_vehicle_conflicts(driver_id, shift_date, start_time, end_time)
        if conflicts:
            return {
                'success': False,
                'error': 'Vehicle conflict detected',
                'conflicts': conflicts
            }
        
        # Check for driver double booking
        driver_conflicts = self.detect_driver_conflicts(driver_id, shift_date, start_time, end_time)
        if driver_conflicts:
            return {
                'success': False,
                'error': 'Driver already scheduled',
                'conflicts': driver_conflicts
            }
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO shifts (driver_id, shift_date, start_time, end_time, 
                              shift_type, status, start_location)
            VALUES (?, ?, ?, ?, ?, 'Scheduled', 'Headquarters')
        """, (driver_id, shift_date, start_time, end_time, shift_type))
        
        shift_id = cursor.lastrowid
        self.db.commit()
        
        return {
            'success': True,
            'shift_id': shift_id,
            'message': 'Shift created successfully'
        }
    
    def reschedule_shift(self, shift_id: int, new_start_time: str, 
                        new_end_time: str) -> Dict:
        """Reschedule shift with automatic ride and revenue adjustments"""
        cursor = self.db.cursor()
        
        # Get original shift details
        cursor.execute("SELECT * FROM shifts WHERE id = ?", (shift_id,))
        original_shift = cursor.fetchone()
        if not original_shift:
            return {'success': False, 'error': 'Shift not found'}
        
        # Get affected rides
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? AND DATE(pickup_time) = ?
            ORDER BY pickup_time ASC
        """, (original_shift['driver_id'], original_shift['shift_date']))
        
        affected_rides = cursor.fetchall()
        
        # Calculate time difference
        original_start = datetime.fromisoformat(f"{original_shift['shift_date']} {original_shift['start_time']}")
        new_start = datetime.fromisoformat(f"{original_shift['shift_date']} {new_start_time}")
        time_diff = new_start - original_start
        
        # Adjust ride times
        updated_rides = []
        for ride in affected_rides:
            old_pickup = datetime.fromisoformat(ride['pickup_time'])
            new_pickup = old_pickup + time_diff
            
            # Update ride time
            cursor.execute("""
                UPDATE rides SET pickup_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_pickup.isoformat(), ride['id']))
            
            updated_rides.append({
                'ride_id': ride['id'],
                'old_time': old_pickup.isoformat(),
                'new_time': new_pickup.isoformat()
            })
        
        # Update shift
        cursor.execute("""
            UPDATE shifts SET start_time = ?, end_time = ?, 
                            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_start_time, new_end_time, shift_id))
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'Shift rescheduled, {len(updated_rides)} rides adjusted',
            'updated_rides': updated_rides
        }
    
    def reassign_driver(self, shift_id: int, new_driver_id: int) -> Dict:
        """Reassign shift to different driver with revenue preservation"""
        cursor = self.db.cursor()
        
        # Get shift details
        cursor.execute("SELECT * FROM shifts WHERE id = ?", (shift_id,))
        shift = cursor.fetchone()
        if not shift:
            return {'success': False, 'error': 'Shift not found'}
        
        old_driver_id = shift['driver_id']
        
        # Check new driver availability
        conflicts = self.detect_driver_conflicts(
            new_driver_id, shift['shift_date'], 
            shift['start_time'], shift['end_time']
        )
        if conflicts:
            return {
                'success': False,
                'error': 'New driver not available',
                'conflicts': conflicts
            }
        
        # Get vehicle for new driver
        cursor.execute("SELECT vehicle FROM drivers WHERE id = ?", (new_driver_id,))
        new_driver = cursor.fetchone()
        if not new_driver:
            return {'success': False, 'error': 'New driver not found'}
        
        # Check vehicle conflicts
        vehicle_conflicts = self.detect_vehicle_conflicts(
            new_driver_id, shift['shift_date'], 
            shift['start_time'], shift['end_time']
        )
        if vehicle_conflicts:
            return {
                'success': False,
                'error': 'Vehicle conflict for new driver',
                'conflicts': vehicle_conflicts
            }
        
        # Get affected rides
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? AND DATE(pickup_time) = ?
        """, (old_driver_id, shift['shift_date']))
        
        affected_rides = cursor.fetchall()
        total_revenue = sum(ride.get('revenue', 0) or 0 for ride in affected_rides)
        
        # Update shift assignment
        cursor.execute("""
            UPDATE shifts SET driver_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_driver_id, shift_id))
        
        # Update ride assignments
        for ride in affected_rides:
            cursor.execute("""
                UPDATE rides SET driver_id = ?, vehicle_plate = ?,
                               updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_driver_id, new_driver['vehicle'], ride['id']))
        
        # Log revenue transfer
        cursor.execute("""
            INSERT INTO revenue_transfers (
                from_driver_id, to_driver_id, shift_date, 
                amount, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (old_driver_id, new_driver_id, shift['shift_date'], 
              total_revenue, f'Driver reassignment for shift {shift_id}'))
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'Shift reassigned, {len(affected_rides)} rides transferred',
            'revenue_transferred': total_revenue
        }
    
    def reduce_shift_duration(self, shift_id: int, new_end_time: str) -> Dict:
        """Reduce shift duration with automatic adjustments"""
        cursor = self.db.cursor()
        
        # Get shift details
        cursor.execute("SELECT * FROM shifts WHERE id = ?", (shift_id,))
        shift = cursor.fetchone()
        if not shift:
            return {'success': False, 'error': 'Shift not found'}
        
        # Calculate new duration
        start_dt = datetime.fromisoformat(f"{shift['shift_date']} {shift['start_time']}")
        new_end_dt = datetime.fromisoformat(f"{shift['shift_date']} {new_end_time}")
        old_end_dt = datetime.fromisoformat(f"{shift['shift_date']} {shift['end_time']}")
        
        if new_end_dt >= old_end_dt:
            return {'success': False, 'error': 'New end time must be earlier'}
        
        new_duration_hours = (new_end_dt - start_dt).total_seconds() / 3600
        
        # Get rides within new timeframe
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? AND DATE(pickup_time) = ?
            AND TIME(pickup_time) BETWEEN ? AND ?
            ORDER BY pickup_time ASC
        """, (shift['driver_id'], shift['shift_date'], 
              shift['start_time'], new_end_time))
        
        kept_rides = cursor.fetchall()
        
        # Get rides outside new timeframe (to be redistributed)
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? AND DATE(pickup_time) = ?
            AND TIME(pickup_time) > ?
            ORDER BY pickup_time ASC
        """, (shift['driver_id'], shift['shift_date'], new_end_time))
        
        removed_rides = cursor.fetchall()
        removed_revenue = sum(ride.get('revenue', 0) or 0 for ride in removed_rides)
        
        # Redistribute removed rides (mark for manual reassignment)
        for ride in removed_rides:
            cursor.execute("""
                UPDATE rides SET status = 'Needs Reassignment', 
                               notes = 'Removed due to shift reduction',
                               updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (ride['id'],))
        
        # Update shift duration
        cursor.execute("""
            UPDATE shifts SET end_time = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_end_time, shift_id))
        
        # Recalculate breaks for new duration
        break_minutes = 30 if new_duration_hours > 6 else 0
        
        # Log the adjustment
        cursor.execute("""
            INSERT INTO shift_adjustments (
                shift_id, adjustment_type, old_value, new_value,
                affected_rides, revenue_amount, reason, created_at
            ) VALUES (?, 'duration_reduction', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (shift_id, shift['end_time'], new_end_time, 
              len(removed_rides), removed_revenue, 'Manual shift reduction'))
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'Shift reduced by {(old_end_dt - new_end_dt).total_seconds() / 3600:.1f} hours',
            'kept_rides': len(kept_rides),
            'removed_rides': len(removed_rides),
            'redistributed_revenue': removed_revenue,
            'new_break_minutes': break_minutes
        }
    
    def detect_vehicle_conflicts(self, driver_id: int, date: str, 
                               start_time: str, end_time: str) -> List[Dict]:
        """Detect vehicle double usage conflicts"""
        cursor = self.db.cursor()
        
        # Get driver's vehicle
        cursor.execute("SELECT vehicle FROM drivers WHERE id = ?", (driver_id,))
        driver_info = cursor.fetchone()
        if not driver_info or not driver_info['vehicle']:
            return []
        
        vehicle_plate = driver_info['vehicle']
        
        # Check for overlapping shifts with same vehicle
        cursor.execute("""
            SELECT s.*, d.name as driver_name 
            FROM shifts s
            JOIN drivers d ON s.driver_id = d.id
            WHERE d.vehicle = ? AND s.shift_date = ?
            AND s.driver_id != ? AND s.status != 'Cancelled'
            AND (
                (TIME(s.start_time) < TIME(?) AND TIME(s.end_time) > TIME(?)) OR
                (TIME(s.start_time) < TIME(?) AND TIME(s.end_time) > TIME(?)) OR
                (TIME(s.start_time) >= TIME(?) AND TIME(s.end_time) <= TIME(?))
            )
        """, (vehicle_plate, date, driver_id, end_time, start_time, 
              start_time, end_time, start_time, end_time))
        
        conflicts = []
        for conflict in cursor.fetchall():
            conflicts.append({
                'type': 'vehicle_conflict',
                'vehicle': vehicle_plate,
                'conflicting_driver': conflict['driver_name'],
                'conflicting_shift_id': conflict['id'],
                'conflict_time': f"{conflict['start_time']} - {conflict['end_time']}"
            })
        
        return conflicts
    
    def detect_driver_conflicts(self, driver_id: int, date: str, 
                              start_time: str, end_time: str) -> List[Dict]:
        """Detect driver double booking conflicts"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT * FROM shifts 
            WHERE driver_id = ? AND shift_date = ? AND status != 'Cancelled'
            AND (
                (TIME(start_time) < TIME(?) AND TIME(end_time) > TIME(?)) OR
                (TIME(start_time) < TIME(?) AND TIME(end_time) > TIME(?)) OR
                (TIME(start_time) >= TIME(?) AND TIME(end_time) <= TIME(?))
            )
        """, (driver_id, date, end_time, start_time, start_time, end_time, 
              start_time, end_time))
        
        conflicts = []
        for conflict in cursor.fetchall():
            conflicts.append({
                'type': 'driver_conflict',
                'existing_shift_id': conflict['id'],
                'conflict_time': f"{conflict['start_time']} - {conflict['end_time']}"
            })
        
        return conflicts
    
    def get_shift_summary(self, shift_id: int) -> Dict:
        """Get comprehensive shift summary with metrics"""
        cursor = self.db.cursor()
        
        # Get shift details
        cursor.execute("""
            SELECT s.*, d.name as driver_name, d.vehicle
            FROM shifts s
            JOIN drivers d ON s.driver_id = d.id
            WHERE s.id = ?
        """, (shift_id,))
        
        shift = cursor.fetchone()
        if not shift:
            return {'error': 'Shift not found'}
        
        # Get ride statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rides,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_rides,
                SUM(CASE WHEN violations IS NOT NULL AND violations != '[]' THEN 1 ELSE 0 END) as violation_rides,
                SUM(COALESCE(revenue, 0)) as total_revenue,
                AVG(COALESCE(distance_km, 0)) as avg_distance,
                AVG(COALESCE(duration_minutes, 0)) as avg_duration
            FROM rides 
            WHERE driver_id = ? AND DATE(pickup_time) = ?
        """, (shift['driver_id'], shift['shift_date']))
        
        ride_stats = cursor.fetchone()
        
        # Calculate shift duration
        start_dt = datetime.fromisoformat(f"{shift['shift_date']} {shift['start_time']}")
        end_dt = datetime.fromisoformat(f"{shift['shift_date']} {shift['end_time']}")
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        
        # Calculate compliance rate
        compliance_rate = 0
        if ride_stats['total_rides'] > 0:
            compliant_rides = ride_stats['total_rides'] - ride_stats['violation_rides']
            compliance_rate = (compliant_rides / ride_stats['total_rides']) * 100
        
        return {
            'shift_id': shift_id,
            'driver_name': shift['driver_name'],
            'vehicle': shift['vehicle'],
            'date': shift['shift_date'],
            'start_time': shift['start_time'],
            'end_time': shift['end_time'],
            'duration_hours': round(duration_hours, 2),
            'status': shift['status'],
            'total_rides': ride_stats['total_rides'],
            'completed_rides': ride_stats['completed_rides'],
            'violation_rides': ride_stats['violation_rides'],
            'compliance_rate': round(compliance_rate, 1),
            'total_revenue': ride_stats['total_revenue'] or 0,
            'avg_distance_km': round(ride_stats['avg_distance'] or 0, 2),
            'avg_duration_minutes': round(ride_stats['avg_duration'] or 0, 1),
            'revenue_per_hour': round((ride_stats['total_revenue'] or 0) / duration_hours, 2) if duration_hours > 0 else 0
        }
    
    def create_shift_adjustment_tables(self):
        """Create additional tables for shift management"""
        cursor = self.db.cursor()
        
        # Revenue transfers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revenue_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_driver_id INTEGER,
                to_driver_id INTEGER,
                shift_date TEXT,
                amount REAL,
                reason TEXT,
                created_at TEXT,
                FOREIGN KEY (from_driver_id) REFERENCES drivers (id),
                FOREIGN KEY (to_driver_id) REFERENCES drivers (id)
            )
        """)
        
        # Shift adjustments log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shift_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER,
                adjustment_type TEXT, -- duration_reduction, reassignment, etc.
                old_value TEXT,
                new_value TEXT,
                affected_rides INTEGER,
                revenue_amount REAL,
                reason TEXT,
                created_at TEXT,
                FOREIGN KEY (shift_id) REFERENCES shifts (id)
            )
        """)
        
        self.db.commit()