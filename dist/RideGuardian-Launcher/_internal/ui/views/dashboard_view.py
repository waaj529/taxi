import os
import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QComboBox,
    QDateEdit, QDialog, QFormLayout, QTextEdit, QSpinBox, QDoubleSpinBox,
    QDialogButtonBox, QHeaderView, QGroupBox, QGridLayout, QCheckBox,
    QProgressBar, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection
from core.translation_manager import TranslationManager

class DatabaseClearThread(QThread):
    """Thread for clearing database operations"""
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, operation_type):
        super().__init__()
        self.operation_type = operation_type
    
    def run(self):
        try:
            from core.database import get_db_connection
            db = get_db_connection()
            cursor = db.cursor()
            
            self.progress.emit(10)
            self.status_update.emit("Starting database operation...")
            
            if self.operation_type == "clear_rides":
                cursor.execute("DELETE FROM rides")
                self.status_update.emit("Clearing rides...")
            elif self.operation_type == "clear_drivers":
                cursor.execute("DELETE FROM drivers")
                self.status_update.emit("Clearing drivers...")
            elif self.operation_type == "clear_all":
                cursor.execute("DELETE FROM rides")
                self.progress.emit(30)
                cursor.execute("DELETE FROM drivers")
                self.progress.emit(60)
                cursor.execute("DELETE FROM address_cache")
                self.status_update.emit("Clearing all data...")
            
            self.progress.emit(90)
            db.commit()
            db.close()
            
            self.progress.emit(100)
            self.finished_signal.emit(True, "Database operation completed successfully")
            
        except Exception as e:
            self.finished_signal.emit(False, f"Database operation failed: {str(e)}")

