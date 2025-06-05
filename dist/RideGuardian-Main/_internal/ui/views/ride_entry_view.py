from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QDateEdit, QLineEdit, QTextEdit, QPushButton, QFrame, QSpacerItem,
    QSizePolicy, QTimeEdit, QSpinBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, QTime, QDateTime
from PyQt6.QtGui import QFont, QIcon
import sqlite3
import os
import sys
from datetime import datetime
import json
from typing import Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)
from core.database import get_db_connection
from core.ride_validator import RideValidator
from core.google_maps import GoogleMapsIntegration
from core.translation_manager import tr

class RideEntryView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.company_id = company_id
        self.db = get_db_connection()
        self.validator = RideValidator(self.db)
        self.google_maps = GoogleMapsIntegration()
        self.init_ui()
        self.load_drivers()

    def init_ui(self):
        """Initialize the redesigned user interface with better UX"""
        # Main layout with proper spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Create scroll area for better responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(25)
        
        # Header section
        header_container = self.create_header()
        content_layout.addWidget(header_container)
        
        # Main form container
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 0px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(0)
        
        # Driver & Vehicle Section
        driver_section = self.create_driver_section()
        form_layout.addWidget(driver_section)
        
        # Add separator
        separator1 = self.create_separator()
        form_layout.addWidget(separator1)
        
        # Ride Details Section
        ride_details_section = self.create_ride_details_section()
        form_layout.addWidget(ride_details_section)
        
        # Add separator
        separator2 = self.create_separator()
        form_layout.addWidget(separator2)
        
        # Locations Section
        locations_section = self.create_locations_section()
        form_layout.addWidget(locations_section)
        
        # Add separator
        separator3 = self.create_separator()
        form_layout.addWidget(separator3)
        
        # Additional Details Section
        additional_section = self.create_additional_section()
        form_layout.addWidget(additional_section)
        
        content_layout.addWidget(form_container)
        
        # Action buttons
        actions_container = self.create_actions()
        content_layout.addWidget(actions_container)
        
        # Add stretch at the end
        content_layout.addStretch()
        
        # Set content to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_header(self):
        """Create the header section with title and description"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Title
        title = QLabel(tr("📝 Neue Fahrt"))
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(tr("Fahrtdetails eingeben und verfügbarem Fahrer zuweisen"))
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(subtitle)
        
        return container

    def create_driver_section(self):
        """Create the driver and vehicle selection section"""
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border: none; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Section header
        section_title = QLabel(tr("👨‍💼 Fahrer & Fahrzeug"))
        section_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                background-color: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(section_title)
        
        # Form grid
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)
        
        # Driver selection
        driver_label = QLabel(tr("Fahrer:"))
        driver_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(driver_label, 0, 0)
        
        self.driver_cb = QComboBox()
        self.driver_cb.setStyleSheet(self.get_combobox_style())
        self.driver_cb.currentIndexChanged.connect(self.update_vehicle)
        form_layout.addWidget(self.driver_cb, 0, 1)
        
        # Vehicle display
        vehicle_label = QLabel(tr("Fahrzeug:"))
        vehicle_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(vehicle_label, 1, 0)
        
        self.vehicle_le = QLineEdit()
        self.vehicle_le.setPlaceholderText(tr("Fahrzeug wird automatisch basierend auf Fahrerauswahl ausgefüllt"))
        self.vehicle_le.setReadOnly(True)
        self.vehicle_le.setStyleSheet(self.get_readonly_input_style())
        form_layout.addWidget(self.vehicle_le, 1, 1)
        
        layout.addLayout(form_layout)
        return container

    def create_ride_details_section(self):
        """Create the ride details section"""
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border: none; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Section header
        section_title = QLabel(tr("🚗 Fahrtdetails"))
        section_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                background-color: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(section_title)
        
        # Form grid
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)
        
        # Date and time in same row
        date_label = QLabel(tr("Abholdatum:"))
        date_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(date_label, 0, 0)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.date_edit, 0, 1)
        
        time_label = QLabel(tr("Abholzeit:"))
        time_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(time_label, 0, 2)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.time_edit, 0, 3)
        
        # Passengers and distance
        passengers_label = QLabel(tr("Fahrgäste:"))
        passengers_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(passengers_label, 1, 0)
        
        self.passengers_spin = QSpinBox()
        self.passengers_spin.setRange(1, 8)
        self.passengers_spin.setValue(1)
        self.passengers_spin.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.passengers_spin, 1, 1)
        
        distance_label = QLabel(tr("Entfernung (km):"))
        distance_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(distance_label, 1, 2)
        
        self.distance_spin = QSpinBox()
        self.distance_spin.setRange(0, 999)
        self.distance_spin.setSuffix(" km")
        self.distance_spin.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.distance_spin, 1, 3)
        
        layout.addLayout(form_layout)
        return container

    def create_locations_section(self):
        """Create the locations section"""
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border: none; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Section header
        section_title = QLabel(tr("📍 Standorte"))
        section_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                background-color: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(section_title)
        
        # Form layout
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)
        
        # Pickup location
        pickup_label = QLabel(tr("Abholort:"))
        pickup_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(pickup_label, 0, 0)
        
        self.pickup_le = QLineEdit()
        self.pickup_le.setPlaceholderText(tr("Abholadresse oder Orientierungspunkt eingeben"))
        self.pickup_le.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.pickup_le, 0, 1, 1, 2)
        
        # Destination
        dest_label = QLabel(tr("Ziel:"))
        dest_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(dest_label, 1, 0)
        
        self.dest_le = QLineEdit()
        self.dest_le.setPlaceholderText(tr("Zieladresse oder Orientierungspunkt eingeben"))
        self.dest_le.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.dest_le, 1, 1, 1, 2)
        
        layout.addLayout(form_layout)
        return container

    def create_additional_section(self):
        """Create the additional details section"""
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border: none; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Section header
        section_title = QLabel(tr("💰 Finanzielle Details"))
        section_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                background-color: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(section_title)
        
        # Form layout
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)
        
        # Fare amount
        fare_label = QLabel(tr("Fahrpreis:"))
        fare_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(fare_label, 0, 0)
        
        self.fare_spin = QSpinBox()
        self.fare_spin.setRange(0, 9999)
        self.fare_spin.setPrefix("€")
        self.fare_spin.setValue(0)
        self.fare_spin.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.fare_spin, 0, 1)
        
        # Notes
        notes_label = QLabel(tr("Notizen:"))
        notes_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(notes_label, 1, 0, Qt.AlignmentFlag.AlignTop)
        
        self.notes_te = QTextEdit()
        self.notes_te.setPlaceholderText(tr("Besondere Anweisungen oder Notizen für diese Fahrt hinzufügen..."))
        self.notes_te.setMaximumHeight(100)
        self.notes_te.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
                color: #495057;
            }
            QTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        form_layout.addWidget(self.notes_te, 1, 1, 1, 2)
        
        layout.addLayout(form_layout)
        return container

    def create_actions(self):
        """Create the action buttons section"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Add stretch to push buttons to the right
        layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton(tr("🗑️ Formular löschen"))
        clear_btn.setMinimumSize(130, 45)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e555b;
            }
        """)
        clear_btn.clicked.connect(self.clear_form)
        layout.addWidget(clear_btn)
        
        # Validate button
        self.validate_btn = QPushButton(tr("✅ Fahrt validieren"))
        self.validate_btn.setMinimumSize(130, 45)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #0e6674;
            }
        """)
        self.validate_btn.clicked.connect(self.validate_ride)
        layout.addWidget(self.validate_btn)
        
        # Submit button
        self.submit_btn = QPushButton(tr("🚀 Fahrt einreichen"))
        self.submit_btn.setMinimumSize(130, 45)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.submit_btn.clicked.connect(self.submit_ride)
        layout.addWidget(self.submit_btn)
        
        return container

    def create_separator(self):
        """Create a visual separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                color: #e9ecef;
                background-color: #e9ecef;
                border: none;
                height: 1px;
            }
        """)
        return separator

    def get_label_style(self):
        """Get consistent label styling"""
        return """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                background-color: transparent;
                border: none;
                min-width: 120px;
            }
        """

    def get_input_style(self):
        """Get consistent input field styling"""
        return """
            QLineEdit, QSpinBox, QDateEdit, QTimeEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
                color: #495057;
                min-height: 20px;
            }
            QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            QLineEdit:hover, QSpinBox:hover, QDateEdit:hover, QTimeEdit:hover {
                border-color: #80bdff;
            }
        """

    def get_readonly_input_style(self):
        """Get styling for readonly input fields"""
        return """
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: #f8f9fa;
                color: #6c757d;
                min-height: 20px;
            }
        """

    def get_combobox_style(self):
        """Get consistent combobox styling"""
        return """
            QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
                color: #495057;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox:hover {
                border-color: #80bdff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background-color: #f8f9fa;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #495057;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e9ecef;
                background-color: white;
                selection-background-color: #007bff;
                selection-color: white;
                outline: none;
                font-size: 14px;
            }
        """

    def load_drivers(self):
        """Load all available drivers into the combo box"""
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT id, name, vehicle FROM drivers WHERE company_id = ? AND status = 'Active' ORDER BY name", (self.company_id,))
            
            self.driver_cb.clear()
            self.driver_cb.addItem(tr("-- Fahrer auswählen --"), 0)  # Default option
            
            self.drivers_data = {}  # Store driver data for quick lookup
            
            for driver in cursor.fetchall():
                display_text = f"{driver['name']} - {driver['vehicle'] or tr('Kein Fahrzeug')}"
                self.driver_cb.addItem(display_text, driver['id'])
                self.drivers_data[driver['id']] = {
                    'name': driver['name'],
                    'vehicle': driver['vehicle'] or tr('Kein Fahrzeug zugewiesen')
                }
                
        except Exception as e:
            print(f"Error loading drivers: {e}")
            QMessageBox.critical(self, tr("Datenbankfehler"), tr(f"Fahrer konnten nicht geladen werden: {str(e)}"))

    def update_vehicle(self, index):
        """Update vehicle field when driver is selected"""
        if index <= 0 or not self.drivers_data:  # 0 is "-- Select a Driver --"
            self.vehicle_le.clear()
            return
            
        try:
            # Get driver ID from combo box
            driver_id = self.driver_cb.currentData()
            if driver_id and driver_id in self.drivers_data:
                self.vehicle_le.setText(self.drivers_data[driver_id]['vehicle'])
        except (KeyError, TypeError):
            self.vehicle_le.clear()

    def clear_form(self):
        """Clear all form fields"""
        self.driver_cb.setCurrentIndex(0)
        self.vehicle_le.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.time_edit.setTime(QTime.currentTime())
        self.passengers_spin.setValue(1)
        self.distance_spin.setValue(0)
        self.pickup_le.clear()
        self.dest_le.clear()
        self.fare_spin.setValue(0)
        self.notes_te.clear()

    def validate_ride(self):
        """Enhanced ride validation using the rule engine"""
        errors = []
        
        # Basic field validation
        if self.driver_cb.currentData() is None or self.driver_cb.currentData() == 0:
            errors.append(tr("Bitte wählen Sie einen Fahrer aus"))
        
        if not self.pickup_le.text().strip():
            errors.append(tr("Bitte geben Sie den Abholort ein"))
            
        if not self.dest_le.text().strip():
            errors.append(tr("Bitte geben Sie das Ziel ein"))
            
        if self.passengers_spin.value() <= 0:
            errors.append(tr("Anzahl der Fahrgäste muss mindestens 1 sein"))
        
        # If basic validation passes, run rule validation
        if not errors:
            ride_data = self._prepare_ride_data()
            
            # Validate addresses with Google Maps
            pickup_valid, pickup_standardized = self.google_maps.validate_address(ride_data['pickup_location'])
            dest_valid, dest_standardized = self.google_maps.validate_address(ride_data['destination'])
            
            if not pickup_valid:
                errors.append(tr(f"Ungültige Abholadresse: {ride_data['pickup_location']}"))
            if not dest_valid:
                errors.append(tr(f"Ungültige Zieladresse: {ride_data['destination']}"))
                
            # Run comprehensive rule validation
            if not errors:
                is_valid, violations = self.validator.validate_ride(ride_data)
                
                if violations:
                    rule_errors = []
                    for violation in violations:
                        if violation.startswith("RULE_1"):
                            rule_errors.append(tr("⚠️ Regel 1 Verstoß: Schicht muss am Hauptquartier beginnen"))
                        elif violation.startswith("RULE_2"):
                            rule_errors.append(tr(f"⚠️ Regel 2 Verstoß: Abholentfernung zu weit - {violation}"))
                        elif violation.startswith("RULE_3"):
                            rule_errors.append(tr(f"⚠️ Regel 3 Verstoß: Routenlogik-Problem - {violation}"))
                        elif violation.startswith("RULE_4"):
                            rule_errors.append(tr(f"⚠️ Regel 4 Verstoß: Zeitlücken-Problem - {violation}"))
                        elif violation.startswith("RULE_5"):
                            rule_errors.append(tr("⚠️ Regel 5 Verstoß: Unlogische Routenzuweisung"))
                        else:
                            rule_errors.append(tr(f"⚠️ Regelverstoß: {violation}"))
                    
                    # Show rule violations as warnings, not errors (they can still submit)
                    violation_msg = (tr("Regelverstöße erkannt:\n\n") + 
                                   "\n".join(rule_errors) + 
                                   tr("\n\nSie können diese Fahrt trotzdem einreichen, aber sie wird als Verstoß markiert."))
                    
                    reply = QMessageBox.warning(self, tr("Regelverstöße erkannt"), 
                                              violation_msg,
                                              QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
                    
                    if reply == QMessageBox.StandardButton.Cancel:
                        return  # Don't proceed with submission
        
        # Show validation results
        if errors:
            QMessageBox.warning(self, tr("Validierungsfehler"), 
                              tr("Bitte beheben Sie die folgenden Probleme:\n\n") + "\n".join(f"• {error}" for error in errors))
        else:
            QMessageBox.information(self, tr("Validierung erfolgreich"), 
                                  tr("✅ Alle Fahrtdetails sind gültig!\n\nSie können die Fahrt jetzt einreichen."))
    
    def submit_ride(self):
        """Enhanced ride submission with rule validation"""
        # Validate first
        if self.driver_cb.currentData() is None or self.driver_cb.currentData() == 0:
            QMessageBox.warning(self, tr("Ungültige Daten"), tr("Bitte wählen Sie einen Fahrer aus"))
            return
            
        if not self.pickup_le.text().strip() or not self.dest_le.text().strip():
            QMessageBox.warning(self, tr("Ungültige Daten"), tr("Bitte geben Sie sowohl Abholort als auch Ziel ein"))
            return
        
        if not self.db:
            QMessageBox.warning(self, tr("Datenbankfehler"), tr("Datenbankverbindung nicht verfügbar"))
            return
        
        try:
            # Prepare ride data
            ride_data = self._prepare_ride_data()
            
            # Run rule validation
            is_valid, violations = self.validator.validate_ride(ride_data)
            
            # Calculate distance and duration with Google Maps
            distance_km, duration_minutes = self.google_maps.calculate_distance_and_duration(
                ride_data['pickup_location'], ride_data['destination']
            )
            
            # Insert into database with enhanced data
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO rides (
                    driver_id, pickup_time, pickup_location, destination, 
                    vehicle_plate, status, violations, revenue, distance_km, 
                    duration_minutes, passengers, is_reserved, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ride_data['driver_id'], 
                ride_data['pickup_time'], 
                ride_data['pickup_location'], 
                ride_data['destination'],
                ride_data['vehicle_plate'], 
                'Violation' if violations else 'Pending',
                json.dumps(violations) if violations else None, 
                ride_data['revenue'],
                distance_km,
                duration_minutes,
                ride_data['passengers'],
                ride_data.get('is_reserved', False),
                ride_data.get('notes', '')
            ))
            
            ride_id = cursor.lastrowid
            self.db.commit()
            
            # Success message with rule status
            status_text = tr("⚠️ MIT REGELVERSTÖSSEN") if violations else tr("✅ KONFORM")
            violation_details = ""
            if violations:
                violation_details = tr(f"\n\nErkannte Verstöße:\n") + "\n".join(f"• {v}" for v in violations)
            
            QMessageBox.information(self, tr("Erfolg"), 
                                  tr(f"🎉 Fahrt erfolgreich eingereicht! {status_text}\n\n"
                                  f"Fahrer: {self.driver_cb.currentText()}\n"
                                  f"Von: {ride_data['pickup_location']}\n"
                                  f"Nach: {ride_data['destination']}\n"
                                  f"Entfernung: {distance_km:.1f} km\n"
                                  f"Dauer: {duration_minutes:.0f} Minuten\n"
                                  f"Zeit: {self.date_edit.date().toString('dd.MM.yyyy')} um {self.time_edit.time().toString('HH:mm')}"
                                  f"{violation_details}"))
            
            # Clear form after successful submission
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(self, tr("Einreichungsfehler"), tr(f"Fahrt konnte nicht eingereicht werden:\n\n{str(e)}"))
    
    def _prepare_ride_data(self) -> Dict:
        """Prepare ride data from form fields"""
        driver_id = self.driver_cb.currentData()
        
        # Combine date and time
        pickup_date = self.date_edit.date()
        pickup_time = self.time_edit.time()
        pickup_datetime = QDateTime(pickup_date, pickup_time)
        
        return {
            'company_id': self.company_id,
            'driver_id': driver_id,
            'pickup_time': pickup_datetime.toString("yyyy-MM-dd hh:mm:ss"),
            'pickup_location': self.pickup_le.text().strip(),
            'destination': self.dest_le.text().strip(),
            'vehicle_plate': self.vehicle_le.text().strip(),
            'passengers': self.passengers_spin.value(),
            'distance_km': self.distance_spin.value(),
            'revenue': self.fare_spin.value(),
            'notes': self.notes_te.toPlainText().strip(),
            'status': 'Pending'
        }
    
    def refresh_data(self):
        """Refresh data when company changes"""
        self.load_drivers()
