from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QTabWidget,
    QSizePolicy, QSpacerItem, QDialog, QLineEdit, QComboBox, QMessageBox,
    QDialogButtonBox, QScrollArea, QSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QFont, QPalette, QColor, QBrush
import sqlite3
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)
from core.database import get_db_connection
from core.translation_manager import tr

class AddDriverDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Fahrer hinzufügen"))
        self.setModal(True)
        self.setMinimumSize(480, 420)
        self.resize(480, 420)
        # Make dialog resizable and responsive
        self.setSizeGripEnabled(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title = QLabel(tr("Fahrer hinzufügen"))
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2c3e50; 
            margin-bottom: 10px;
            padding-bottom: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Form container with visible background
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                margin: 5px 0px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(18)

        # Driver Name Section
        name_section = QWidget()
        name_section_layout = QVBoxLayout(name_section)
        name_section_layout.setContentsMargins(0, 0, 0, 0)
        name_section_layout.setSpacing(8)
        
        name_label = QLabel(tr("Name des Fahrers") + " *")
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 13px;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        name_section_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("Vollständigen Namen des Fahrers eingeben"))
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px; 
                border: 2px solid #e9ecef; 
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
                min-height: 18px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #2196F3;
                outline: none;
                background-color: #ffffff;
            }
        """)
        name_section_layout.addWidget(self.name_edit)
        form_layout.addWidget(name_section)

        # Vehicle Plate Section
        vehicle_section = QWidget()
        vehicle_section_layout = QVBoxLayout(vehicle_section)
        vehicle_section_layout.setContentsMargins(0, 0, 0, 0)
        vehicle_section_layout.setSpacing(8)
        
        vehicle_label = QLabel(tr("Fahrzeugnummer"))
        vehicle_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 13px;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        vehicle_section_layout.addWidget(vehicle_label)
        
        self.vehicle_edit = QLineEdit()
        self.vehicle_edit.setPlaceholderText(tr("z.B.: ABC-1234"))
        self.vehicle_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px; 
                border: 2px solid #e9ecef; 
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
                min-height: 18px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #2196F3;
                outline: none;
                background-color: #ffffff;
            }
        """)
        vehicle_section_layout.addWidget(self.vehicle_edit)
        form_layout.addWidget(vehicle_section)

        # Status Section
        status_section = QWidget()
        status_section_layout = QVBoxLayout(status_section)
        status_section_layout.setContentsMargins(0, 0, 0, 0)
        status_section_layout.setSpacing(8)
        
        status_label = QLabel(tr("Status"))
        status_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 13px;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        status_section_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([tr("Aktiv"), tr("Inaktiv")])
        self.status_combo.setStyleSheet("""
            QComboBox {
                padding: 12px; 
                border: 2px solid #e9ecef; 
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
                min-height: 18px;
                color: #2c3e50;
            }
            QComboBox:focus {
                border-color: #2196F3;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                background-color: #ffffff;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #666;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e9ecef;
                background-color: #ffffff;
                selection-background-color: #2196F3;
                selection-color: white;
                outline: none;
            }
        """)
        status_section_layout.addWidget(self.status_combo)
        form_layout.addWidget(status_section)

        layout.addWidget(form_container)
        layout.addStretch()

        # Button container
        button_container = QFrame()
        button_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                margin-top: 15px;
            }
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Add stretch to push buttons to the right
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton(tr("Abbrechen"))
        cancel_btn.setMinimumSize(100, 40)
        cancel_btn.setMaximumSize(120, 40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #495057;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # OK button
        ok_btn = QPushButton(tr("OK"))
        ok_btn.setMinimumSize(100, 40)
        ok_btn.setMaximumSize(120, 40)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 2px solid #2196F3;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addWidget(button_container)

        # Make the layout responsive
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)

    def get_driver_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'vehicle': self.vehicle_edit.text().strip(),
            'status': self.status_combo.currentText()
        }

    def resizeEvent(self, event):
        """Handle resize events to maintain responsiveness"""
        super().resizeEvent(event)
        # Adjust padding based on dialog size
        if self.width() < 500:
            # Reduce margins for smaller screens
            self.layout().setContentsMargins(15, 15, 15, 15)
        else:
            # Normal margins for larger screens
            self.layout().setContentsMargins(25, 25, 25, 25)

class AddVehicleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Fahrzeug hinzufügen"))
        self.setModal(True)
        self.setMinimumSize(550, 700)
        self.resize(550, 750)
        self.setSizeGripEnabled(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title
        title = QLabel(tr("Fahrzeug hinzufügen"))
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #2c3e50; 
            margin-bottom: 10px;
            padding: 10px;
            background-color: white;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #f1f1f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
        """)

        # Content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(20)

        # Form container
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 25px;
                margin: 5px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(22)

        # Plate Number Section (Required)
        plate_section = self.create_form_section(tr("Kennzeichen") + " *", tr("Geben Sie die Fahrzeugnummer ein"), tr("z.B., B-TX 1234"), required=True)
        self.plate_edit = plate_section['widget']
        form_layout.addWidget(plate_section['container'])

        # Make and Model Section
        make_section = self.create_form_section(tr("Marke"), tr("Fahrzeughersteller"), tr("z.B., Toyota, BMW, Mercedes"))
        self.make_edit = make_section['widget']
        form_layout.addWidget(make_section['container'])

        model_section = self.create_form_section(tr("Modell"), tr("Fahrzeugmodell"), tr("z.B., Camry, X5, E-Klasse"))
        self.model_edit = model_section['widget']
        form_layout.addWidget(model_section['container'])

        # Year Section
        year_section = QWidget()
        year_section_layout = QVBoxLayout(year_section)
        year_section_layout.setContentsMargins(0, 0, 0, 0)
        year_section_layout.setSpacing(10)
        
        year_label = QLabel(tr("Baujahr"))
        year_label.setStyleSheet(self.get_label_style())
        year_section_layout.addWidget(year_label)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1990, 2030)
        self.year_spin.setValue(2020)
        self.year_spin.setStyleSheet(self.get_input_style())
        self.year_spin.setMinimumHeight(50)
        year_section_layout.addWidget(self.year_spin)
        form_layout.addWidget(year_section)

        # Color Section
        color_section = self.create_form_section(tr("Farbe"), tr("Fahrzeugfarbe"), tr("z.B., Weiß, Schwarz, Rot"))
        self.color_edit = color_section['widget']
        form_layout.addWidget(color_section['container'])

        # Status Section
        status_section = QWidget()
        status_section_layout = QVBoxLayout(status_section)
        status_section_layout.setContentsMargins(0, 0, 0, 0)
        status_section_layout.setSpacing(10)
        
        status_label = QLabel(tr("Status"))
        status_label.setStyleSheet(self.get_label_style())
        status_section_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([tr("Verfügbar"), tr("In Benutzung"), tr("Wartung")])
        self.status_combo.setStyleSheet(self.get_combo_style())
        self.status_combo.setMinimumHeight(50)
        status_section_layout.addWidget(self.status_combo)
        form_layout.addWidget(status_section)

        # Total KM Section
        km_section = QWidget()
        km_section_layout = QVBoxLayout(km_section)
        km_section_layout.setContentsMargins(0, 0, 0, 0)
        km_section_layout.setSpacing(10)
        
        km_label = QLabel(tr("Gesamt KM"))
        km_label.setStyleSheet(self.get_label_style())
        km_section_layout.addWidget(km_label)
        
        self.km_spin = QSpinBox()
        self.km_spin.setRange(0, 999999)
        self.km_spin.setValue(0)
        self.km_spin.setStyleSheet(self.get_input_style())
        self.km_spin.setMinimumHeight(50)
        km_section_layout.addWidget(self.km_spin)
        form_layout.addWidget(km_section)

        # Last Maintenance Date Section
        maintenance_section = QWidget()
        maintenance_section_layout = QVBoxLayout(maintenance_section)
        maintenance_section_layout.setContentsMargins(0, 0, 0, 0)
        maintenance_section_layout.setSpacing(10)
        
        maintenance_label = QLabel(tr("Letzte Wartung"))
        maintenance_label.setStyleSheet(self.get_label_style())
        maintenance_section_layout.addWidget(maintenance_label)
        
        self.maintenance_date = QDateEdit()
        self.maintenance_date.setDate(QDate.currentDate())
        self.maintenance_date.setCalendarPopup(True)
        self.maintenance_date.setStyleSheet(self.get_input_style())
        self.maintenance_date.setMinimumHeight(50)
        maintenance_section_layout.addWidget(self.maintenance_date)
        form_layout.addWidget(maintenance_section)

        content_layout.addWidget(form_container)
        content_layout.addStretch()

        # Button container
        button_container = QFrame()
        button_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                margin-top: 15px;
            }
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(10, 15, 10, 15)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton(tr("Abbrechen"))
        cancel_btn.setMinimumSize(120, 45)
        cancel_btn.setMaximumSize(150, 45)
        cancel_btn.setStyleSheet(self.get_cancel_button_style())
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # OK button
        ok_btn = QPushButton(tr("Hinzufügen"))
        ok_btn.setMinimumSize(120, 45)
        ok_btn.setMaximumSize(150, 45)
        ok_btn.setStyleSheet(self.get_ok_button_style())
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        content_layout.addWidget(button_container)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_form_section(self, label_text, tooltip, placeholder, required=False):
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(10)
        
        label = QLabel(label_text)
        label.setStyleSheet(self.get_label_style(required))
        label.setToolTip(tooltip)
        section_layout.addWidget(label)
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet(self.get_input_style())
        edit.setMinimumHeight(50)
        edit.setToolTip(tooltip)
        section_layout.addWidget(edit)
        
        return {'container': section, 'widget': edit}

    def get_label_style(self, required=False):
        color = "#dc3545" if required else "#2c3e50"
        return f"""
            QLabel {{
                font-weight: bold; 
                color: {color}; 
                font-size: 14px;
                background-color: transparent;
                border: none;
                padding: 5px 0px;
                margin: 0px;
            }}
        """

    def get_input_style(self):
        return """
            QLineEdit, QSpinBox, QDateEdit {
                padding: 15px; 
                border: 2px solid #e9ecef; 
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus, QSpinBox:focus, QDateEdit:focus {
                border-color: #2196F3;
                outline: none;
                background-color: #ffffff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background: #f8f9fa;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 10px;
                height: 10px;
            }
            QDateEdit::drop-down {
                border: none;
                width: 25px;
                background-color: #f8f9fa;
            }
        """

    def get_combo_style(self):
        return """
            QComboBox {
                padding: 15px; 
                border: 2px solid #e9ecef; 
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 14px;
                color: #2c3e50;
            }
            QComboBox:focus {
                border-color: #2196F3;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background-color: #f8f9fa;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e9ecef;
                background-color: #ffffff;
                selection-background-color: #2196F3;
                selection-color: white;
                outline: none;
                font-size: 14px;
            }
        """

    def get_cancel_button_style(self):
        return """
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #495057;
            }
        """

    def get_ok_button_style(self):
        return """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 2px solid #2196F3;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """

    def get_vehicle_data(self):
        return {
            'plate_number': self.plate_edit.text().strip(),
            'make': self.make_edit.text().strip(),
            'model': self.model_edit.text().strip(),
            'year': self.year_spin.value(),
            'color': self.color_edit.text().strip(),
            'status': self.status_combo.currentText(),
            'total_km': self.km_spin.value(),
            'last_maintenance_date': self.maintenance_date.date().toString('yyyy-MM-dd')
        }

    def resizeEvent(self, event):
        """Handle resize events to maintain responsiveness"""
        super().resizeEvent(event)
        # Adjust layout based on dialog size
        if self.width() < 600:
            self.layout().setContentsMargins(10, 10, 10, 10)
        else:
            self.layout().setContentsMargins(15, 15, 15, 15)

    def showEvent(self, event):
        """Center the dialog when shown"""
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(x, y)

class StatCard(QFrame):
    """Improved responsive stat card widget"""
    def __init__(self, title, value, color):
        super().__init__()
        self.title_text = title
        self.value_text = value
        self.color = color
        self.init_ui()

    def init_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {self.color};
                border-radius: 12px;
                padding: 15px;
                margin: 5px;
            }}
            QFrame:hover {{
                border-width: 3px;
                background-color: #f8f9fa;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Value label - large and prominent
        self.value_label = QLabel(self.value_text)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {self.color};
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Title label
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #666;
                font-weight: 600;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Set minimum size for responsiveness
        self.setMinimumSize(120, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def update_value(self, new_value):
        """Update the displayed value"""
        self.value_text = new_value
        self.value_label.setText(new_value)

class DriversView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.company_id = company_id
        self.db_conn = get_db_connection()
        self._adding_driver = False  # Flag to prevent multiple simultaneous operations
        self._adding_vehicle = False  # Flag to prevent multiple simultaneous operations
        self.init_ui()
        self.load_drivers()
    
    def init_ui(self):
        """Initialize the user interface with responsive design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel(tr("Fahrer- und Fahrzeugverwaltung"))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }
        """)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel(tr("Verwalten Sie Fahrer, Fahrzeuge und verfolgen Sie Leistungskennzahlen"))
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                margin-bottom: 15px;
            }
        """)
        subtitle_label.setWordWrap(True)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget for drivers and vehicles
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #f1f1f1;
                color: #555;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
        """)
        
        # Create tabs
        drivers_tab = self.create_drivers_tab()
        vehicles_tab = self.create_vehicles_tab()
        
        self.tab_widget.addTab(drivers_tab, "👨‍💼 " + tr("Fahrer"))
        self.tab_widget.addTab(vehicles_tab, "🚗 " + tr("Fahrzeuge"))
        
        # Connect tab change event to load appropriate data
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
        # Set responsive size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def on_tab_changed(self, index):
        """Handle tab change events to load appropriate data"""
        if index == 1:  # Vehicles tab
            self.load_vehicles_data()
        elif index == 0:  # Drivers tab
            self.load_drivers()

    def create_drivers_tab(self):
        """Create the drivers management tab"""
        drivers_widget = QWidget()
        layout = QVBoxLayout(drivers_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Driver statistics cards
        stats_container = QWidget()
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stats_layout = QGridLayout(stats_container)
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.total_drivers_card = StatCard(tr("Gesamtfahrer"), "0", "#3498db")
        self.active_drivers_card = StatCard(tr("Aktiv"), "0", "#27ae60")
        self.inactive_drivers_card = StatCard(tr("Inaktiv"), "0", "#e74c3c")
        self.total_rides_card = StatCard(tr("Gesamtfahrten"), "0", "#f39c12")
        
        # Responsive grid layout
        stats_layout.addWidget(self.total_drivers_card, 0, 0, 1, 1)
        stats_layout.addWidget(self.active_drivers_card, 0, 1, 1, 1)
        stats_layout.addWidget(self.inactive_drivers_card, 0, 2, 1, 1)
        stats_layout.addWidget(self.total_rides_card, 0, 3, 1, 1)
        
        # Make columns stretch equally
        for i in range(4):
            stats_layout.setColumnStretch(i, 1)
        
        layout.addWidget(stats_container)
        
        # Driver Management section
        management_layout = QVBoxLayout()
        
        # Header with title and Add Driver button
        header_layout = QHBoxLayout()
        
        header_section = QVBoxLayout()
        header_section.setSpacing(4)
        
        title_label = QLabel(tr("Fahrerverwaltung"))
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_section.addWidget(title_label)
        
        subtitle_label = QLabel(tr("Fügen Sie Fahrer hinzu, bearbeiten Sie sie und überwachen Sie die Leistung"))
        subtitle_label.setStyleSheet("font-size: 12px; color: #666;")
        subtitle_label.setWordWrap(True)
        header_section.addWidget(subtitle_label)
        
        header_layout.addLayout(header_section)
        header_layout.addStretch()
        
        add_driver_btn = QPushButton(tr("Fahrer hinzufügen"))
        add_driver_btn.setMinimumSize(120, 36)
        add_driver_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5985;
            }
        """)
        add_driver_btn.clicked.connect(self.add_driver)
        header_layout.addWidget(add_driver_btn)
        
        management_layout.addLayout(header_layout)
        
        # Table container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Drivers table
        self.drivers_table = QTableWidget()
        self.drivers_table.setColumnCount(8)
        self.drivers_table.setHorizontalHeaderLabels([
            tr("Name"), tr("Fahrzeug"), tr("Status"), tr("Schicht"), tr("Stunden"), tr("Fahrten"), tr("Einnahmen"), tr("Verstöße")
        ])
        
        # Enhanced table styling
        self.drivers_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #f0f0f0;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #f0f0f0;
                border-right: 1px solid #f8f8f8;
            }
            QTableWidget::item:selected {
                background-color: transparent !important;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
                font-size: 12px;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Set responsive column sizing
        header = self.drivers_table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setDefaultSectionSize(100)
        
        # Responsive column sizing
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Vehicle
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Shift
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Hours
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Rides
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)    # Earnings
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)    # Violations
        
        # Set specific column widths
        self.drivers_table.setColumnWidth(2, 80)   # Status
        self.drivers_table.setColumnWidth(3, 80)   # Shift
        self.drivers_table.setColumnWidth(4, 80)   # Hours
        self.drivers_table.setColumnWidth(5, 80)   # Rides
        self.drivers_table.setColumnWidth(6, 100)  # Earnings
        self.drivers_table.setColumnWidth(7, 90)   # Violations
        
        # Enable word wrap and adjust row height
        self.drivers_table.setWordWrap(True)
        self.drivers_table.verticalHeader().setDefaultSectionSize(40)
        self.drivers_table.verticalHeader().hide()
        
        table_layout.addWidget(self.drivers_table)
        management_layout.addWidget(table_container)
        layout.addLayout(management_layout)
        
        return drivers_widget

    def load_drivers(self):
        """Load and display drivers in the table"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT id, name, vehicle, status
                FROM drivers 
                WHERE company_id = ?
                ORDER BY name
            """, (self.company_id,))
            
            drivers = cursor.fetchall()
            
            # Set table row count
            self.drivers_table.setRowCount(len(drivers))
            
            # Populate table
            for row, driver in enumerate(drivers):
                self.drivers_table.setItem(row, 0, QTableWidgetItem(driver['name'] or ''))
                self.drivers_table.setItem(row, 1, QTableWidgetItem(driver['vehicle'] or tr('Kein Fahrzeug')))
                self.drivers_table.setItem(row, 2, QTableWidgetItem(driver['status'] or tr('Aktiv')))
                
                # Placeholder data for remaining columns
                self.drivers_table.setItem(row, 3, QTableWidgetItem(tr('Tag')))  # Shift
                self.drivers_table.setItem(row, 4, QTableWidgetItem('0.0h'))  # Hours
                self.drivers_table.setItem(row, 5, QTableWidgetItem('0'))  # Rides
                self.drivers_table.setItem(row, 6, QTableWidgetItem('€0.00'))  # Earnings
                self.drivers_table.setItem(row, 7, QTableWidgetItem('0'))  # Violations
                
            # Update stat cards
            self.total_drivers_card.update_value(str(len(drivers)))
            self.active_drivers_card.update_value(str(sum(1 for d in drivers if d['status'] == tr('Aktiv'))))
            self.inactive_drivers_card.update_value(str(sum(1 for d in drivers if d['status'] == tr('Inaktiv'))))
            self.total_rides_card.update_value('0')  # Placeholder
            
        except Exception as e:
            QMessageBox.critical(self, tr("Datenbankfehler"), tr("Fehler beim Laden der Fahrer") + f": {str(e)}")
            print(f"Error loading drivers: {e}")

    def create_vehicles_tab(self):
        """Create the vehicles management tab"""
        vehicles_widget = QWidget()
        vehicles_layout = QVBoxLayout(vehicles_widget)
        vehicles_layout.setContentsMargins(0, 0, 0, 0)
        vehicles_layout.setSpacing(20)
        
        # Vehicle statistics cards
        vehicle_stats_container = QWidget()
        vehicle_stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        vehicle_stats_layout = QGridLayout(vehicle_stats_container)
        vehicle_stats_layout.setSpacing(15)
        vehicle_stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.total_vehicles_card = StatCard(tr("Gesamtfahrzeuge"), "0", "#3F51B5")
        self.available_vehicles_card = StatCard(tr("Verfügbar"), "0", "#4CAF50")
        self.in_use_vehicles_card = StatCard(tr("In Benutzung"), "0", "#FF9800")
        self.maintenance_vehicles_card = StatCard(tr("Wartung"), "0", "#f44336")
        
        # Responsive grid layout
        vehicle_stats_layout.addWidget(self.total_vehicles_card, 0, 0, 1, 1)
        vehicle_stats_layout.addWidget(self.available_vehicles_card, 0, 1, 1, 1)
        vehicle_stats_layout.addWidget(self.in_use_vehicles_card, 0, 2, 1, 1)
        vehicle_stats_layout.addWidget(self.maintenance_vehicles_card, 0, 3, 1, 1)
        
        # Make columns stretch equally
        for i in range(4):
            vehicle_stats_layout.setColumnStretch(i, 1)
        
        vehicles_layout.addWidget(vehicle_stats_container)
        
        # Vehicle Management section
        vehicle_management_layout = QVBoxLayout()
        
        # Header with title and Add Vehicle button
        vehicle_header_layout = QHBoxLayout()
        
        vehicle_header_section = QVBoxLayout()
        vehicle_header_section.setSpacing(4)
        
        vehicle_title_label = QLabel(tr("Fahrzeugflottenverwaltung"))
        vehicle_title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        vehicle_header_section.addWidget(vehicle_title_label)
        
        vehicle_subtitle_label = QLabel(tr("Überwachen Sie den Fahrzeugstatus, die Wartung und die Zuordnungen"))
        vehicle_subtitle_label.setStyleSheet("font-size: 12px; color: #666;")
        vehicle_subtitle_label.setWordWrap(True)
        vehicle_header_section.addWidget(vehicle_subtitle_label)
        
        vehicle_header_layout.addLayout(vehicle_header_section)
        vehicle_header_layout.addStretch()
        
        add_vehicle_btn = QPushButton(tr("Fahrzeug hinzufügen"))
        add_vehicle_btn.setMinimumSize(120, 36)
        add_vehicle_btn.setStyleSheet("""
            QPushButton {
                background-color: #3F51B5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #303F9F;
            }
            QPushButton:pressed {
                background-color: #1A237E;
            }
        """)
        add_vehicle_btn.clicked.connect(self.add_vehicle)
        vehicle_header_layout.addWidget(add_vehicle_btn)
        
        vehicle_management_layout.addLayout(vehicle_header_layout)
        
        # Vehicle table container
        vehicle_table_container = QFrame()
        vehicle_table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        vehicle_table_layout = QVBoxLayout(vehicle_table_container)
        vehicle_table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Vehicles table
        self.vehicles_table = QTableWidget()
        self.vehicles_table.setColumnCount(8)
        self.vehicles_table.setHorizontalHeaderLabels([
            tr("Kennzeichen"), tr("Marke/Modell"), tr("Baujahr"), tr("Farbe"), tr("Status"), tr("Gesamt KM"), tr("Letzte Wartung"), tr("Zugew. Fahrer")
        ])
        
        # Enhanced table styling
        self.vehicles_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #f0f0f0;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #f0f0f0;
                border-right: 1px solid #f8f8f8;
            }
            QTableWidget::item:selected {
                background-color: transparent !important;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
                font-size: 12px;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Set responsive column sizing
        vehicles_header = self.vehicles_table.horizontalHeader()
        vehicles_header.setMinimumSectionSize(80)
        vehicles_header.setDefaultSectionSize(100)
        
        # Responsive column sizing for vehicles
        vehicles_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Plate
        vehicles_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Make/Model
        vehicles_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)            # Year
        vehicles_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Color
        vehicles_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)            # Status
        vehicles_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)            # Total KM
        vehicles_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Last Maintenance
        vehicles_header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Assigned Driver
        
        # Set specific column widths for vehicles
        self.vehicles_table.setColumnWidth(2, 80)   # Year
        self.vehicles_table.setColumnWidth(4, 100)  # Status
        self.vehicles_table.setColumnWidth(5, 100)  # Total KM
        
        # Enable word wrap and adjust row height
        self.vehicles_table.setWordWrap(True)
        self.vehicles_table.verticalHeader().setDefaultSectionSize(40)
        self.vehicles_table.verticalHeader().hide()
        
        vehicle_table_layout.addWidget(self.vehicles_table)
        vehicle_management_layout.addWidget(vehicle_table_container)
        vehicles_layout.addLayout(vehicle_management_layout)
        
        return vehicles_widget

    def load_vehicles_data(self):
        """Load and display vehicles in the table"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT plate_number, make, model, year, color, status, total_km, 
                       last_maintenance_date, current_driver_id
                FROM vehicles 
                WHERE company_id = ?
                ORDER BY plate_number
            """, (self.company_id,))
            
            vehicles = cursor.fetchall()
            
            self.vehicles_table.setRowCount(len(vehicles))
            
            # Count vehicles by status
            total_vehicles = len(vehicles)
            available_count = sum(1 for v in vehicles if v[5] == tr("Verfügbar"))
            in_use_count = sum(1 for v in vehicles if v[5] == tr("In Benutzung"))
            maintenance_count = sum(1 for v in vehicles if v[5] == tr("Wartung"))
            
            # Update stat cards
            self.total_vehicles_card.update_value(str(total_vehicles))
            self.available_vehicles_card.update_value(str(available_count))
            self.in_use_vehicles_card.update_value(str(in_use_count))
            self.maintenance_vehicles_card.update_value(str(maintenance_count))
            
            for row, vehicle in enumerate(vehicles):
                plate_number, make, model, year, color, status, total_km, last_maintenance, current_driver_id = vehicle
                
                # Get assigned driver name
                assigned_driver = "-"
                if current_driver_id:
                    cursor.execute("SELECT name FROM drivers WHERE id = ?", (current_driver_id,))
                    driver_result = cursor.fetchone()
                    if driver_result:
                        assigned_driver = driver_result[0]
                
                # Populate table row
                self.vehicles_table.setItem(row, 0, QTableWidgetItem(str(plate_number)))
                self.vehicles_table.setItem(row, 1, QTableWidgetItem(f"{make} {model}"))
                self.vehicles_table.setItem(row, 2, QTableWidgetItem(str(year)))
                self.vehicles_table.setItem(row, 3, QTableWidgetItem(str(color)))
                
                # Status with color coding
                status_item = QTableWidgetItem(str(status))
                if status == tr("Verfügbar"):
                    status_item.setBackground(QBrush(QColor("#d4edda")))
                elif status == tr("In Benutzung"):
                    status_item.setBackground(QBrush(QColor("#fff3cd")))
                elif status == tr("Wartung"):
                    status_item.setBackground(QBrush(QColor("#f8d7da")))
                self.vehicles_table.setItem(row, 4, status_item)
                
                self.vehicles_table.setItem(row, 5, QTableWidgetItem(f"{total_km} km"))
                self.vehicles_table.setItem(row, 6, QTableWidgetItem(str(last_maintenance) if last_maintenance else "-"))
                self.vehicles_table.setItem(row, 7, QTableWidgetItem(str(assigned_driver)))
                
        except Exception as e:
            print(f"Error loading vehicles: {e}")
            QMessageBox.warning(self, tr("Fehler"), f"Fehler beim Laden der Fahrzeuge: {e}")

    def add_driver(self):
        """Add a new driver"""
        if self._adding_driver:
            return
        
        self._adding_driver = True
        try:
            dialog = AddDriverDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                driver_data = dialog.get_driver_data()
                
                if not driver_data['name']:
                    QMessageBox.warning(self, tr("Fehler"), tr("Bitte geben Sie einen Fahrernamen ein."))
                    return
                
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO drivers (name, vehicle_plate, status, company_id)
                    VALUES (?, ?, ?, ?)
                """, (driver_data['name'], driver_data['vehicle'], driver_data['status'], self.company_id))
                
                self.db_conn.commit()
                self.load_drivers()
                QMessageBox.information(self, tr("Erfolg"), tr("Fahrer erfolgreich hinzugefügt."))
                
        except Exception as e:
            print(f"Error adding driver: {e}")
            QMessageBox.critical(self, tr("Fehler"), f"Fehler beim Hinzufügen des Fahrers: {e}")
        finally:
            self._adding_driver = False

    def add_vehicle(self):
        """Add a new vehicle"""
        if self._adding_vehicle:
            return
        
        self._adding_vehicle = True
        try:
            dialog = AddVehicleDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                vehicle_data = dialog.get_vehicle_data()
                
                if not vehicle_data['plate_number']:
                    QMessageBox.warning(self, tr("Fehler"), tr("Bitte geben Sie eine Fahrzeugnummer ein."))
                    return
                
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO vehicles (plate_number, make, model, year, color, status, 
                                        total_km, last_maintenance_date, company_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle_data['plate_number'],
                    vehicle_data['make'],
                    vehicle_data['model'],
                    vehicle_data['year'],
                    vehicle_data['color'],
                    vehicle_data['status'],
                    vehicle_data['total_km'],
                    vehicle_data['last_maintenance_date'],
                    self.company_id
                ))
                
                self.db_conn.commit()
                self.load_vehicles_data()
                QMessageBox.information(self, tr("Erfolg"), tr("Fahrzeug erfolgreich hinzugefügt."))
                
        except Exception as e:
            print(f"Error adding vehicle: {e}")
            QMessageBox.critical(self, tr("Fehler"), f"Fehler beim Hinzufügen des Fahrzeugs: {e}")
        finally:
            self._adding_vehicle = False

    def resizeEvent(self, event):
        """Handle resize events for responsive design"""
        super().resizeEvent(event)
        
        # Adjust layout based on window size
        current_width = self.width()
        
        # Adjust stat cards layout for smaller screens
        if hasattr(self, 'total_drivers_card') and hasattr(self, 'total_vehicles_card'):
            if current_width < 800:
                # Stack cards vertically on small screens
                pass
            else:
                # Keep horizontal layout on larger screens
                pass

    def refresh_data(self):
        """Refresh all data in the current view"""
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # Drivers tab
            self.load_drivers()
        elif current_tab == 1:  # Vehicles tab
            self.load_vehicles_data()