class RideEditDialog(QDialog):
    """Dialog for adding/editing rides"""
    
    def __init__(self, parent=None, ride_data=None):
        super().__init__(parent)
        self.ride_data = ride_data
        self.is_edit_mode = ride_data is not None
        self.tm = TranslationManager()
        
        self.setWindowTitle(self.tm.tr("edit_ride") if self.is_edit_mode else self.tm.tr("add_new_ride"))
        self.setModal(True)
        self.resize(500, 600)
        
        self.init_ui()
        self.load_drivers()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Driver selection
        self.driver_combo = QComboBox()
        form_layout.addRow(f"{self.tm.tr('driver')}:", self.driver_combo)
        
        # Pickup date and time
        self.pickup_date = QDateEdit()
        self.pickup_date.setDate(QDate.currentDate())
        self.pickup_date.setCalendarPopup(True)
        form_layout.addRow(f"{self.tm.tr('pickup_date')}:", self.pickup_date)
        
        self.pickup_time = QLineEdit()
        self.pickup_time.setPlaceholderText("HH:MM")
        form_layout.addRow(f"{self.tm.tr('pickup_time')}:", self.pickup_time)
        
        # Dropoff date and time
        self.dropoff_date = QDateEdit()
        self.dropoff_date.setDate(QDate.currentDate())
        self.dropoff_date.setCalendarPopup(True)
        form_layout.addRow(f"{self.tm.tr('dropoff_date')}:", self.dropoff_date)
        
        # Locations
        self.pickup_location = QLineEdit()
        self.pickup_location.setPlaceholderText(self.tm.tr("pickup_address"))
        form_layout.addRow(f"{self.tm.tr('pickup_location')}:", self.pickup_location)
        
        self.destination = QLineEdit()
        self.destination.setPlaceholderText(self.tm.tr("destination_address"))
        form_layout.addRow(f"{self.tm.tr('destination')}:", self.destination)
        
        # Distance and duration
        self.distance_km = QDoubleSpinBox()
        self.distance_km.setRange(0, 1000)
        self.distance_km.setDecimals(2)
        self.distance_km.setSuffix(" km")
        form_layout.addRow(f"{self.tm.tr('distance')}:", self.distance_km)
        
        self.duration_minutes = QSpinBox()
        self.duration_minutes.setRange(0, 1440)  # Max 24 hours
        self.duration_minutes.setSuffix(f" {self.tm.tr('minutes')}")
        form_layout.addRow(f"{self.tm.tr('duration')}:", self.duration_minutes)
        
        # Revenue
        self.revenue = QDoubleSpinBox()
        self.revenue.setRange(0, 10000)
        self.revenue.setDecimals(2)
        self.revenue.setPrefix("€")
        form_layout.addRow(f"{self.tm.tr('revenue')}:", self.revenue)
        
        # Status
        self.status = QComboBox()
        self.status.addItems([
            self.tm.tr("completed"),
            self.tm.tr("cancelled"),
            self.tm.tr("in_progress")
        ])
        form_layout.addRow(f"{self.tm.tr('status')}:", self.status)
        
        # Vehicle plate
        self.vehicle_plate = QLineEdit()
        self.vehicle_plate.setPlaceholderText(self.tm.tr("vehicle_plate"))
        form_layout.addRow(f"{self.tm.tr('vehicle_plate')}:", self.vehicle_plate)
        
        # Violations
        self.violations = QTextEdit()
        self.violations.setPlaceholderText(self.tm.tr("violations_description"))
        self.violations.setMaximumHeight(80)
        form_layout.addRow(f"{self.tm.tr('violations')}:", self.violations)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.tm.tr("save"))
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tm.tr("cancel"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_drivers(self):
        try:
            from core.database import get_db_connection
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT id, name FROM drivers WHERE status = 'Active' ORDER BY name")
            drivers = cursor.fetchall()
            
            self.driver_combo.clear()
            self.driver_combo.addItem(self.tm.tr("select_driver"), None)
            
            for driver in drivers:
                self.driver_combo.addItem(driver['name'], driver['id'])
            
            db.close()
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"Failed to load drivers: {str(e)}")
    
    def populate_fields(self):
        if not self.ride_data:
            return
        
        # Set driver
        driver_id = self.ride_data.get('driver_id')
        for i in range(self.driver_combo.count()):
            if self.driver_combo.itemData(i) == driver_id:
                self.driver_combo.setCurrentIndex(i)
                break
        
        # Set dates and times
        pickup_datetime = datetime.fromisoformat(self.ride_data.get('pickup_time', ''))
        self.pickup_date.setDate(QDate.fromString(pickup_datetime.date().isoformat(), "yyyy-MM-dd"))
        self.pickup_time.setText(pickup_datetime.time().strftime("%H:%M"))
        
        dropoff_datetime = datetime.fromisoformat(self.ride_data.get('dropoff_time', ''))
        self.dropoff_date.setDate(QDate.fromString(dropoff_datetime.date().isoformat(), "yyyy-MM-dd"))
        self.dropoff_time.setText(dropoff_datetime.time().strftime("%H:%M"))
        
        # Set other fields
        self.pickup_location.setText(self.ride_data.get('pickup_location', ''))
        self.destination.setText(self.ride_data.get('destination', ''))
        self.distance_km.setValue(self.ride_data.get('distance_km', 0))
        self.duration_minutes.setValue(self.ride_data.get('duration_minutes', 0))
        self.revenue.setValue(self.ride_data.get('revenue', 0))
        self.vehicle_plate.setText(self.ride_data.get('vehicle_plate', ''))
        self.violations.setPlainText(self.ride_data.get('violations', '[]'))
        
        # Set status - map from English to German
        status_map = {
            "Completed": self.tm.tr("completed"),
            "Cancelled": self.tm.tr("cancelled"),
            "In Progress": self.tm.tr("in_progress")
        }
        english_status = self.ride_data.get('status', 'Completed')
        german_status = status_map.get(english_status, english_status)
        index = self.status.findText(german_status)
        if index >= 0:
            self.status.setCurrentIndex(index)
    
    def get_ride_data(self):
        try:
            # Combine date and time
            pickup_date = self.pickup_date.date().toString("yyyy-MM-dd")
            pickup_time = self.pickup_time.text()
            pickup_datetime = f"{pickup_date} {pickup_time}:00"
            
            dropoff_date = self.dropoff_date.date().toString("yyyy-MM-dd")
            dropoff_time = self.dropoff_time.text()
            dropoff_datetime = f"{dropoff_date} {dropoff_time}:00"
            
            # Validate datetime format
            datetime.fromisoformat(pickup_datetime)
            datetime.fromisoformat(dropoff_datetime)
            
            # Map German status back to English for database
            status_reverse_map = {
                self.tm.tr("completed"): "Completed",
                self.tm.tr("cancelled"): "Cancelled",
                self.tm.tr("in_progress"): "In Progress"
            }
            german_status = self.status.currentText()
            english_status = status_reverse_map.get(german_status, german_status)
            
            return {
                'driver_id': self.driver_combo.currentData(),
                'pickup_time': pickup_datetime,
                'dropoff_time': dropoff_datetime,
                'pickup_location': self.pickup_location.text(),
                'destination': self.destination.text(),
                'distance_km': self.distance_km.value(),
                'duration_minutes': self.duration_minutes.value(),
                'revenue': self.revenue.value(),
                'status': english_status,
                'vehicle_plate': self.vehicle_plate.text(),
                'violations': self.violations.toPlainText()
            }
        except Exception as e:
            raise ValueError(f"{self.tm.tr('invalid_data_format')}: {str(e)}")

