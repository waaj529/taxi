import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QProgressBar, QTableWidget, QTableWidgetItem, QTextEdit, QMessageBox,
    QHeaderView, QComboBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Assuming database functions are in core.database
# Adjust the import path based on your project structure
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection
from core.ride_validator import RideValidator
from core.translation_manager import tr

class ImportWorker(QThread):
    """ Worker thread for processing the Excel file to avoid freezing the GUI."""
    progress = pyqtSignal(int)
    results = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, import_mode):
        super().__init__()
        self.file_path = file_path
        self.import_mode = import_mode
        self.db = None
        self.required_columns = ["Driver Name", "Date/Time", "Pickup Address", "Destination", "Vehicle Plate"]

    def run(self):
        try:
            # Connect to the database
            self.db = get_db_connection()

            df = pd.read_excel(self.file_path, engine='openpyxl')
            self.progress.emit(10)

            # Basic validation: Check for required columns
            missing_cols = [col for col in self.required_columns if col not in df.columns]
            if missing_cols:
                self.error.emit(tr(f"Fehlende erforderliche Spalten: {', '.join(missing_cols)}"))
                return

            total_rows = len(df)
            valid_rides = 0
            invalid_rides_details = []
            imported_rides = []

            validator = RideValidator(self.db)

            for index, row in df.iterrows():
                # More specific validation can be added here (e.g., date format, non-empty fields)
                driver_name = row.get("Driver Name")
                pickup_time = str(row.get("Date/Time")) # Convert to string, ideally parse/validate date
                pickup_loc = row.get("Pickup Address")
                destination = row.get("Destination")
                vehicle_plate = row.get("Vehicle Plate")

                # Basic check for non-empty essential fields
                if not all([driver_name, pickup_time, pickup_loc, destination, vehicle_plate]):
                    invalid_rides_details.append(tr(f"Zeile {index + 2}: Wichtige Daten fehlen."))
                    continue

                try:
                    # Get driver_id (or create driver if not exists? - Requires decision)
                    cursor = self.db.cursor()
                    cursor.execute("SELECT id FROM drivers WHERE name = ?", (driver_name,))
                    driver_result = cursor.fetchone()
                    if driver_result:
                        driver_id = driver_result['id']
                    else:
                        # Option 2: Create driver if not exists (using default values)
                        cursor.execute("INSERT INTO drivers (name, vehicle, status) VALUES (?, ?, ?)",
                                       (driver_name, vehicle_plate, 'Active'))
                        driver_id = cursor.lastrowid
                        print(f"Created new driver: {driver_name}") # Log or notify

                    # Validate ride data
                    ride_data = {
                        'driver_id': driver_id,
                        'pickup_time': pickup_time,
                        'pickup_location': pickup_loc,
                        'destination': destination,
                        'vehicle_plate': vehicle_plate,
                        'revenue': row.get("Fare", 0),
                        'is_reserved': row.get("Reserved", False)
                    }
                    is_valid, violations = validator.validate_ride(ride_data)

                    if not is_valid and tr("Validieren und importieren") in self.import_mode:
                        # Insert ride data with violations noted
                        cursor.execute("""
                            INSERT INTO rides (driver_id, pickup_time, pickup_location, destination, vehicle_plate, status, violations, revenue)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (driver_id, pickup_time, pickup_loc, destination, vehicle_plate, 'Violation', str(violations), ride_data.get('revenue')))
                        valid_rides += 1
                        imported_rides.append(row.to_dict())
                    elif is_valid:
                        # Insert ride data as normal
                        cursor.execute("""
                            INSERT INTO rides (driver_id, pickup_time, pickup_location, destination, vehicle_plate, status)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (driver_id, pickup_time, pickup_loc, destination, vehicle_plate, 'Imported'))
                        valid_rides += 1
                        imported_rides.append(row.to_dict())
                    # If not valid and mode is not "Validate and Import", skip the ride

                except Exception as e:
                    invalid_rides_details.append(tr(f"Zeile {index + 2}: Fehler - {e}"))

                # Update progress roughly
                progress_val = 10 + int(80 * (index + 1) / total_rows)
                self.progress.emit(progress_val)

            self.db.commit()
            self.progress.emit(100)

            results_summary = {
                "total_rows": total_rows,
                "valid_rides": valid_rides,
                "invalid_rides": total_rows - valid_rides,
                "invalid_details": invalid_rides_details,
                "imported_data_preview": imported_rides[:10] # Preview first 10 imported
            }
            self.results.emit(results_summary)

        except FileNotFoundError:
            self.error.emit(tr(f"Fehler: Datei nicht gefunden bei {self.file_path}"))
        except Exception as e:
            self.error.emit(tr(f"Ein Fehler ist während des Imports aufgetreten: {e}"))
            self.progress.emit(0)
        finally:
            if self.db:
                self.db.close()

