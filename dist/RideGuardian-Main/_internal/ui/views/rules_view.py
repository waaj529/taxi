import sys
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox, QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt

# Adjust import path based on project structure
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection # Ensure this import works
from core.translation_manager import tr

class RulesView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.company_id = company_id
        self.db = get_db_connection()
        self.rule_widgets = {} # Dictionary to store input widgets for easy access
        self.init_ui()
        self.load_rules()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Scroll Area for Rules --- 
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # --- Rule Sections --- 
        # Distance Rules
        distance_group = QGroupBox(tr("Entfernungsregeln"))
        distance_layout = QGridLayout(distance_group)
        self.add_rule_input(distance_layout, 0, "max_pickup_distance", tr("Max. Abholentfernung (km):"), tr("Maximale Entfernung vom aktuellen Standort des Fahrers zur Abholung erlaubt."), QDoubleSpinBox, {"decimals": 1, "minimum": 0, "maximum": 100, "suffix": " km"})
        self.add_rule_input(distance_layout, 1, "max_next_job_distance", tr("Max. Entfernung nächster Auftrag (km):"), tr("Maximale Entfernung für die Annahme des nächsten Auftrags nach dem Absetzen."), QDoubleSpinBox, {"decimals": 1, "minimum": 0, "maximum": 100, "suffix": " km"})
        self.add_rule_input(distance_layout, 2, "max_hq_deviation", tr("Max. HQ-Abweichung (km):"), tr("Maximal erlaubte Abweichung von der Route zum Hauptsitz."), QDoubleSpinBox, {"decimals": 1, "minimum": 0, "maximum": 50, "suffix": " km"})
        scroll_layout.addWidget(distance_group)

        # Time Rules
        time_group = QGroupBox(tr("Zeitregeln"))
        time_layout = QGridLayout(time_group)
        self.add_rule_input(time_layout, 0, "time_tolerance_minutes", tr("Zeittoleranz (Minuten):"), tr("Erlaubte Verspätung in Minuten für Abhol-/Absetzzeiten."), QSpinBox, {"minimum": 0, "maximum": 60, "suffix": " min"})
        # Add more time rules if needed (e.g., max shift length)
        scroll_layout.addWidget(time_group)

        # Bonus & Pay Rules
        pay_group = QGroupBox(tr("Bonus- und Lohnregeln"))
        pay_layout = QGridLayout(pay_group)
        self.add_rule_input(pay_layout, 0, "night_bonus_rate", tr("Nachtschichtbonus-Satz (%):"), tr("Prozentbonus für Fahrten während der Nachtstunden."), QDoubleSpinBox, {"decimals": 1, "minimum": 0, "maximum": 100, "suffix": " %"})
        self.add_rule_input(pay_layout, 1, "weekend_bonus_rate", tr("Wochenendbonus-Satz (%):"), tr("Prozentbonus für Fahrten am Wochenende."), QDoubleSpinBox, {"decimals": 1, "minimum": 0, "maximum": 100, "suffix": " %"})
        self.add_rule_input(pay_layout, 2, "holiday_bonus_rate", tr("Feiertagsbonus-Satz (%):"), tr("Prozentbonus für Fahrten an Feiertagen."), QDoubleSpinBox, {"decimals": 1, "minimum": 0, "maximum": 100, "suffix": " %"})
        self.add_rule_input(pay_layout, 3, "minimum_wage_hourly", tr("Mindestlohn (pro Stunde):"), tr("Mindestlohngarantie pro Stunde."), QDoubleSpinBox, {"decimals": 2, "minimum": 0, "maximum": 100, "prefix": "€"})
        scroll_layout.addWidget(pay_group)

        # Exemptions
        exemptions_group = QGroupBox(tr("Ausnahmen"))
        exemptions_layout = QGridLayout(exemptions_group)
        self.add_rule_input(exemptions_layout, 0, "exempt_reserved_rides", tr("Reservierte Fahrten ausschließen:"), tr("Vorbuchte/reservierte Fahrten von bestimmten Regeln ausschließen (z.B. Entfernung)."), QCheckBox)
        # Add more exemptions if needed
        scroll_layout.addWidget(exemptions_group)

        scroll_layout.addStretch() # Push groups to the top

        # --- Action Buttons --- 
        button_layout = QHBoxLayout()
        save_button = QPushButton(tr("Änderungen speichern"))
        save_button.clicked.connect(self.save_rules)
        reset_button = QPushButton(tr("Auf Standard zurücksetzen")) # Or Reset to Saved
        reset_button.clicked.connect(self.load_rules) # Reloads saved values

        button_layout.addStretch()
        button_layout.addWidget(reset_button)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

    def add_rule_input(self, layout, row, rule_name, label_text, tooltip, widget_type, widget_params=None):
        """Helper function to add a rule input row to a layout."""
        label = QLabel(label_text)
        label.setToolTip(tooltip)
        
        if widget_type == QCheckBox:
            widget = QCheckBox()
            widget.setToolTip(tooltip)
            layout.addWidget(widget, row, 1, 1, 2) # Span checkbox across value/unit columns
        else:
            widget = widget_type()
            widget.setToolTip(tooltip)
            if widget_params:
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setMinimum(widget_params.get("minimum", 0))
                    widget.setMaximum(widget_params.get("maximum", 1000))
                    if "decimals" in widget_params: widget.setDecimals(widget_params["decimals"])
                    if "prefix" in widget_params: widget.setPrefix(widget_params["prefix"])
                    if "suffix" in widget_params: widget.setSuffix(widget_params["suffix"])
                elif isinstance(widget, QLineEdit):
                     widget.setPlaceholderText(widget_params.get("placeholder", ""))
            
            # Set a reasonable fixed width for numeric inputs
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                 widget.setFixedWidth(120)
                 layout.addWidget(widget, row, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            else:
                 layout.addWidget(widget, row, 1)

            # Add explanation/description label
            explanation_label = QLabel(tooltip)
            explanation_label.setStyleSheet("color: #555; font-size: 9pt;")
            explanation_label.setWordWrap(True)
            layout.addWidget(explanation_label, row, 2)

        layout.addWidget(label, row, 0)
        self.rule_widgets[rule_name] = widget # Store widget for easy access

    def load_rules(self):
        """Load rules from database and populate the form"""
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT rule_name, rule_value FROM rules WHERE company_id = ? ORDER BY rule_name", (self.company_id,))
            rules = cursor.fetchall()
            
            # Convert to dictionary for easier access
            rules_dict = {rule['rule_name']: rule['rule_value'] for rule in rules}
            
            # Populate form fields with existing values using rule_widgets
            for rule_name, widget in self.rule_widgets.items():
                rule_value = rules_dict.get(rule_name)
                
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(int(rule_value)) if rule_value else False)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    try:
                        widget.setValue(float(rule_value) if rule_value else widget.minimum())
                    except (ValueError, TypeError):
                        widget.setValue(widget.minimum())
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(rule_value) if rule_value else "")
            
        except Exception as e:
            QMessageBox.critical(self, tr("Datenbankfehler"), tr(f"Regeln konnten nicht geladen werden: {str(e)}"))
            print(f"Error loading rules: {e}")

    def save_rules(self):
        """Save rules to database"""
        try:
            cursor = self.db.cursor()
            
            # Get all form values from rule_widgets
            rules_values = []
            
            for rule_name, widget in self.rule_widgets.items():
                if isinstance(widget, QCheckBox):
                    value = str(1 if widget.isChecked() else 0)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    value = str(widget.value())
                elif isinstance(widget, QLineEdit):
                    value = widget.text()
                else:
                    value = ""
                
                rules_values.append((rule_name, value))
            
            # Update each rule
            for rule_name, rule_value in rules_values:
                cursor.execute("""
                    INSERT OR REPLACE INTO rules (company_id, rule_name, rule_value)
                    VALUES (?, ?, ?)
                """, (self.company_id, rule_name, rule_value))
            
            self.db.commit()
            QMessageBox.information(self, tr("Erfolg"), tr("Regeln erfolgreich gespeichert!"))
            
        except Exception as e:
            QMessageBox.critical(self, tr("Datenbankfehler"), tr(f"Regeln konnten nicht gespeichert werden: {str(e)}"))
            print(f"Error saving rules: {e}")

    def closeEvent(self, event):
        """Ensure database connection is closed when the widget is closed."""
        if self.db:
            self.db.close()
        super().closeEvent(event)

    def refresh_data(self):
        """Refresh data when company changes"""
        self.load_rules()

# Example of how to run this view standalone for testing
if __name__ == '__main__':
    # Ensure DB exists for testing
    from core.database import initialize_database
    db_path = os.path.join(PROJECT_ROOT, 'ride_guardian.db')
    if not os.path.exists(db_path):
        print("Initializing DB for testing...")
        initialize_database()
        # Add default rules if needed during init

    app = QApplication(sys.argv)
    view = RulesView()
    view.setWindowTitle("Rule Configuration Test")
    view.setGeometry(100, 100, 700, 600)
    view.show()
    sys.exit(app.exec())