class DriverEditDialog(QDialog):
    """Dialog for adding/editing drivers"""
    
    def __init__(self, parent=None, driver_data=None):
        super().__init__(parent)
        self.driver_data = driver_data
        self.is_edit_mode = driver_data is not None
        self.tm = TranslationManager()
        
        self.setWindowTitle(self.tm.tr("edit_driver") if self.is_edit_mode else self.tm.tr("add_new_driver"))
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name = QLineEdit()
        self.name.setPlaceholderText(self.tm.tr("driver_name"))
        form_layout.addRow(f"{self.tm.tr('name')}:", self.name)
        
        self.vehicle = QLineEdit()
        self.vehicle.setPlaceholderText(self.tm.tr("vehicle_description"))
        form_layout.addRow(f"{self.tm.tr('vehicle')}:", self.vehicle)
        
        self.status = QComboBox()
        self.status.addItems([
            self.tm.tr("active"),
            self.tm.tr("inactive"),
            self.tm.tr("suspended")
        ])
        form_layout.addRow(f"{self.tm.tr('status')}:", self.status)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.tm.tr("save"))
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tm.tr("cancel"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_fields(self):
        if not self.driver_data:
            return
        
        self.name.setText(self.driver_data.get('name', ''))
        self.vehicle.setText(self.driver_data.get('vehicle', ''))
        
        # Map English status to German
        status_map = {
            "Active": self.tm.tr("active"),
            "Inactive": self.tm.tr("inactive"),
            "Suspended": self.tm.tr("suspended")
        }
        english_status = self.driver_data.get('status', 'Active')
        german_status = status_map.get(english_status, english_status)
        index = self.status.findText(german_status)
        if index >= 0:
            self.status.setCurrentIndex(index)
    
    def get_driver_data(self):
        # Map German status back to English for database
        status_reverse_map = {
            self.tm.tr("active"): "Active",
            self.tm.tr("inactive"): "Inactive",
            self.tm.tr("suspended"): "Suspended"
        }
        german_status = self.status.currentText()
        english_status = status_reverse_map.get(german_status, german_status)
        
        return {
            'name': self.name.text().strip(),
            'vehicle': self.vehicle.text().strip(),
            'status': english_status
        }

class DashboardView(QWidget):
    """Comprehensive dashboard with CRUD operations and search functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db_connection()
        self.current_table = "rides"
        self.current_search_results = []
        self.tm = TranslationManager()
        
        self.init_ui()
        self.refresh_data()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(self.tm.tr("dashboard_title"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Quick stats
        self.stats_label = QLabel(self.tm.tr("loading_statistics"))
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main content area with tabs
        self.tab_widget = QTabWidget()
        
        # Rides tab
        rides_tab = self.create_rides_tab()
        self.tab_widget.addTab(rides_tab, self.tm.tr("rides_management"))
        
        # Drivers tab
        drivers_tab = self.create_drivers_tab()
        self.tab_widget.addTab(drivers_tab, self.tm.tr("drivers_management"))
        
        # Search Results tab
        search_tab = self.create_search_tab()
        self.tab_widget.addTab(search_tab, self.tm.tr("search_results"))
        
        # Database Management tab
        db_tab = self.create_database_tab()
        self.tab_widget.addTab(db_tab, self.tm.tr("database_management"))
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QLabel(self.tm.tr("ready"))
        self.status_bar.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-top: 1px solid #ddd;")
        layout.addWidget(self.status_bar)
    
    def create_control_panel(self):
        panel = QGroupBox(self.tm.tr("search_and_filter"))
        layout = QHBoxLayout(panel)
        
        # Global search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tm.tr("search_placeholder"))
        self.search_input.returnPressed.connect(self.perform_global_search)
        layout.addWidget(QLabel(f"{self.tm.tr('search')}:"))
        layout.addWidget(self.search_input)
        
        # Search button
        search_btn = QPushButton(self.tm.tr("search"))
        search_btn.clicked.connect(self.perform_global_search)
        layout.addWidget(search_btn)
        
        # Clear search
        clear_btn = QPushButton(self.tm.tr("clear"))
        clear_btn.clicked.connect(self.clear_search)
        layout.addWidget(clear_btn)
        
        # Date filter
        layout.addWidget(QLabel(f"{self.tm.tr('date')}:"))
        self.date_filter = QDateEdit()
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setCalendarPopup(True)
        self.date_filter.dateChanged.connect(self.apply_date_filter)
        layout.addWidget(self.date_filter)
        
        # Status filter
        layout.addWidget(QLabel(f"{self.tm.tr('status')}:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            self.tm.tr("all_status"),
            self.tm.tr("completed"),
            self.tm.tr("cancelled"),
            self.tm.tr("in_progress")
        ])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.status_filter)
        
        return panel
    
    def create_rides_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Rides controls
        controls_layout = QHBoxLayout()
        
        add_ride_btn = QPushButton(self.tm.tr("add_new_ride"))
        add_ride_btn.clicked.connect(self.add_ride)
        controls_layout.addWidget(add_ride_btn)
        
        edit_ride_btn = QPushButton(self.tm.tr("edit_selected_ride"))
        edit_ride_btn.clicked.connect(self.edit_ride)
        controls_layout.addWidget(edit_ride_btn)
        
        delete_ride_btn = QPushButton(self.tm.tr("delete_selected_ride"))
        delete_ride_btn.clicked.connect(self.delete_ride)
        delete_ride_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        delete_ride_btn.setVisible(False)
        controls_layout.addWidget(delete_ride_btn)
        
        refresh_btn = QPushButton(self.tm.tr("refresh"))
        refresh_btn.clicked.connect(self.refresh_rides_data)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Rides table
        self.rides_table = QTableWidget()
        self.rides_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rides_table.setAlternatingRowColors(True)
        self.rides_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.rides_table)
        
        return widget
    
    def create_drivers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Drivers controls
        controls_layout = QHBoxLayout()
        
        add_driver_btn = QPushButton(self.tm.tr("add_new_driver"))
        add_driver_btn.clicked.connect(self.add_driver)
        controls_layout.addWidget(add_driver_btn)
        
        edit_driver_btn = QPushButton(self.tm.tr("edit_selected_driver"))
        edit_driver_btn.clicked.connect(self.edit_driver)
        controls_layout.addWidget(edit_driver_btn)
        
        delete_driver_btn = QPushButton(self.tm.tr("delete_selected_driver"))
        delete_driver_btn.clicked.connect(self.delete_driver)
        delete_driver_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        delete_driver_btn.setVisible(False)
        controls_layout.addWidget(delete_driver_btn)
        
        refresh_btn = QPushButton(self.tm.tr("refresh"))
        refresh_btn.clicked.connect(self.refresh_drivers_data)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Drivers table
        self.drivers_table = QTableWidget()
        self.drivers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.drivers_table.setAlternatingRowColors(True)
        self.drivers_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.drivers_table)
        
        return widget
    
    def create_search_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search results info
        self.search_info = QLabel(self.tm.tr("no_search_performed"))
        self.search_info.setStyleSheet("padding: 10px; background-color: #e9ecef; border-radius: 5px;")
        layout.addWidget(self.search_info)
        
        # Search results table
        self.search_table = QTableWidget()
        self.search_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_table.setAlternatingRowColors(True)
        self.search_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.search_table)
        
        return widget
    
    def create_database_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Database info
        info_group = QGroupBox(self.tm.tr("database_information"))
        info_layout = QGridLayout(info_group)
        
        self.db_info_label = QLabel(self.tm.tr("loading_database_info"))
        info_layout.addWidget(self.db_info_label, 0, 0, 1, 2)
        
        layout.addWidget(info_group)
        
        # Database operations
        ops_group = QGroupBox(self.tm.tr("database_operations"))
        ops_layout = QVBoxLayout(ops_group)
        
        # Warning label
        warning = QLabel(f"⚠️ {self.tm.tr('warning_cannot_undo')}")
        warning.setStyleSheet("color: #dc3545; font-weight: bold; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;")
        ops_layout.addWidget(warning)
        
        # Clear buttons
        buttons_layout = QHBoxLayout()
        
        clear_rides_btn = QPushButton(self.tm.tr("clear_all_rides"))
        clear_rides_btn.clicked.connect(lambda: self.clear_database("clear_rides"))
        clear_rides_btn.setStyleSheet("QPushButton { background-color: #fd7e14; color: white; padding: 10px; }")
        clear_rides_btn.setVisible(False)
        buttons_layout.addWidget(clear_rides_btn)
        
        clear_drivers_btn = QPushButton(self.tm.tr("clear_all_drivers"))
        clear_drivers_btn.clicked.connect(lambda: self.clear_database("clear_drivers"))
        clear_drivers_btn.setStyleSheet("QPushButton { background-color: #fd7e14; color: white; padding: 10px; }")
        clear_drivers_btn.setVisible(False)
        buttons_layout.addWidget(clear_drivers_btn)
        
        clear_all_btn = QPushButton(self.tm.tr("clear_entire_database"))
        clear_all_btn.clicked.connect(lambda: self.clear_database("clear_all"))
        clear_all_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; padding: 10px; }")
        clear_all_btn.setVisible(False)
        buttons_layout.addWidget(clear_all_btn)
        
        ops_layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        ops_layout.addWidget(self.progress_bar)
        
        # Status label
        self.operation_status = QLabel("")
        self.operation_status.setVisible(False)
        ops_layout.addWidget(self.operation_status)
        
        layout.addWidget(ops_group)
        layout.addStretch()
        
        return widget

    # CRUD Operations for Rides
    def add_ride(self):
        dialog = RideEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                ride_data = dialog.get_ride_data()
                
                # Validate required fields
                if not ride_data['driver_id']:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_select_driver"))
                    return
                
                if not ride_data['pickup_location'] or not ride_data['destination']:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_fill_locations"))
                    return
                
                # Check for duplicate ride
                cursor = self.db.cursor()
                cursor.execute("""
                    SELECT id FROM rides 
                    WHERE driver_id = ? AND pickup_time = ? AND pickup_location = ? AND destination = ?
                """, (ride_data['driver_id'], ride_data['pickup_time'], ride_data['pickup_location'], ride_data['destination']))
                existing_ride = cursor.fetchone()
                if existing_ride:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("duplicate_ride_error"))
                    return
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO rides (driver_id, pickup_time, dropoff_time, pickup_location, 
                                     destination, distance_km, duration_minutes, revenue, status, 
                                     vehicle_plate, violations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ride_data['driver_id'], ride_data['pickup_time'], ride_data['dropoff_time'],
                    ride_data['pickup_location'], ride_data['destination'], ride_data['distance_km'],
                    ride_data['duration_minutes'], ride_data['revenue'], ride_data['status'],
                    ride_data['vehicle_plate'], ride_data['violations']
                ))
                
                self.db.commit()
                self.refresh_rides_data()
                self.update_stats()
                
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("ride_added_successfully"))
                self.status_bar.setText(self.tm.tr("ride_added_successfully"))
                
            except Exception as e:
                QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_add_ride')}: {str(e)}")
    
    def edit_ride(self):
        current_row = self.rides_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_select_ride_to_edit"))
            return
        
        # Get ride ID from the first column
        ride_id = int(self.rides_table.item(current_row, 0).text())
        
        # Fetch ride data
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
            ride_row = cursor.fetchone()
            
            if not ride_row:
                QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("ride_not_found"))
                return
            
            ride_data = dict(ride_row)
            
            dialog = RideEditDialog(self, ride_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_ride_data()
                
                cursor.execute("""
                    UPDATE rides SET driver_id=?, pickup_time=?, dropoff_time=?, pickup_location=?,
                                   destination=?, distance_km=?, duration_minutes=?, revenue=?, 
                                   status=?, vehicle_plate=?, violations=?
                    WHERE id=?
                """, (
                    updated_data['driver_id'], updated_data['pickup_time'], updated_data['dropoff_time'],
                    updated_data['pickup_location'], updated_data['destination'], updated_data['distance_km'],
                    updated_data['duration_minutes'], updated_data['revenue'], updated_data['status'],
                    updated_data['vehicle_plate'], updated_data['violations'], ride_id
                ))
                
                self.db.commit()
                self.refresh_rides_data()
                self.update_stats()
                
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("ride_updated_successfully"))
                self.status_bar.setText(self.tm.tr("ride_updated_successfully"))
                
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_edit_ride')}: {str(e)}")
    
    def delete_ride(self):
        current_row = self.rides_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_select_ride_to_delete"))
            return
        
        # Get ride ID and some info for confirmation
        ride_id = int(self.rides_table.item(current_row, 0).text())
        pickup_location = self.rides_table.item(current_row, 3).text()
        destination = self.rides_table.item(current_row, 4).text()
        
        reply = QMessageBox.question(
            self, self.tm.tr("confirm_delete"),
            f"{self.tm.tr('confirm_delete_ride')}\n\n"
            f"{self.tm.tr('from')}: {pickup_location}\n{self.tm.tr('to')}: {destination}\n\n"
            f"{self.tm.tr('action_cannot_undone')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.db.cursor()
                cursor.execute("DELETE FROM rides WHERE id = ?", (ride_id,))
                self.db.commit()
                
                self.refresh_rides_data()
                self.update_stats()
                
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("ride_deleted_successfully"))
                self.status_bar.setText(self.tm.tr("ride_deleted_successfully"))
                
            except Exception as e:
                QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_delete_ride')}: {str(e)}")
    
    # CRUD Operations for Drivers
    def add_driver(self):
        dialog = DriverEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                driver_data = dialog.get_driver_data()
                
                # Validate required fields
                if not driver_data['name']:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_enter_driver_name"))
                    return
                
                # Check for duplicate driver
                cursor = self.db.cursor()
                # Assuming company_id is part of the driver's table or context,
                # If not, this check might need adjustment or be based on name globally.
                # For now, we'll check for name uniqueness. If your schema has company_id in drivers, add it to WHERE.
                cursor.execute("SELECT id FROM drivers WHERE name = ?", (driver_data['name'],))
                existing_driver = cursor.fetchone()
                if existing_driver:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("duplicate_driver_error"))
                    return
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO drivers (name, vehicle, status)
                    VALUES (?, ?, ?)
                """, (driver_data['name'], driver_data['vehicle'], driver_data['status']))
                
                self.db.commit()
                self.refresh_drivers_data()
                self.update_stats()
                
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("driver_added_successfully"))
                self.status_bar.setText(self.tm.tr("driver_added_successfully"))
                
            except Exception as e:
                QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_add_driver')}: {str(e)}")
    
    def edit_driver(self):
        current_row = self.drivers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_select_driver_to_edit"))
            return
        
        # Get driver ID from the first column
        driver_id = int(self.drivers_table.item(current_row, 0).text())
        
        # Fetch driver data
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
            driver_row = cursor.fetchone()
            
            if not driver_row:
                QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("driver_not_found"))
                return
            
            driver_data = dict(driver_row)
            
            dialog = DriverEditDialog(self, driver_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_driver_data()
                
                cursor.execute("""
                    UPDATE drivers SET name=?, vehicle=?, status=?
                    WHERE id=?
                """, (updated_data['name'], updated_data['vehicle'], updated_data['status'], driver_id))
                
                self.db.commit()
                self.refresh_drivers_data()
                self.update_stats()
                
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("driver_updated_successfully"))
                self.status_bar.setText(self.tm.tr("driver_updated_successfully"))
                
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_edit_driver')}: {str(e)}")
    
    def delete_driver(self):
        current_row = self.drivers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("please_select_driver_to_delete"))
            return
        
        # Get driver ID and name for confirmation
        driver_id = int(self.drivers_table.item(current_row, 0).text())
        driver_name = self.drivers_table.item(current_row, 1).text()
        
        # Check if driver has rides
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT COUNT(*) as ride_count FROM rides WHERE driver_id = ?", (driver_id,))
            ride_count = cursor.fetchone()['ride_count']
            
            warning_msg = f"{self.tm.tr('confirm_delete_driver')} '{driver_name}'?"
            if ride_count > 0:
                warning_msg += f"\n\n{self.tm.tr('driver_has_rides').format(ride_count)}"
                warning_msg += f"\n{self.tm.tr('deleting_driver_warning')}"
            warning_msg += f"\n\n{self.tm.tr('action_cannot_undone')}"
            
            reply = QMessageBox.question(
                self, self.tm.tr("confirm_delete"), warning_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))
                self.db.commit()
                
                self.refresh_drivers_data()
                self.update_stats()
                
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("driver_deleted_successfully"))
                self.status_bar.setText(self.tm.tr("driver_deleted_successfully"))
                
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_delete_driver')}: {str(e)}")
    
    # Search and Filter Functions
    def perform_global_search(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.information(self, self.tm.tr("search"), self.tm.tr("please_enter_search_term"))
            return
        
        try:
            cursor = self.db.cursor()
            
            # Search across multiple tables and fields
            search_query = """
                SELECT 'ride' as type, r.id, r.pickup_time, r.pickup_location, r.destination, 
                       d.name as driver_name, r.vehicle_plate, r.status, r.revenue
                FROM rides r
                LEFT JOIN drivers d ON r.driver_id = d.id
                WHERE r.pickup_location LIKE ? OR r.destination LIKE ? 
                   OR d.name LIKE ? OR r.vehicle_plate LIKE ?
                   OR r.status LIKE ?
                UNION ALL
                SELECT 'driver' as type, d.id, NULL as pickup_time, NULL as pickup_location, 
                       NULL as destination, d.name as driver_name, d.vehicle as vehicle_plate, 
                       d.status, NULL as revenue
                FROM drivers d
                WHERE d.name LIKE ? OR d.vehicle LIKE ? OR d.status LIKE ?
                ORDER BY pickup_time DESC
            """
            
            search_pattern = f"%{search_term}%"
            cursor.execute(search_query, [search_pattern] * 8)
            results = cursor.fetchall()
            
            self.current_search_results = results
            self.display_search_results(results, search_term)
            
            # Switch to search results tab
            self.tab_widget.setCurrentIndex(2)  # Search Results tab
            
            self.status_bar.setText(self.tm.tr("search_completed").format(len(results)))
            
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("search_error"), f"{self.tm.tr('failed_to_perform_search')}: {str(e)}")
    
    def display_search_results(self, results, search_term):
        self.search_info.setText(self.tm.tr("search_results_info").format(len(results), search_term))
        
        if not results:
            self.search_table.setRowCount(0)
            self.search_table.setColumnCount(0)
            return
        
        # Set up table columns
        columns = [
            self.tm.tr("type"),
            "ID",
            self.tm.tr("date_time"),
            self.tm.tr("from_location"),
            self.tm.tr("to_location_vehicle"),
            self.tm.tr("driver"),
            self.tm.tr("status"),
            self.tm.tr("revenue")
        ]
        self.search_table.setColumnCount(len(columns))
        self.search_table.setHorizontalHeaderLabels(columns)
        self.search_table.setRowCount(len(results))
        
        # Populate table
        for row, result in enumerate(results):
            type_text = self.tm.tr("ride") if result['type'] == 'ride' else self.tm.tr("driver")
            self.search_table.setItem(row, 0, QTableWidgetItem(type_text))
            self.search_table.setItem(row, 1, QTableWidgetItem(str(result['id'])))
            
            if result['pickup_time']:
                date_time = datetime.fromisoformat(result['pickup_time']).strftime("%Y-%m-%d %H:%M")
                self.search_table.setItem(row, 2, QTableWidgetItem(date_time))
            else:
                self.search_table.setItem(row, 2, QTableWidgetItem("N/A"))
            
            self.search_table.setItem(row, 3, QTableWidgetItem(result['pickup_location'] or result['driver_name'] or ""))
            self.search_table.setItem(row, 4, QTableWidgetItem(result['destination'] or result['vehicle_plate'] or ""))
            self.search_table.setItem(row, 5, QTableWidgetItem(result['driver_name'] or ""))
            self.search_table.setItem(row, 6, QTableWidgetItem(result['status'] or ""))
            
            revenue_text = f"€{result['revenue']:.2f}" if result['revenue'] else "N/A"
            self.search_table.setItem(row, 7, QTableWidgetItem(revenue_text))
        
        # Resize columns to content
        self.search_table.resizeColumnsToContents()
    
    def clear_search(self):
        self.search_input.clear()
        self.current_search_results = []
        self.search_info.setText(self.tm.tr("no_search_performed"))
        self.search_table.setRowCount(0)
        self.search_table.setColumnCount(0)
        self.status_bar.setText(self.tm.tr("search_cleared"))
    
    def apply_date_filter(self):
        self.apply_filters()
    
    def apply_filters(self):
        # Apply filters to the current rides view
        selected_date = self.date_filter.date().toString("yyyy-MM-dd")
        selected_status = self.status_filter.currentText()
        
        try:
            cursor = self.db.cursor()
            
            # Build query with filters
            query = """
                SELECT r.*, d.name as driver_name 
                FROM rides r 
                LEFT JOIN drivers d ON r.driver_id = d.id 
                WHERE DATE(r.pickup_time) = ?
            """
            params = [selected_date]
            
            if selected_status != self.tm.tr("all_status"):
                # Map German status to English for database query
                status_map = {
                    self.tm.tr("completed"): "Completed",
                    self.tm.tr("cancelled"): "Cancelled", 
                    self.tm.tr("in_progress"): "In Progress"
                }
                english_status = status_map.get(selected_status, selected_status)
                query += " AND r.status = ?"
                params.append(english_status)
            
            query += " ORDER BY r.pickup_time DESC"
            
            cursor.execute(query, params)
            filtered_rides = cursor.fetchall()
            
            self.populate_rides_table(filtered_rides)
            self.status_bar.setText(self.tm.tr("filter_applied").format(len(filtered_rides), selected_date))
            
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("filter_error"), f"{self.tm.tr('failed_to_apply_filters')}: {str(e)}")
    
    # Database Management Functions
    def clear_database(self, operation_type):
        operation_names = {
            "clear_rides": self.tm.tr("clear_all_rides"),
            "clear_drivers": self.tm.tr("clear_all_drivers"), 
            "clear_all": self.tm.tr("clear_entire_database")
        }
        
        operation_name = operation_names.get(operation_type, self.tm.tr("unknown_operation"))
        
        reply = QMessageBox.question(
            self, self.tm.tr("confirm_database_operation"),
            f"{self.tm.tr('confirm_perform_operation')}: {operation_name}?\n\n"
            f"⚠️ {self.tm.tr('permanent_delete_warning')}\n\n"
            f"{self.tm.tr('type_confirm_instruction')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Additional confirmation
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, self.tm.tr("final_confirmation"), 
                                          self.tm.tr("type_confirm_to_proceed"))
            
            if ok and text == "CONFIRM":
                self.execute_database_clear(operation_type)
            else:
                QMessageBox.information(self, self.tm.tr("cancelled"), self.tm.tr("operation_cancelled"))
    
    def execute_database_clear(self, operation_type):
        # Show progress indicators
        self.progress_bar.setVisible(True)
        self.operation_status.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start background thread
        self.clear_thread = DatabaseClearThread(operation_type)
        self.clear_thread.progress.connect(self.progress_bar.setValue)
        self.clear_thread.status_update.connect(self.operation_status.setText)
        self.clear_thread.finished_signal.connect(self.database_clear_finished)
        self.clear_thread.start()
    
    def database_clear_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.operation_status.setVisible(False)
        
        if success:
            QMessageBox.information(self, self.tm.tr("success"), message)
            self.refresh_data()
            self.update_stats()
        else:
            QMessageBox.critical(self, self.tm.tr("error"), message)
        
        self.status_bar.setText(self.tm.tr("database_operation_completed"))
    
    # Data Loading and Display Functions
    def refresh_data(self):
        self.refresh_rides_data()
        self.refresh_drivers_data()
        self.update_stats()
        self.update_database_info()
    
    def refresh_rides_data(self):
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT r.*, d.name as driver_name 
                FROM rides r 
                LEFT JOIN drivers d ON r.driver_id = d.id 
                ORDER BY r.pickup_time DESC 
                LIMIT 1000
            """)
            rides = cursor.fetchall()
            self.populate_rides_table(rides)
            
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_load_rides')}: {str(e)}")
    
    def populate_rides_table(self, rides):
        columns = [
            "ID",
            self.tm.tr("driver"),
            self.tm.tr("pickup_time"),
            self.tm.tr("pickup_location"),
            self.tm.tr("destination"),
            self.tm.tr("distance_km"),
            self.tm.tr("duration_minutes"),
            self.tm.tr("revenue"),
            self.tm.tr("status"),
            self.tm.tr("vehicle")
        ]
        
        self.rides_table.setColumnCount(len(columns))
        self.rides_table.setHorizontalHeaderLabels(columns)
        self.rides_table.setRowCount(len(rides))
        
        for row, ride in enumerate(rides):
            self.rides_table.setItem(row, 0, QTableWidgetItem(str(ride['id'])))
            self.rides_table.setItem(row, 1, QTableWidgetItem(ride['driver_name'] or self.tm.tr("unknown")))
            
            # Handle pickup_time safely
            try:
                if ride['pickup_time']:
                    pickup_time = datetime.fromisoformat(ride['pickup_time']).strftime("%Y-%m-%d %H:%M")
                else:
                    pickup_time = "N/A"
            except (ValueError, TypeError):
                pickup_time = str(ride['pickup_time']) if ride['pickup_time'] else "N/A"
            
            self.rides_table.setItem(row, 2, QTableWidgetItem(pickup_time))
            
            self.rides_table.setItem(row, 3, QTableWidgetItem(ride['pickup_location'] or ""))
            self.rides_table.setItem(row, 4, QTableWidgetItem(ride['destination'] or ""))
            
            # Handle None values properly for numeric fields
            distance_text = f"{ride['distance_km']:.2f}" if ride['distance_km'] is not None else "N/A"
            self.rides_table.setItem(row, 5, QTableWidgetItem(distance_text))
            
            duration_text = str(ride['duration_minutes']) if ride['duration_minutes'] is not None else "N/A"
            self.rides_table.setItem(row, 6, QTableWidgetItem(duration_text))
            
            revenue_text = f"€{ride['revenue']:.2f}" if ride['revenue'] is not None else "N/A"
            self.rides_table.setItem(row, 7, QTableWidgetItem(revenue_text))
            
            # Map English status to German for display
            status_map = {
                "Completed": self.tm.tr("completed"),
                "Cancelled": self.tm.tr("cancelled"),
                "In Progress": self.tm.tr("in_progress")
            }
            german_status = status_map.get(ride['status'], ride['status'])
            self.rides_table.setItem(row, 8, QTableWidgetItem(german_status or ""))
            
            self.rides_table.setItem(row, 9, QTableWidgetItem(ride['vehicle_plate'] or ""))
        
        self.rides_table.resizeColumnsToContents()
    
    def refresh_drivers_data(self):
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM drivers ORDER BY name")
            drivers = cursor.fetchall()
            self.populate_drivers_table(drivers)
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_load_drivers')}: {str(e)}")
    
    def populate_drivers_table(self, drivers):
        columns = [
            "ID",
            self.tm.tr("name"),
            self.tm.tr("vehicle"),
            self.tm.tr("status")
        ]
        
        self.drivers_table.setColumnCount(len(columns))
        self.drivers_table.setHorizontalHeaderLabels(columns)
        self.drivers_table.setRowCount(len(drivers))
        
        for row, driver in enumerate(drivers):
            self.drivers_table.setItem(row, 0, QTableWidgetItem(str(driver['id'])))
            self.drivers_table.setItem(row, 1, QTableWidgetItem(driver['name'] or ""))
            self.drivers_table.setItem(row, 2, QTableWidgetItem(driver['vehicle'] or ""))
            
            # Map English status to German
            status_map = {
                "Active": self.tm.tr("active"),
                "Inactive": self.tm.tr("inactive"),
                "Suspended": self.tm.tr("suspended")
            }
            german_status = status_map.get(driver['status'], driver['status'])
            self.drivers_table.setItem(row, 3, QTableWidgetItem(german_status or ""))
        
        self.drivers_table.resizeColumnsToContents()
    
    def update_stats(self):
        try:
            cursor = self.db.cursor()
            
            # Get ride count
            cursor.execute("SELECT COUNT(*) as count FROM rides")
            ride_count = cursor.fetchone()['count']
            
            # Get driver count
            cursor.execute("SELECT COUNT(*) as count FROM drivers WHERE status = 'Active'")
            driver_count = cursor.fetchone()['count']
            
            # Get today's revenue
            cursor.execute("""
                SELECT SUM(revenue) as total_revenue 
                FROM rides 
                WHERE DATE(pickup_time) = DATE('now') 
                AND status = 'Completed'
            """)
            result = cursor.fetchone()
            today_revenue = result['total_revenue'] or 0
            
            stats_text = f"{self.tm.tr('total_rides')}: {ride_count} | {self.tm.tr('active_drivers')}: {driver_count} | {self.tm.tr('today_revenue')}: €{today_revenue:.2f}"
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            self.stats_label.setText(f"{self.tm.tr('error_loading_stats')}: {str(e)}")
    
    def update_database_info(self):
        try:
            cursor = self.db.cursor()
            
            # Get table counts
            cursor.execute("SELECT COUNT(*) as count FROM rides")
            ride_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM drivers")
            driver_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM companies")
            company_count = cursor.fetchone()['count']
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            
            info_text = f"""
            {self.tm.tr('database_statistics')}:
            • {self.tm.tr('rides')}: {ride_count}
            • {self.tm.tr('drivers')}: {driver_count}
            • {self.tm.tr('companies')}: {company_count}
            • {self.tm.tr('database_size')}: {db_size_mb:.2f} MB
            """
            
            self.db_info_label.setText(info_text)
            
        except Exception as e:
            self.db_info_label.setText(f"{self.tm.tr('error_loading_db_info')}: {str(e)}")
    
    def closeEvent(self, event):
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        if self.db:
            self.db.close()
        super().closeEvent(event)