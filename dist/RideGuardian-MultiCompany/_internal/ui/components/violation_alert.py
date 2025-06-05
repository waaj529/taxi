"""
Violation Alert Component
Shows real-time rule violations with clear visual feedback
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime
from typing import Dict, List, Optional
from core.translation_manager import tr


class ViolationItem(QFrame):
    """Individual violation display item"""
    
    dismissed = pyqtSignal(str)  # Signal with violation ID
    
    def __init__(self, violation_data: Dict, parent=None):
        super().__init__(parent)
        self.violation_id = violation_data.get('id', str(datetime.now().timestamp()))
        self.violation_data = violation_data
        self.init_ui()
        
    def init_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #fff5f5;
                border: 2px solid #dc3545;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with icon and time
        header_layout = QHBoxLayout()
        
        # Warning icon
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        # Violation type and time
        info_layout = QVBoxLayout()
        
        type_label = QLabel(self.get_violation_type())
        type_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        type_label.setStyleSheet("color: #dc3545;")
        info_layout.addWidget(type_label)
        
        time_label = QLabel(self.format_time())
        time_label.setStyleSheet("color: #666; font-size: 9px;")
        info_layout.addWidget(time_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        # Dismiss button
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setFixedSize(20, 20)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #dc3545;
            }
        """)
        dismiss_btn.clicked.connect(lambda: self.dismissed.emit(self.violation_id))
        header_layout.addWidget(dismiss_btn)
        
        layout.addLayout(header_layout)
        
        # Violation details
        details_label = QLabel(self.get_violation_details())
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #333; margin-top: 5px;")
        layout.addWidget(details_label)
        
        # Driver and ride info
        if 'driver_name' in self.violation_data:
            driver_label = QLabel(f"{tr('Driver')}: {self.violation_data['driver_name']}")
            driver_label.setStyleSheet("color: #666; font-size: 9px; margin-top: 5px;")
            layout.addWidget(driver_label)
            
    def get_violation_type(self) -> str:
        """Get localized violation type"""
        violation_type = self.violation_data.get('type', 'Unknown')
        type_mapping = {
            'distance_pickup': tr("Distance Rule Violation"),
            'distance_next_job': tr("Next Job Distance Violation"),
            'hq_deviation': tr("HQ Route Deviation"),
            'time_tolerance': tr("Time Violation"),
            'shift_start': tr("Shift Start Violation")
        }
        return type_mapping.get(violation_type, violation_type)
        
    def get_violation_details(self) -> str:
        """Get detailed violation message"""
        message = self.violation_data.get('message', '')
        if not message:
            violation_type = self.violation_data.get('type', '')
            if violation_type == 'distance_pickup':
                return tr("Rule 2 violated - Distance to pickup exceeds limit")
            elif violation_type == 'distance_next_job':
                return tr("Rule 3 violated - Next job distance exceeds limit")
            elif violation_type == 'hq_deviation':
                return tr("Rule 4 violated - Deviation from HQ route exceeds limit")
            elif violation_type == 'time_tolerance':
                return tr("Time tolerance exceeded")
            elif violation_type == 'shift_start':
                return tr("Rule 1 violated - Shift did not start at headquarters")
        return message
        
    def format_time(self) -> str:
        """Format violation time"""
        timestamp = self.violation_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                timestamp = datetime.now()
        return timestamp.strftime("%H:%M:%S")


