"""
Real-time Labor Law Violation Monitor
Provides live monitoring and alerts for German labor law compliance
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QGroupBox, QProgressBar
from PyQt6.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from core.enhanced_ride_validator import EnhancedRideValidator
from core.labor_law_validator import GermanLaborLawValidator
from core.database import get_db_connection

class LaborLawMonitorWidget(QWidget):
    """
    Real-time monitoring widget for German labor law compliance
    """
    
    violation_detected = pyqtSignal(dict)  # Signal when new violation is detected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db_connection()
        self.validator = EnhancedRideValidator(self.db)
        self.labor_validator = GermanLaborLawValidator(self.db)
        
        self.init_ui()
        self.setup_monitoring()
        
    def init_ui(self):
        """Initialize the monitoring UI"""
        layout = QVBoxLayout()
        
        # Header with current status
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🚨 Arbeitszeitrecht Monitor")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        # Status indicator
        self.status_label = QLabel("🟢 Konform")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #27ae60;")
        header_layout.addWidget(self.status_label)
        
        # Last update time
        self.last_update_label = QLabel(f"Letztes Update: {datetime.now().strftime('%H:%M:%S')}")
        self.last_update_label.setStyleSheet("color: #bdc3c7;")
        header_layout.addWidget(self.last_update_label)
        
        layout.addWidget(header_frame)
        
        # Current violations panel
        violations_group = QGroupBox("🔴 Aktuelle Verstöße")
        violations_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #e74c3c;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.violations_layout = QVBoxLayout(violations_group)
        self.violations_scroll = QScrollArea()
        self.violations_scroll.setWidgetResizable(True)
        self.violations_scroll.setMaximumHeight(200)
        
        self.violations_content = QWidget()
        self.violations_content_layout = QVBoxLayout(self.violations_content)
        self.violations_scroll.setWidget(self.violations_content)
        self.violations_layout.addWidget(self.violations_scroll)
        
        layout.addWidget(violations_group)
        
        # Driver status overview
        status_group = QGroupBox("👥 Fahrer Status Übersicht")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        self.status_layout = QVBoxLayout(status_group)
        self.driver_status_area = QScrollArea()
        self.driver_status_area.setWidgetResizable(True)
        self.driver_status_area.setMaximumHeight(300)
        
        self.driver_status_content = QWidget()
        self.driver_status_content_layout = QVBoxLayout(self.driver_status_content)
        self.driver_status_area.setWidget(self.driver_status_content)
        self.status_layout.addWidget(self.driver_status_area)
        
        layout.addWidget(status_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_monitoring)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.generate_report_btn = QPushButton("📊 Bericht erstellen")
        self.generate_report_btn.clicked.connect(self.generate_compliance_report)
        self.generate_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.generate_report_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def setup_monitoring(self):
        """Setup real-time monitoring timer"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_violations)
        self.monitor_timer.start(30000)  # Check every 30 seconds
        
        # Initial check
        self.check_violations()
        
    @pyqtSlot()
    def check_violations(self):
        """Check for current violations and update display"""
        try:
            current_violations = self._get_current_violations()
            driver_statuses = self._get_driver_statuses()
            
            self._update_violations_display(current_violations)
            self._update_driver_status_display(driver_statuses)
            self._update_overall_status(current_violations)
            
            self.last_update_label.setText(f"Letztes Update: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error checking violations: {e}")
            
    def _get_current_violations(self) -> List[Dict]:
        """Get all current unresolved violations"""
        cursor = self.db.cursor()
        
        # Get recent labor law violations (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        
        cursor.execute("""
            SELECT llv.*, d.name as driver_name
            FROM labor_law_violations llv
            JOIN drivers d ON llv.driver_id = d.id
            WHERE llv.timestamp >= ?
            AND llv.resolved = 0
            ORDER BY llv.timestamp DESC
        """, (yesterday.isoformat(),))
        
        violations = []
        for row in cursor.fetchall():
            violations.append({
                'id': row['id'],
                'type': row['violation_type'],
                'severity': row['severity'],
                'message': row['message'],
                'driver_name': row['driver_name'],
                'driver_id': row['driver_id'],
                'timestamp': row['timestamp'],
                'details': json.loads(row['details']) if row['details'] else {}
            })
            
        return violations
    
    def _get_driver_statuses(self) -> List[Dict]:
        """Get current status of all active drivers"""
        cursor = self.db.cursor()
        
        # Get all active drivers and their current status
        cursor.execute("""
            SELECT d.id, d.name, d.status
            FROM drivers d
            WHERE d.status = 'Active'
            ORDER BY d.name
        """)
        
        drivers = cursor.fetchall()
        driver_statuses = []
        
        today = datetime.now().date()
        
        for driver in drivers:
            # Get today's shifts
            cursor.execute("""
                SELECT start_time, end_time, status
                FROM shifts
                WHERE driver_id = ? AND shift_date = ?
                ORDER BY start_time DESC
                LIMIT 1
            """, (driver['id'], today.isoformat()))
            
            current_shift = cursor.fetchone()
            
            # Calculate current status
            status_info = self._calculate_driver_current_status(driver['id'], current_shift)
            
            driver_statuses.append({
                'driver_id': driver['id'],
                'name': driver['name'],
                'current_shift': current_shift,
                'status_info': status_info
            })
            
        return driver_statuses
    
    def _calculate_driver_current_status(self, driver_id: int, current_shift: Dict) -> Dict:
        """Calculate comprehensive status for a driver"""
        now = datetime.now()
        status = {
            'work_status': 'Inaktiv',
            'hours_today': 0,
            'hours_this_week': 0,
            'last_break': None,
            'next_required_break': None,
            'compliance_status': 'OK',
            'warnings': []
        }
        
        if current_shift:
            shift_start = datetime.fromisoformat(f"{now.date()} {current_shift['start_time']}")
            
            if current_shift['status'] == 'Active':
                # Driver is currently working
                hours_worked = (now - shift_start).total_seconds() / 3600
                status['work_status'] = 'Aktiv'
                status['hours_today'] = round(hours_worked, 1)
                
                # Check for break requirements
                if hours_worked >= 6:
                    required_break = 30 if hours_worked < 9 else 45
                    status['next_required_break'] = f"{required_break} Min Pause erforderlich"
                    
                    # Check if break has been taken
                    if not self._has_taken_required_break(driver_id, shift_start, hours_worked):
                        status['warnings'].append(f"Pausenpflicht: {required_break} Min erforderlich")
                        status['compliance_status'] = 'WARNUNG'
                
                # Check maximum shift duration
                if hours_worked >= 10:
                    status['warnings'].append("Maximale Schichtdauer (10h) erreicht!")
                    status['compliance_status'] = 'KRITISCH'
        
        # Calculate weekly hours
        week_start = now - timedelta(days=now.weekday())
        weekly_hours = self._get_weekly_hours(driver_id, week_start)
        status['hours_this_week'] = round(weekly_hours, 1)
        
        if weekly_hours >= 60:
            status['warnings'].append("Wöchentliche Arbeitszeit (60h) überschritten!")
            status['compliance_status'] = 'KRITISCH'
        elif weekly_hours >= 55:
            status['warnings'].append("Wöchentliche Arbeitszeit nähert sich Limit")
            if status['compliance_status'] == 'OK':
                status['compliance_status'] = 'WARNUNG'
        
        return status
    
    def _has_taken_required_break(self, driver_id: int, shift_start: datetime, hours_worked: float) -> bool:
        """Check if driver has taken required break during current shift"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT pickup_time, dropoff_time
            FROM rides
            WHERE driver_id = ? 
            AND pickup_time >= ?
            ORDER BY pickup_time
        """, (driver_id, shift_start.isoformat()))
        
        rides = cursor.fetchall()
        
        if len(rides) < 2:
            return False
            
        # Look for gaps >= 15 minutes
        total_break_time = 0
        for i in range(1, len(rides)):
            prev_end = datetime.fromisoformat(rides[i-1]['dropoff_time'])
            curr_start = datetime.fromisoformat(rides[i]['pickup_time'])
            gap_minutes = (curr_start - prev_end).total_seconds() / 60
            
            if gap_minutes >= 15:
                total_break_time += gap_minutes
                
        required_break = 30 if hours_worked < 9 else 45
        return total_break_time >= required_break
    
    def _get_weekly_hours(self, driver_id: int, week_start: datetime) -> float:
        """Get total hours worked this week"""
        cursor = self.db.cursor()
        week_end = week_start + timedelta(days=6)
        
        cursor.execute("""
            SELECT start_time, end_time, shift_date
            FROM shifts
            WHERE driver_id = ?
            AND shift_date BETWEEN ? AND ?
            AND status != 'Cancelled'
        """, (driver_id, week_start.date().isoformat(), week_end.date().isoformat()))
        
        shifts = cursor.fetchall()
        total_hours = 0
        
        for shift in shifts:
            start = datetime.fromisoformat(f"{shift['shift_date']} {shift['start_time']}")
            end = datetime.fromisoformat(f"{shift['shift_date']} {shift['end_time']}")
            hours = (end - start).total_seconds() / 3600
            total_hours += hours
            
        return total_hours
    
    def _update_violations_display(self, violations: List[Dict]):
        """Update the violations display panel"""
        # Clear existing violations
        for i in reversed(range(self.violations_content_layout.count())):
            child = self.violations_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        if not violations:
            no_violations_label = QLabel("✅ Keine aktuellen Verstöße")
            no_violations_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px;")
            self.violations_content_layout.addWidget(no_violations_label)
        else:
            for violation in violations:
                violation_widget = self._create_violation_widget(violation)
                self.violations_content_layout.addWidget(violation_widget)
                
    def _create_violation_widget(self, violation: Dict) -> QWidget:
        """Create a widget for displaying a single violation"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {'#e74c3c' if violation['severity'] == 'high' else '#f39c12' if violation['severity'] == 'medium' else '#f1c40f'};
                border-radius: 5px;
                margin: 2px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        
        # Header with severity and driver
        header_layout = QHBoxLayout()
        
        severity_icon = "🔴" if violation['severity'] == 'high' else "🟡" if violation['severity'] == 'medium' else "🟢"
        severity_label = QLabel(f"{severity_icon} {violation['severity'].upper()}")
        severity_label.setStyleSheet("color: white; font-weight: bold;")
        
        driver_label = QLabel(f"Fahrer: {violation['driver_name']}")
        driver_label.setStyleSheet("color: white; font-weight: bold;")
        
        time_label = QLabel(datetime.fromisoformat(violation['timestamp']).strftime("%H:%M"))
        time_label.setStyleSheet("color: white;")
        
        header_layout.addWidget(severity_label)
        header_layout.addWidget(driver_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(violation['message'])
        message_label.setStyleSheet("color: white; font-size: 12px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Resolve button
        resolve_btn = QPushButton("✅ Beheben")
        resolve_btn.clicked.connect(lambda: self._resolve_violation(violation['id']))
        resolve_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        layout.addWidget(resolve_btn)
        
        return widget
    
    def _update_driver_status_display(self, driver_statuses: List[Dict]):
        """Update the driver status overview"""
        # Clear existing status widgets
        for i in reversed(range(self.driver_status_content_layout.count())):
            child = self.driver_status_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        for driver_status in driver_statuses:
            status_widget = self._create_driver_status_widget(driver_status)
            self.driver_status_content_layout.addWidget(status_widget)
            
    def _create_driver_status_widget(self, driver_status: Dict) -> QWidget:
        """Create a widget for displaying driver status"""
        widget = QFrame()
        status_info = driver_status['status_info']
        
        # Color coding based on compliance status
        bg_color = {
            'OK': '#27ae60',
            'WARNUNG': '#f39c12', 
            'KRITISCH': '#e74c3c'
        }.get(status_info['compliance_status'], '#7f8c8d')
        
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 5px;
                margin: 2px;
                padding: 6px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        
        # Driver name and status
        header_layout = QHBoxLayout()
        name_label = QLabel(f"👤 {driver_status['name']}")
        name_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        
        work_status_label = QLabel(status_info['work_status'])
        work_status_label.setStyleSheet("color: white; font-size: 10px;")
        
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(work_status_label)
        layout.addLayout(header_layout)
        
        # Hours worked
        hours_layout = QHBoxLayout()
        today_hours = QLabel(f"Heute: {status_info['hours_today']}h")
        today_hours.setStyleSheet("color: white; font-size: 10px;")
        
        week_hours = QLabel(f"Woche: {status_info['hours_this_week']}h")
        week_hours.setStyleSheet("color: white; font-size: 10px;")
        
        hours_layout.addWidget(today_hours)
        hours_layout.addWidget(week_hours)
        layout.addLayout(hours_layout)
        
        # Warnings
        if status_info['warnings']:
            for warning in status_info['warnings']:
                warning_label = QLabel(f"⚠️ {warning}")
                warning_label.setStyleSheet("color: white; font-size: 9px;")
                warning_label.setWordWrap(True)
                layout.addWidget(warning_label)
                
        return widget
    
    def _update_overall_status(self, violations: List[Dict]):
        """Update the overall system status"""
        if not violations:
            self.status_label.setText("🟢 Konform")
            self.status_label.setStyleSheet("color: #27ae60;")
        else:
            high_severity = any(v['severity'] == 'high' for v in violations)
            if high_severity:
                self.status_label.setText("🔴 Kritische Verstöße")
                self.status_label.setStyleSheet("color: #e74c3c;")
            else:
                self.status_label.setText("🟡 Verstöße erkannt")
                self.status_label.setStyleSheet("color: #f39c12;")
                
    def _resolve_violation(self, violation_id: int):
        """Mark a violation as resolved"""
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE labor_law_violations 
            SET resolved = 1, resolution_notes = 'Manuell behoben'
            WHERE id = ?
        """, (violation_id,))
        self.db.commit()
        
        # Refresh display
        self.check_violations()
        
    @pyqtSlot()
    def refresh_monitoring(self):
        """Manually refresh the monitoring display"""
        self.check_violations()
        
    @pyqtSlot()
    def generate_compliance_report(self):
        """Generate and display compliance report"""
        report = self.validator.generate_compliance_report(period_days=7)
        
        # You could show this in a dialog or export to file
        print("Compliance Report Generated:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
        # Emit signal that report is ready
        self.violation_detected.emit({'type': 'report_generated', 'data': report})