class DataImportView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.company_id = company_id
        self.db_conn = get_db_connection()
        self.rides_data = []
        self.file_path = None
        self.preview_table = None
        self.import_progress = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Header ---
        header_label = QLabel(tr("Datenimport - Excel-Dateien"))
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(header_label)

        # --- File Selection --- 
        file_layout = QHBoxLayout()
        self.file_label = QLabel(tr("Keine Datei ausgewählt."))
        self.file_label.setStyleSheet("QLabel { font-style: italic; color: #555; }")
        select_button = QPushButton(tr("Excel-Datei auswählen (.xlsx, .xls)"))
        select_button.clicked.connect(self.select_file)
        file_layout.addWidget(QLabel(tr("Excel-Datei:")))
        file_layout.addWidget(self.file_label, 1) # Stretch label
        file_layout.addWidget(select_button)
        layout.addLayout(file_layout)

        # --- Import Options ---
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel(tr("Import-Modus:")))
        self.import_mode_combo = QComboBox()
        self.import_mode_combo.addItems([tr("Validieren und importieren"), tr("Nur validieren"), tr("Import erzwingen")])
        options_layout.addWidget(self.import_mode_combo)
        layout.addLayout(options_layout)

        # --- Import Button --- 
        self.import_button = QPushButton(tr("Import starten"))
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.start_import)
        layout.addWidget(self.import_button)

        # --- Cancel Button ---
        self.cancel_button = QPushButton(tr("Abbrechen"))
        self.cancel_button.clicked.connect(self.cancel_import)
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button)

        # --- Progress Bar --- 
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- Log Area ---
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # --- Results Area --- 
        self.results_label = QLabel(tr("Import-Ergebnisse:"))
        self.results_label.setStyleSheet("QLabel { font-weight: bold; margin-top: 10px; }")
        self.results_label.setVisible(False)
        layout.addWidget(self.results_label)

        self.stats_label = QLabel("")
        self.stats_label.setVisible(False)
        layout.addWidget(self.stats_label)

        # --- Preview Table --- 
        self.preview_table = QTableWidget()
        self.preview_table.setVisible(False)
        self.preview_table.setColumnCount(5) # Adjust based on columns
        self.preview_table.setHorizontalHeaderLabels([tr("Fahrer"), tr("Zeit"), tr("Abholung"), tr("Ziel"), tr("Fahrzeug")])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setMaximumHeight(200)
        layout.addWidget(self.preview_table)

        # --- Error Details --- 
        self.errors_label = QLabel(tr("Validierungsfehler/Probleme:"))
        self.errors_label.setStyleSheet("QLabel { font-weight: bold; color: red; margin-top: 10px; }")
        self.errors_label.setVisible(False)
        layout.addWidget(self.errors_label)

        self.error_details = QTextEdit()
        self.error_details.setReadOnly(True)
        self.error_details.setVisible(False)
        self.error_details.setMaximumHeight(150)
        self.error_details.setStyleSheet("QTextEdit { background-color: #f8f8f8; border: 1px solid #ddd; }")
        layout.addWidget(self.error_details)

        layout.addStretch() # Push elements to the top

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, tr("Excel-Datei auswählen"), "", tr("Excel-Dateien (*.xlsx *.xls)"))
        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("QLabel { color: #000; }") # Reset style
            self.import_button.setEnabled(True)
            self.reset_results_ui()

    def start_import(self):
        if not self.file_path:
            QMessageBox.warning(self, tr("Warnung"), tr("Bitte wählen Sie zuerst eine Datei aus."))
            return

        self.reset_results_ui()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.import_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        import_mode = self.import_mode_combo.currentText()

        # Run import in a separate thread
        self.import_progress = ImportWorker(self.file_path, import_mode)
        self.import_progress.progress.connect(self.update_progress)
        self.import_progress.results.connect(self.show_results)
        self.import_progress.error.connect(self.show_error)
        self.import_progress.finished.connect(self.import_finished)
        self.import_progress.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_results(self, results):
        self.results_label.setVisible(True)
        self.stats_label.setVisible(True)
        self.stats_label.setText(
            tr(f"Verarbeitete Zeilen insgesamt: {results['total_rows']} | "
            f"Erfolgreich importiert: {results['valid_rides']} | "
            f"Ungültig/Übersprungen: {results['invalid_rides']}")
        )

        if results['invalid_details']:
            self.errors_label.setVisible(True)
            self.error_details.setVisible(True)
            self.error_details.setText("\n".join(results['invalid_details']))
        else:
            self.errors_label.setVisible(False)
            self.error_details.setVisible(False)

        if results['imported_data_preview']:
            self.preview_table.setVisible(True)
            self.preview_table.setRowCount(len(results['imported_data_preview']))
            for row_idx, ride_data in enumerate(results['imported_data_preview']):
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(str(ride_data.get("Driver Name", ""))))
                self.preview_table.setItem(row_idx, 1, QTableWidgetItem(str(ride_data.get("Date/Time", ""))))
                self.preview_table.setItem(row_idx, 2, QTableWidgetItem(str(ride_data.get("Pickup Address", ""))))
                self.preview_table.setItem(row_idx, 3, QTableWidgetItem(str(ride_data.get("Destination", ""))))
                self.preview_table.setItem(row_idx, 4, QTableWidgetItem(str(ride_data.get("Vehicle Plate", ""))))
        else:
             self.preview_table.setVisible(False)

    def show_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.results_label.setVisible(True)
        self.results_label.setText(tr("Import fehlgeschlagen"))
        self.errors_label.setVisible(True)
        self.error_details.setVisible(True)
        self.error_details.setText(error_message)
        QMessageBox.critical(self, tr("Import-Fehler"), error_message)

    def import_finished(self):
        self.import_button.setEnabled(True) # Re-enable after completion or error
        self.cancel_button.setEnabled(False)
        if self.import_progress and self.import_progress.isRunning():
             self.import_progress.quit()
             self.import_progress.wait()
        self.import_progress = None # Clean up worker reference

    def cancel_import(self):
        """Cancel the current import operation"""
        if self.import_progress and self.import_progress.isRunning():
            self.import_progress.terminate()
            self.import_progress.wait()
            self.log_text.append(tr("Import vom Benutzer abgebrochen"))
        
        self.import_finished()
        self.reset_results_ui()

    def reset_results_ui(self):
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.results_label.setVisible(False)
        self.stats_label.setVisible(False)
        self.stats_label.setText("")
        self.preview_table.setVisible(False)
        self.preview_table.setRowCount(0)
        self.errors_label.setVisible(False)
        self.error_details.setVisible(False)
        self.error_details.clear()

    def refresh_data(self):
        """Refresh data when company changes"""
        # Clear any existing data
        self.rides_data = []
        self.file_path = None
        if self.preview_table:
            self.preview_table.setRowCount(0)

# Example of how to run this view standalone for testing
if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = DataImportView()
    view.setWindowTitle("Data Import Test")
    view.setGeometry(100, 100, 600, 700)
    view.show()
    sys.exit(app.exec())

