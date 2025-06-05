import sys
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QLineEdit, QComboBox, QDateEdit, QHeaderView, QMenu, QGroupBox, QGridLayout,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QTextEdit, QDoubleSpinBox, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate, QDateTime
from PyQt6.QtGui import QColor, QBrush, QAction

# Adjust import path based on project structure
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection 
from core.translation_manager import TranslationManager

class RideEditDialog(QDialog):
    def __init__(self, parent=None, ride_data=None, drivers_map=None):
        super().__init__(parent)
        self.ride_data = ride_data
        self.drivers_map = drivers_map or {}
        self.tm = TranslationManager()
        self.setWindowTitle(self.tm.tr("add_ride") if ride_data is None else self.tm.tr("edit_ride"))
        self.setModal(True)
        self.resize(400, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Driver selection
        self.driver_combo = QComboBox()
        driver_names = [name for name in self.drivers_map.keys() if name != self.tm.tr("all_drivers")]
        self.driver_combo.addItems(driver_names)
        form_layout.addRow(f"{self.tm.tr('driver')}:", self.driver_combo)
        
        # Vehicle plate
        self.vehicle_edit = QLineEdit()
        form_layout.addRow(f"{self.tm.tr('vehicle_plate')}:", self.vehicle_edit)
        
        # Pickup time
        self.pickup_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.pickup_time_edit.setCalendarPopup(True)
        form_layout.addRow(f"{self.tm.tr('pickup_time')}:", self.pickup_time_edit)
        
        # Pickup location
        self.pickup_location_edit = QLineEdit()
        form_layout.addRow(f"{self.tm.tr('pickup_location')}:", self.pickup_location_edit)
        
        # Destination
        self.destination_edit = QLineEdit()
        form_layout.addRow(f"{self.tm.tr('destination')}:", self.destination_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            self.tm.tr("pending"),
            self.tm.tr("in_progress"), 
            self.tm.tr("completed"),
            self.tm.tr("violation"),
            self.tm.tr("imported")
        ])
        form_layout.addRow(f"{self.tm.tr('status')}:", self.status_combo)
        
        # Violations
        self.violations_edit = QTextEdit()
        self.violations_edit.setMaximumHeight(80)
        form_layout.addRow(f"{self.tm.tr('violations')}:", self.violations_edit)
        
        # Revenue
        self.revenue_spin = QDoubleSpinBox()
        self.revenue_spin.setRange(0.0, 9999.99)
        self.revenue_spin.setDecimals(2)
        form_layout.addRow(f"{self.tm.tr('revenue')}:", self.revenue_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.tm.tr("save"))
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tm.tr("cancel"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Populate fields if editing
        if self.ride_data:
            self.populate_fields()
    
    def populate_fields(self):
        if not self.ride_data:
            return
            
        # Set driver
        driver_name = self.ride_data.get("driver_name", "")
        if driver_name in self.drivers_map:
            self.driver_combo.setCurrentText(driver_name)
        
        # Set other fields
        self.vehicle_edit.setText(self.ride_data.get("vehicle_plate", ""))
        
        pickup_time_str = self.ride_data.get("pickup_time", "")
        if pickup_time_str:
            dt = QDateTime.fromString(pickup_time_str.split('.')[0], "yyyy-MM-dd HH:mm:ss")
            if dt.isValid():
                self.pickup_time_edit.setDateTime(dt)
        
        self.pickup_location_edit.setText(self.ride_data.get("pickup_location", ""))
        self.destination_edit.setText(self.ride_data.get("destination", ""))
        
        # Map status from English to German display
        status_map = {
            "Pending": self.tm.tr("pending"),
            "In Progress": self.tm.tr("in_progress"),
            "Completed": self.tm.tr("completed"),
            "Violation": self.tm.tr("violation"),
            "Imported": self.tm.tr("imported")
        }
        english_status = self.ride_data.get("status", "Pending")
        german_status = status_map.get(english_status, english_status)
        self.status_combo.setCurrentText(german_status)
        
        self.violations_edit.setPlainText(self.ride_data.get("violations", ""))
        
        revenue = self.ride_data.get("revenue", 0.0)
        if revenue:
            self.revenue_spin.setValue(float(revenue))
    
    def get_ride_data(self):
        driver_name = self.driver_combo.currentText()
        driver_id = self.drivers_map.get(driver_name)
        
        # Map German status back to English for database
        status_reverse_map = {
            self.tm.tr("pending"): "Pending",
            self.tm.tr("in_progress"): "In Progress",
            self.tm.tr("completed"): "Completed", 
            self.tm.tr("violation"): "Violation",
            self.tm.tr("imported"): "Imported"
        }
        german_status = self.status_combo.currentText()
        english_status = status_reverse_map.get(german_status, german_status)
        
        return {
            "driver_id": driver_id,
            "vehicle_plate": self.vehicle_edit.text(),
            "pickup_time": self.pickup_time_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "pickup_location": self.pickup_location_edit.text(),
            "destination": self.destination_edit.text(),
            "status": english_status,
            "violations": self.violations_edit.toPlainText(),
            "revenue": self.revenue_spin.value()
        }

class RideMonitoringView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.company_id = company_id
        self.db_conn = get_db_connection()
        self.tm = TranslationManager()
        self.drivers_map = self._load_drivers()
        self.init_ui()
        self.setup_timer()
        self.load_ride_data()

    def _load_drivers(self):
        """Load driver names and IDs for filter dropdown."""
        drivers = {self.tm.tr("all_drivers"): None}
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM drivers WHERE company_id = ? ORDER BY name", (self.company_id,))
            for row in cursor.fetchall():
                drivers[row["name"]] = row["id"]
        except Exception as e:
            print(f"Error loading drivers: {e}")
        return drivers

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Summary Cards ---
        summary_group = QGroupBox(self.tm.tr("summary"))
        summary_layout = QGridLayout(summary_group)

        self.total_rides_label = QLabel(f"{self.tm.tr('total_rides')}: 0")
        self.active_drivers_label = QLabel(f"{self.tm.tr('active_drivers')}: 0")
        self.violations_label = QLabel(f"{self.tm.tr('violations')}: 0")
        self.compliance_label = QLabel(f"{self.tm.tr('compliance')}: N/A")

        summary_layout.addWidget(self.total_rides_label, 0, 0)
        summary_layout.addWidget(self.active_drivers_label, 0, 1)
        summary_layout.addWidget(self.violations_label, 1, 0)
        summary_layout.addWidget(self.compliance_label, 1, 1)
        main_layout.addWidget(summary_group)

        # --- Filters --- 
        filter_group = QGroupBox(self.tm.tr("filters"))
        filter_group_layout = QHBoxLayout(filter_group)

        self.driver_filter = QComboBox()
        self.driver_filter.addItems(self.drivers_map.keys())

        self.start_date_filter = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter.setCalendarPopup(True)
        self.end_date_filter = QDateEdit(QDate.currentDate())
        self.end_date_filter.setCalendarPopup(True)

        self.status_filter = QComboBox()
        self.status_filter.addItems([
            self.tm.tr("all_status"),
            self.tm.tr("pending"),
            self.tm.tr("in_progress"), 
            self.tm.tr("completed"),
            self.tm.tr("violation"),
            self.tm.tr("imported")
        ])

        apply_filter_button = QPushButton(self.tm.tr("apply_filters"))
        apply_filter_button.clicked.connect(self.load_ride_data)

        filter_group_layout.addWidget(QLabel(f"{self.tm.tr('driver')}:"))
        filter_group_layout.addWidget(self.driver_filter)
        filter_group_layout.addWidget(QLabel(f"{self.tm.tr('from')}:"))
        filter_group_layout.addWidget(self.start_date_filter)
        filter_group_layout.addWidget(QLabel(f"{self.tm.tr('to')}:"))
        filter_group_layout.addWidget(self.end_date_filter)
        filter_group_layout.addWidget(QLabel(f"{self.tm.tr('status')}:"))
        filter_group_layout.addWidget(self.status_filter)
        filter_group_layout.addWidget(apply_filter_button)
        filter_group_layout.addStretch()

        main_layout.addWidget(filter_group)

        # --- CRUD Operation Buttons ---
        crud_group = QGroupBox(self.tm.tr("record_operations"))
        crud_layout = QHBoxLayout(crud_group)
        
        self.add_button = QPushButton(self.tm.tr("add_record"))
        self.add_button.clicked.connect(self.add_record)
        self.add_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px 16px; }")
        
        self.edit_button = QPushButton(self.tm.tr("edit_record"))
        self.edit_button.clicked.connect(self.edit_record)
        self.edit_button.setStyleSheet("QPushButton { background-color: #007bff; color: white; padding: 8px 16px; }")
        
        self.delete_button = QPushButton(self.tm.tr("delete_record"))
        self.delete_button.clicked.connect(self.delete_record)
        self.delete_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; padding: 8px 16px; }")
        
        self.refresh_button = QPushButton(self.tm.tr("refresh"))
        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; padding: 8px 16px; }")
        
        self.clear_button = QPushButton(self.tm.tr("clear_all"))
        self.clear_button.clicked.connect(self.clear_all_records)
        self.clear_button.setStyleSheet("QPushButton { background-color: #6c757d; color: white; padding: 8px 16px; }")
        
        crud_layout.addWidget(self.add_button)
        crud_layout.addWidget(self.edit_button)
        crud_layout.addWidget(self.delete_button)
        crud_layout.addWidget(self.refresh_button)
        crud_layout.addWidget(self.clear_button)
        crud_layout.addStretch()
        
        main_layout.addWidget(crud_group)

        # --- Ride Table --- 
        self.ride_table = QTableWidget()
        self.ride_table.setColumnCount(8)
        self.ride_table.setHorizontalHeaderLabels([
            "ID",
            self.tm.tr("driver"),
            self.tm.tr("vehicle"),
            self.tm.tr("pickup_time"),
            self.tm.tr("route"),
            self.tm.tr("status"),
            self.tm.tr("violations"),
            self.tm.tr("revenue")
        ])
        self.ride_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ride_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ride_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ride_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ride_table.customContextMenuRequested.connect(self.show_context_menu)
        self.ride_table.itemDoubleClicked.connect(self.edit_record)

        main_layout.addWidget(self.ride_table)

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_ride_data)
        self.timer.start(30000)

    def load_ride_data(self):
        try:
            # Get filter values
            selected_driver = self.driver_filter.currentText()
            driver_id = self.drivers_map.get(selected_driver) if selected_driver != self.tm.tr("all_drivers") else None
            start_date = self.start_date_filter.date().toString("yyyy-MM-dd")
            end_date = self.end_date_filter.date().toString("yyyy-MM-dd")
            selected_status = self.status_filter.currentText()

            # Map German status to English for database query
            status_map = {
                self.tm.tr("pending"): "Pending",
                self.tm.tr("in_progress"): "In Progress",
                self.tm.tr("completed"): "Completed",
                self.tm.tr("violation"): "Violation",
                self.tm.tr("imported"): "Imported"
            }
            english_status = status_map.get(selected_status, selected_status)

            # Build query
            query = """
                SELECT r.id, r.driver_id, r.pickup_time, r.pickup_location, r.destination, r.status,
                       r.violations, r.revenue, r.vehicle_plate, d.name as driver_name
                FROM rides r
                LEFT JOIN drivers d ON r.driver_id = d.id
                WHERE r.company_id = ? AND DATE(r.pickup_time) BETWEEN ? AND ?
            """
            params = [self.company_id, start_date, end_date]

            if driver_id:
                query += " AND r.driver_id = ?"
                params.append(driver_id)

            if selected_status != self.tm.tr("all_status"):
                query += " AND r.status = ?"
                params.append(english_status)

            query += " ORDER BY r.pickup_time DESC"

            cursor = self.db_conn.cursor()
            cursor.execute(query, params)
            rides = cursor.fetchall()

            # Clear existing data
            self.ride_table.setRowCount(0)

            # Add data to table
            total_rides = len(rides)
            violation_count = 0

            # Status display mapping from English to German
            status_display_map = {
                "Pending": self.tm.tr("pending"),
                "In Progress": self.tm.tr("in_progress"),
                "Completed": self.tm.tr("completed"),
                "Violation": self.tm.tr("violation"),
                "Imported": self.tm.tr("imported")
            }

            for row_idx, ride in enumerate(rides):
                self.ride_table.insertRow(row_idx)
                
                # Check for violations
                violations = ride['violations']
                if violations and violations != '[]' and violations.strip():
                    try:
                        violations_list = json.loads(violations) if violations.startswith('[') else [violations]
                        violation_count += 1 if violations_list else 0
                    except:
                        violation_count += 1 if violations else 0

                # Populate table columns
                self.ride_table.setItem(row_idx, 0, QTableWidgetItem(str(ride['id'])))
                self.ride_table.setItem(row_idx, 1, QTableWidgetItem(ride['driver_name'] or self.tm.tr("unknown")))
                self.ride_table.setItem(row_idx, 2, QTableWidgetItem(ride['vehicle_plate'] or "N/A"))
                self.ride_table.setItem(row_idx, 3, QTableWidgetItem(ride['pickup_time'] or ""))
                
                # Format route (pickup -> destination)
                pickup = ride['pickup_location'] or "N/A"
                destination = ride['destination'] or "N/A"
                route = f"{pickup[:20]}... → {destination[:20]}..." if len(pickup) > 20 or len(destination) > 20 else f"{pickup} → {destination}"
                self.ride_table.setItem(row_idx, 4, QTableWidgetItem(route))
                
                # Display status in German
                english_status = ride['status'] or "Pending"
                german_status = status_display_map.get(english_status, english_status)
                self.ride_table.setItem(row_idx, 5, QTableWidgetItem(german_status))
                
                self.ride_table.setItem(row_idx, 6, QTableWidgetItem(str(violations or "")))
                self.ride_table.setItem(row_idx, 7, QTableWidgetItem(f"{ride['revenue']:.2f}" if ride["revenue"] is not None else "N/A"))

            # Update Summary Cards
            self.total_rides_label.setText(f"{self.tm.tr('total_rides')}: {total_rides}")
            self.violations_label.setText(f"{self.tm.tr('violations')}: {violation_count}")
            if total_rides > 0:
                compliance_rate = ((total_rides - violation_count) / total_rides) * 100
                self.compliance_label.setText(f"{self.tm.tr('compliance')}: {compliance_rate:.1f}%")
            else:
                self.compliance_label.setText(f"{self.tm.tr('compliance')}: N/A")

        except Exception as e:
            print(f"Error loading ride data: {e}")

    def show_context_menu(self, pos):
        if not self.ride_table.selectionModel().hasSelection():
            return
            
        menu = QMenu()
        view_details_action = QAction(self.tm.tr("view_ride_details"), self)
        menu.addAction(view_details_action)
        
        menu.exec(self.ride_table.mapToGlobal(pos))

    def closeEvent(self, event):
        """Ensure database connection is closed when the widget is closed."""
        if self.db_conn:
            self.db_conn.close()
        super().closeEvent(event)

    def add_record(self):
        """Add a new ride record"""
        dialog = RideEditDialog(self, None, self.drivers_map)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ride_data = dialog.get_ride_data()
            try:
                cursor = self.db_conn.cursor()

                # Check for duplicate ride
                # Note: company_id is implicitly handled if rides are company-specific in DB schema
                # or if driver_id itself is unique across companies (less likely).
                # Assuming self.company_id is the relevant company context here.
                cursor.execute("""
                    SELECT id FROM rides 
                    WHERE driver_id = ? AND pickup_time = ? AND pickup_location = ? AND destination = ? AND company_id = ?
                """, (ride_data["driver_id"], ride_data["pickup_time"], 
                      ride_data["pickup_location"], ride_data["destination"], self.company_id))
                existing_ride = cursor.fetchone()
                if existing_ride:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("duplicate_ride_error"))
                    return

                cursor.execute("""
                    INSERT INTO rides (driver_id, vehicle_plate, pickup_time, pickup_location, 
                                     destination, status, violations, revenue, company_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ride_data["driver_id"],
                    ride_data["vehicle_plate"],
                    ride_data["pickup_time"],
                    ride_data["pickup_location"],
                    ride_data["destination"],
                    ride_data["status"],
                    ride_data["violations"],
                    ride_data["revenue"],
                    self.company_id # Ensure company_id is inserted
                ))
                self.db_conn.commit()
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("ride_added_successfully"))
                self.load_ride_data()
            except Exception as e:
                QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_add_ride')}: {e}")

    def edit_record(self):
        """Edit selected ride record"""
        current_row = self.ride_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tm.tr("warning"), self.tm.tr("select_ride_to_edit"))
            return
        
        ride_id = self.ride_table.item(current_row, 0).text()
        
        # Fetch current ride data
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT r.*, d.name as driver_name 
                FROM rides r 
                LEFT JOIN drivers d ON r.driver_id = d.id 
                WHERE r.id = ?
            """, (ride_id,))
            ride_data = cursor.fetchone()
            
            if not ride_data:
                QMessageBox.warning(self, self.tm.tr("warning"), self.tm.tr("ride_not_found"))
                return
            
            dialog = RideEditDialog(self, dict(ride_data), self.drivers_map)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_ride_data()
                cursor.execute("""
                    UPDATE rides SET driver_id=?, vehicle_plate=?, pickup_time=?, 
                           pickup_location=?, destination=?, status=?, violations=?, revenue=?
                    WHERE id=?
                """, (
                    updated_data["driver_id"],
                    updated_data["vehicle_plate"],
                    updated_data["pickup_time"],
                    updated_data["pickup_location"],
                    updated_data["destination"],
                    updated_data["status"],
                    updated_data["violations"],
                    updated_data["revenue"],
                    ride_id
                ))
                self.db_conn.commit()
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("ride_updated_successfully"))
                self.load_ride_data()
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_edit_ride')}: {e}")

    def delete_record(self):
        """Delete selected ride record"""
        current_row = self.ride_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tm.tr("warning"), self.tm.tr("select_ride_to_delete"))
            return
        
        ride_id = self.ride_table.item(current_row, 0).text()
        driver_name = self.ride_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, self.tm.tr("confirm_delete"), 
            f"{self.tm.tr('confirm_delete_ride')} ID {ride_id} {self.tm.tr('for_driver')} {driver_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM rides WHERE id = ?", (ride_id,))
                self.db_conn.commit()
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("ride_deleted_successfully"))
                self.load_ride_data()
            except Exception as e:
                QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_delete_ride')}: {e}")

    def refresh_data(self):
        """Refresh data when company changes"""
        self.drivers_map = self._load_drivers()
        # Update driver filter
        self.driver_filter.clear()
        self.driver_filter.addItems(self.drivers_map.keys())
        self.load_ride_data()

    def clear_all_records(self):
        """Clear all ride records"""
        reply = QMessageBox.question(
            self, self.tm.tr("confirm_clear_all"), 
            self.tm.tr("confirm_clear_all_rides"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Double confirmation for such a destructive action
            reply2 = QMessageBox.question(
                self, self.tm.tr("final_confirmation"), 
                self.tm.tr("final_confirmation_clear_all"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("DELETE FROM rides")
                    self.db_conn.commit()
                    QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("all_rides_cleared"))
                    self.load_ride_data()
                except Exception as e:
                    QMessageBox.critical(self, self.tm.tr("error"), f"{self.tm.tr('failed_to_clear_rides')}: {e}")