class ViolationAlertWidget(QWidget):
    """Widget for displaying multiple violation alerts"""
    
    violation_clicked = pyqtSignal(dict)  # Signal when violation is clicked
    
    def __init__(self, parent=None, max_visible: int = 5):
        super().__init__(parent)
        self.max_visible = max_visible
        self.violations: Dict[str, ViolationItem] = {}
        self.init_ui()
        
        # Auto-dismiss old violations after 5 minutes
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_violations)
        self.cleanup_timer.start(60000)  # Check every minute
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(tr("Active Violations"))
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        # Clear all button
        self.clear_btn = QPushButton(tr("Clear All"))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all_violations)
        self.clear_btn.hide()
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for violations
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container for violation items
        self.violations_container = QWidget()
        self.violations_layout = QVBoxLayout(self.violations_container)
        self.violations_layout.setContentsMargins(0, 0, 0, 0)
        self.violations_layout.addStretch()
        
        scroll_area.setWidget(self.violations_container)
        main_layout.addWidget(scroll_area)
        
        # No violations message
        self.no_violations_label = QLabel(tr("No active violations"))
        self.no_violations_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_violations_label.setStyleSheet("color: #666; padding: 20px;")
        self.violations_layout.insertWidget(0, self.no_violations_label)
        
    def add_violation(self, violation_data: Dict):
        """Add a new violation alert"""
        violation_id = violation_data.get('id', str(datetime.now().timestamp()))
        
        # Don't add duplicate violations
        if violation_id in self.violations:
            return
            
        # Create violation item
        violation_item = ViolationItem(violation_data)
        violation_item.dismissed.connect(self.remove_violation)
        violation_item.mouseReleaseEvent = lambda e: self.violation_clicked.emit(violation_data)
        
        # Add to layout (insert at top)
        self.violations_layout.insertWidget(0, violation_item)
        self.violations[violation_id] = violation_item
        
        # Hide no violations message
        self.no_violations_label.hide()
        
        # Show clear button if we have violations
        if len(self.violations) > 0:
            self.clear_btn.show()
            
        # Update count
        self.update_count()
        
        # Animate appearance
        self.animate_appearance(violation_item)
        
        # Remove oldest if exceeding max
        if len(self.violations) > self.max_visible:
            self.remove_oldest_violation()
            
    def remove_violation(self, violation_id: str):
        """Remove a specific violation"""
        if violation_id in self.violations:
            violation_item = self.violations[violation_id]
            
            # Animate removal
            self.animate_removal(violation_item)
            
            # Remove from dict
            del self.violations[violation_id]
            
            # Update UI
            self.update_count()
            
            # Show no violations message if empty
            if len(self.violations) == 0:
                self.no_violations_label.show()
                self.clear_btn.hide()
                
    def clear_all_violations(self):
        """Clear all violations"""
        for violation_id in list(self.violations.keys()):
            self.remove_violation(violation_id)
            
    def cleanup_old_violations(self):
        """Remove violations older than 5 minutes"""
        current_time = datetime.now()
        for violation_id, violation_item in list(self.violations.items()):
            timestamp = violation_item.violation_data.get('timestamp', current_time)
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    continue
                    
            if (current_time - timestamp).seconds > 300:  # 5 minutes
                self.remove_violation(violation_id)
                
    def remove_oldest_violation(self):
        """Remove the oldest violation"""
        if not self.violations:
            return
            
        oldest_id = min(self.violations.keys())
        self.remove_violation(oldest_id)
        
    def update_count(self):
        """Update violation count display"""
        count = len(self.violations)
        self.count_label.setText(f"({count})")
        
        # Change color based on count
        if count == 0:
            self.count_label.setStyleSheet("color: #28a745;")
        elif count < 3:
            self.count_label.setStyleSheet("color: #ffc107;")
        else:
            self.count_label.setStyleSheet("color: #dc3545;")
            
    def animate_appearance(self, widget: QWidget):
        """Animate widget appearance"""
        widget.setMaximumHeight(0)
        animation = QPropertyAnimation(widget, b"maximumHeight")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(200)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
    def animate_removal(self, widget: QWidget):
        """Animate widget removal"""
        animation = QPropertyAnimation(widget, b"maximumHeight")
        animation.setDuration(300)
        animation.setStartValue(widget.height())
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        animation.finished.connect(widget.deleteLater)
        animation.start()
        
    def get_active_violations(self) -> List[Dict]:
        """Get list of active violations"""
        return [item.violation_data for item in self.violations.values()] 