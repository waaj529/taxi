import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QDateEdit, QComboBox, QHeaderView, QGroupBox, QGridLayout, 
    QFileDialog, QMessageBox, QApplication, QProgressDialog
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor, QBrush

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Adjust import path based on project structure
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection # Ensure this import works
from core.payroll_calculator import PayrollCalculator
from core.translation_manager import tr

class PayrollView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.company_id = company_id
        self.db = get_db_connection()
        
        # Improved error handling for PayrollCalculator initialization
        try:
            self.payroll_calculator = PayrollCalculator(self.db)
        except Exception as e:
            print(f"Error initializing PayrollCalculator: {e}")
            self.payroll_calculator = None
            
        self.drivers_map = self._load_drivers()
        self.rules = self._load_rules()
        self.payroll_data = [] # To store calculated data for export
        self.init_ui()

    def _load_drivers(self):
        drivers = {tr("Alle Fahrer"): None}
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT id, name FROM drivers WHERE status = 'Active' ORDER BY name")
            for row in cursor.fetchall():
                drivers[row["name"]] = row["id"]
        except Exception as e:
            print(f"Error loading drivers: {e}")
        return drivers

    def _load_rules(self):
        rules = {}
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT rule_name, rule_value, enabled FROM rules")
            for row in cursor.fetchall():
                if row["enabled"]:
                    try:
                        # Attempt to convert to float or int if possible
                        val = float(row["rule_value"])
                        if val.is_integer():
                            val = int(val)
                        rules[row["rule_name"]] = val
                    except (ValueError, TypeError):
                        rules[row["rule_name"]] = row["rule_value"] # Keep as string if conversion fails
        except Exception as e:
            print(f"Error loading rules: {e}")
        return rules

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Period Selection & Filters --- 
        filter_group = QGroupBox(tr("Abrechnungszeitraum & Filter"))
        filter_layout = QGridLayout(filter_group)

        self.period_combo = QComboBox()
        self.period_combo.addItems([tr("Wöchentlich"), tr("Monatlich")])
        self.period_combo.currentIndexChanged.connect(self.update_date_editors)

        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")

        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")

        # Fixed driver selection
        self.driver_filter_combo = QComboBox()
        for name, driver_id in self.drivers_map.items():
            self.driver_filter_combo.addItem(name, driver_id)

        calculate_button = QPushButton(tr("Lohnabrechnung berechnen"))
        calculate_button.clicked.connect(self.calculate_payroll)

        filter_layout.addWidget(QLabel(tr("Zeitraumtyp:")), 0, 0)
        filter_layout.addWidget(self.period_combo, 0, 1)
        filter_layout.addWidget(QLabel(tr("Startdatum:")), 1, 0)
        filter_layout.addWidget(self.start_date_edit, 1, 1)
        filter_layout.addWidget(QLabel(tr("Enddatum:")), 1, 2)
        filter_layout.addWidget(self.end_date_edit, 1, 3)
        filter_layout.addWidget(QLabel(tr("Fahrer:")), 2, 0)
        filter_layout.addWidget(self.driver_filter_combo, 2, 1)
        filter_layout.addWidget(calculate_button, 3, 0, 1, 4) # Span button

        main_layout.addWidget(filter_group)
        self.update_date_editors() # Set initial dates based on default period

        # --- Summary Statistics --- 
        summary_group = QGroupBox(tr("Zusammenfassung"))
        summary_layout = QGridLayout(summary_group)
        self.total_drivers_label = QLabel(tr("Fahrer insgesamt bezahlt: 0"))
        self.total_payroll_label = QLabel(tr("Gesamtlohn: €0,00"))
        summary_layout.addWidget(self.total_drivers_label, 0, 0)
        summary_layout.addWidget(self.total_payroll_label, 0, 1)
        main_layout.addWidget(summary_group)

        # --- Payroll Table --- 
        self.payroll_table = QTableWidget()
        self.payroll_table.setColumnCount(7) # Driver, Period, Hours, Base Pay, Bonuses, Total Pay, Compliance
        self.payroll_table.setHorizontalHeaderLabels([tr("Fahrer"), tr("Zeitraum"), tr("Stunden"), tr("Grundlohn"), tr("Boni"), tr("Gesamtlohn"), tr("Compliance")])
        self.payroll_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payroll_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payroll_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.payroll_table)

        # --- Export Buttons --- 
        export_layout = QHBoxLayout()
        export_excel_button = QPushButton(tr("Nach Excel exportieren"))
        export_excel_button.clicked.connect(self.export_to_excel)
        export_pdf_button = QPushButton(tr("Nach PDF exportieren (Stundenzettel)"))
        export_pdf_button.clicked.connect(self.export_to_pdf)
        export_layout.addStretch()
        export_layout.addWidget(export_excel_button)
        export_layout.addWidget(export_pdf_button)
        main_layout.addLayout(export_layout)

    def update_date_editors(self):
        period_type = self.period_combo.currentText()
        today = QDate.currentDate()
        if tr("Wöchentlich") in period_type:
            start_of_week = today.addDays(-(today.dayOfWeek() % 7)) # Assuming week starts Sunday
            self.start_date_edit.setDate(start_of_week)
            self.end_date_edit.setDate(start_of_week.addDays(6))
        elif tr("Monatlich") in period_type:
            start_of_month = QDate(today.year(), today.month(), 1)
            self.start_date_edit.setDate(start_of_month)
            self.end_date_edit.setDate(start_of_month.addMonths(1).addDays(-1))

    def calculate_payroll(self):
        """Enhanced payroll calculation using the comprehensive payroll engine with proper dialog management"""
        if not self.db:
            QMessageBox.critical(self, tr("Fehler"), tr("Datenbankverbindung nicht verfügbar"))
            return
            
        if not self.payroll_calculator:
            QMessageBox.critical(self, tr("Fehler"), tr("Lohnberechnungs-Engine nicht verfügbar"))
            return

        # Get selected period
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        # Get selected drivers (All Drivers vs specific driver)
        if self.driver_filter_combo.currentText() == tr("Alle Fahrer"):
            try:
                cursor = self.db.cursor()
                cursor.execute("SELECT id, name FROM drivers WHERE status='Active' ORDER BY name")
                drivers_to_process = [(row['id'], row['name']) for row in cursor.fetchall()]
                
                if not drivers_to_process:
                    QMessageBox.warning(self, tr("Warnung"), tr("Keine aktiven Fahrer gefunden."))
                    return
                    
            except Exception as e:
                QMessageBox.critical(self, tr("Fehler"), tr(f"Fahrer konnten nicht abgerufen werden: {e}"))
                return
        else:
            driver_id = self.driver_filter_combo.currentData()
            if driver_id:
                drivers_to_process = [(driver_id, self.driver_filter_combo.currentText())]
            else:
                QMessageBox.warning(self, tr("Warnung"), tr("Ungültige Fahrerauswahl."))
                return

        # Calculate payroll for each driver
        payroll_results = []
        total_company_pay = 0
        total_company_hours = 0
        compliance_issues = 0
        failed_calculations = []

        # Create improved progress dialog with better cancel handling
        progress_dialog = QProgressDialog(
            tr("Lohndaten werden berechnet..."), 
            tr("Abbrechen"), 
            0, 
            len(drivers_to_process), 
            self
        )
        progress_dialog.setWindowTitle(tr("Lohnabrechnung wird verarbeitet"))
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(500)  # Show after 500ms
        progress_dialog.setValue(0)
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)

        # Process each driver with comprehensive error handling
        calculation_successful = False
        
        try:
            for i, (driver_id, driver_name) in enumerate(drivers_to_process):
                # Check if user cancelled early in the loop
                if progress_dialog.wasCanceled():
                    print(f"User cancelled payroll calculation at driver {i+1}/{len(drivers_to_process)}")
                    break
                
                progress_dialog.setLabelText(tr(f"Verarbeite {driver_name} ({i+1}/{len(drivers_to_process)})..."))
                progress_dialog.setValue(i)
                QApplication.processEvents()  # Keep UI responsive
                
                try:
                    # Attempt payroll calculation for this driver
                    print(f"Calculating payroll for driver {driver_name} (ID: {driver_id})")
                    payroll_data = self.payroll_calculator.calculate_driver_payroll(
                        driver_id, start_date, end_date
                    )
                    
                    payroll_results.append(payroll_data)
                    total_company_pay += payroll_data['total_pay']
                    total_company_hours += payroll_data['work_hours']['total_hours']
                    
                    if not payroll_data['compliance']['is_compliant']:
                        compliance_issues += 1
                    
                    calculation_successful = True
                    print(f"Successfully calculated payroll for {driver_name}")
                        
                except Exception as driver_error:
                    error_msg = f"Payroll calculation failed for {driver_name}: {str(driver_error)}"
                    print(f"Debug - {error_msg}")
                    failed_calculations.append((driver_name, str(driver_error)))
                    # Continue with other drivers rather than stopping completely
                    continue
            
            # Mark progress as complete
            progress_dialog.setValue(len(drivers_to_process))
            
        except Exception as general_error:
            print(f"Debug - General payroll calculation error: {general_error}")
            QMessageBox.critical(self, tr("Schwerwiegender Fehler"), 
                               tr(f"Unerwarteter Fehler bei der Lohnberechnung: {general_error}"))
        finally:
            # Always ensure progress dialog is properly closed
            if progress_dialog:
                progress_dialog.close()
                progress_dialog.deleteLater()

        # Handle user cancellation
        if progress_dialog.wasCanceled() and not calculation_successful:
            QMessageBox.information(self, tr("Abgebrochen"), tr("Lohnberechnung wurde vom Benutzer abgebrochen."))
            return

        # Check if we have any successful results
        if not payroll_results:
            error_details = ""
            if failed_calculations:
                error_details = tr("\n\nFehlerdetails:\n") + "\n".join([f"• {name}: {error}" for name, error in failed_calculations[:5]])
                if len(failed_calculations) > 5:
                    error_details += tr(f"\n... und {len(failed_calculations) - 5} weitere Fehler")
            
            QMessageBox.warning(self, tr("Keine Daten"), 
                              tr("Für den ausgewählten Zeitraum konnten keine Lohndaten berechnet werden.") + error_details)
            return

        # Store payroll data for export
        self.payroll_data = payroll_results

        # Display results in the table
        self._display_payroll_results(payroll_results)
        
        # Update summary
        self._update_summary(len(payroll_results), total_company_pay, total_company_hours, compliance_issues)
        
        # Show completion message with details about any failures
        avg_hourly = total_company_pay / total_company_hours if total_company_hours > 0 else 0
        
        summary_msg = tr(f"✅ Lohnberechnung abgeschlossen!\n\n"
                      f"📊 Zusammenfassung für {start_date} bis {end_date}:\n"
                      f"• Erfolgreich verarbeitet: {len(payroll_results)} Fahrer\n"
                      f"• Gesamtstunden: {total_company_hours:.1f}\n"
                      f"• Gesamtlohn: €{total_company_pay:.2f}\n"
                      f"• Durchschnitt pro Stunde: €{avg_hourly:.2f}\n"
                      f"• Compliance-Probleme: {compliance_issues}")
        
        if failed_calculations:
            summary_msg += tr(f"\n\n⚠️ {len(failed_calculations)} Fahrer konnten nicht verarbeitet werden")
        
        if compliance_issues > 0:
            summary_msg += tr(f"\n\n⚠️ {compliance_issues} Fahrer haben Mindestlohn-Compliance-Probleme!")
            
        QMessageBox.information(self, tr("Lohnabrechnung abgeschlossen"), summary_msg)

    def _display_payroll_results(self, payroll_results):
        """Display payroll results in the table with enhanced details"""
        self.payroll_table.setRowCount(len(payroll_results))
        
        for row, data in enumerate(payroll_results):
            # Driver name
            self.payroll_table.setItem(row, 0, QTableWidgetItem(data['driver_name']))
            
            # Period display
            period_text = f"{data['period_start']} bis {data['period_end']}"
            self.payroll_table.setItem(row, 1, QTableWidgetItem(period_text))
            
            # Total hours with breakdown - Fixed: use correct keys from PayrollCalculator
            hours_text = f"{data['work_hours']['total_hours']:.1f}h"
            if data['work_hours']['night_hours'] > 0:
                hours_text += f" ({data['work_hours']['night_hours']:.1f}h Nacht)"
            self.payroll_table.setItem(row, 2, QTableWidgetItem(hours_text))
            
            # Base pay
            base_pay_item = QTableWidgetItem(f"€{data['base_pay']:.2f}")
            self.payroll_table.setItem(row, 3, base_pay_item)
            
            # Bonuses with breakdown
            bonuses = data['bonuses']
            bonus_text = f"€{bonuses['total_bonuses']:.2f}"
            if bonuses['total_bonuses'] > 0:
                breakdown = []
                if bonuses['night_bonus'] > 0:
                    breakdown.append(f"Nacht: €{bonuses['night_bonus']:.2f}")
                if bonuses['weekend_bonus'] > 0:
                    breakdown.append(f"Wochenende: €{bonuses['weekend_bonus']:.2f}")
                if bonuses['holiday_bonus'] > 0:
                    breakdown.append(f"Feiertag: €{bonuses['holiday_bonus']:.2f}")
                if bonuses['performance_bonus'] > 0:
                    breakdown.append(f"Leistung: €{bonuses['performance_bonus']:.2f}")
                
                if breakdown:
                    bonus_text += f" ({'; '.join(breakdown)})"
            
            bonus_item = QTableWidgetItem(bonus_text)
            self.payroll_table.setItem(row, 4, bonus_item)
            
            # Total pay
            total_pay_item = QTableWidgetItem(f"€{data['total_pay']:.2f}")
            if not data['compliance']['is_compliant']:
                total_pay_item.setBackground(QBrush(QColor("#ffebee")))  # Light red for compliance issues
            self.payroll_table.setItem(row, 5, total_pay_item)
            
            # Compliance status
            compliance = data['compliance']
            if compliance['is_compliant']:
                status_item = QTableWidgetItem(tr("✅ Konform"))
                status_item.setBackground(QBrush(QColor("#e8f5e8")))  # Light green
            else:
                status_item = QTableWidgetItem(tr(f"⚠️ Verstoß (€{compliance['shortfall']:.2f} zu wenig)"))
                status_item.setBackground(QBrush(QColor("#ffebee")))  # Light red
                status_item.setToolTip(compliance['warning'])
            
            self.payroll_table.setItem(row, 6, status_item)

    def _update_summary(self, total_drivers, total_pay, total_hours, compliance_issues):
        """Update summary labels with comprehensive statistics"""
        self.total_drivers_label.setText(tr(f"Fahrer insgesamt bezahlt: {total_drivers}"))
        self.total_payroll_label.setText(tr(f"Gesamtlohn: €{total_pay:.2f}"))

    def export_to_excel(self):
        if not self.payroll_data:
            QMessageBox.warning(self, tr("Keine Daten"), tr("Keine Lohndaten zum Exportieren vorhanden. Bitte zuerst berechnen."))
            return

        file_path, _ = QFileDialog.getSaveFileName(self, tr("Lohndaten speichern"), "", tr("Excel-Dateien (*.xlsx)"))
        if file_path:
            try:
                # Create simplified export data with corrected key references
                export_data = []
                for item in self.payroll_data:
                    export_data.append({
                        tr('Fahrer'): item['driver_name'],
                        tr('Zeitraum Start'): item['period_start'],
                        tr('Zeitraum Ende'): item['period_end'],
                        tr('Gesamtstunden'): item['work_hours']['total_hours'],  # Fixed: use correct key
                        tr('Reguläre Stunden'): item['work_hours']['regular_hours'],
                        tr('Nachtstunden'): item['work_hours']['night_hours'],
                        tr('Wochenendstunden'): item['work_hours']['weekend_hours'],
                        tr('Feiertagsstunden'): item['work_hours']['holiday_hours'],
                        tr('Grundlohn'): item['base_pay'],
                        tr('Boni gesamt'): item['bonuses']['total_bonuses'],
                        tr('Nachtbonus'): item['bonuses']['night_bonus'],
                        tr('Wochenendbonus'): item['bonuses']['weekend_bonus'],
                        tr('Feiertagsbonus'): item['bonuses']['holiday_bonus'],
                        tr('Leistungsbonus'): item['bonuses']['performance_bonus'],
                        tr('Gesamtlohn'): item['total_pay'],
                        tr('Compliance'): tr('Konform') if item['compliance']['is_compliant'] else tr('Verstoß'),
                        tr('Fahrten gesamt'): item['total_rides'],
                        tr('Compliance-Rate'): item['compliance_rate'],
                        tr('Umsatz generiert'): item['revenue_generated']
                    })
                
                df = pd.DataFrame(export_data)
                df.to_excel(file_path, index=False, engine="openpyxl")
                QMessageBox.information(self, tr("Export erfolgreich"), tr(f"Lohndaten exportiert nach {file_path}"))
            except Exception as e:
                QMessageBox.critical(self, tr("Export-Fehler"), tr(f"Export nach Excel fehlgeschlagen: {e}"))
                print(f"Excel export error: {e}")

    def export_to_pdf(self):
        if not self.payroll_data:
            QMessageBox.warning(self, tr("Keine Daten"), tr("Keine Lohndaten zum Exportieren vorhanden. Bitte zuerst berechnen."))
            return

        file_path, _ = QFileDialog.getSaveFileName(self, tr("Stundenzettel speichern"), "", tr("PDF-Dateien (*.pdf)"))
        if file_path:
            try:
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []

                for driver_data in self.payroll_data:
                    story.append(Paragraph(tr(f"Stundenzettel: {driver_data['driver_name']}"), styles['h1']))
                    story.append(Paragraph(tr(f"Zeitraum: {driver_data['period_start']} bis {driver_data['period_end']}"), styles['h2']))
                    story.append(Spacer(1, 12))

                    # Summary Table
                    summary_data = [
                        [tr("Gesamtstunden"), f"{driver_data['work_hours']['total_hours']:.2f}"],
                        [tr("Grundlohn"), f"€{driver_data['base_pay']:.2f}"],
                        [tr("Boni"), f"€{driver_data['bonuses']['total_bonuses']:.2f}"],
                        [tr("Gesamtlohn"), f"€{driver_data['total_pay']:.2f}"],
                        [tr("Compliance"), tr('Konform') if driver_data['compliance']['is_compliant'] else tr('Verstoß')]
                    ]
                    summary_table = Table(summary_data, colWidths=[100, 200])
                    summary_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(summary_table)
                    story.append(Spacer(1, 24))

                    # Add page break for next driver if needed
                    from reportlab.platypus import PageBreak
                    story.append(PageBreak())
                
                # Remove last page break if it exists
                if story and isinstance(story[-1], PageBreak):
                    story.pop()

                doc.build(story)
                QMessageBox.information(self, tr("Export erfolgreich"), tr(f"Stundenzettel exportiert nach {file_path}"))

            except Exception as e:
                QMessageBox.critical(self, tr("Export-Fehler"), tr(f"Export nach PDF fehlgeschlagen: {e}"))
                print(f"PDF export error: {e}")

    def closeEvent(self, event):
        if self.db:
            self.db.close()
        super().closeEvent(event)

    def refresh_data(self):
        """Refresh data when company changes"""
        # Refresh any data that might be company-specific
        pass

# Example of how to run this view standalone for testing
if __name__ == '__main__':
    # Ensure DB exists for testing
    from core.database import initialize_database
    db_path = os.path.join(PROJECT_ROOT, 'ride_guardian.db')
    if not os.path.exists(db_path):
        print("Initializing DB for testing...")
        initialize_database()
        # Add dummy data if needed

    app = QApplication(sys.argv)
    view = PayrollView()
    view.setWindowTitle("Payroll Calculator Test")
    view.setGeometry(100, 100, 800, 600)
    view.show()
    sys.exit(app.exec())

