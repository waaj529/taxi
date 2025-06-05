import sys
import os

# Ensure project root in PYTHONPATH before imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QListWidget, QStackedWidget, QListWidgetItem, QMessageBox, 
                            QComboBox, QLabel, QFrame, QDialog, QDialogButtonBox, QLineEdit,
                            QFormLayout, QCheckBox, QPushButton)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSize, QTranslator, QLocale, QCoreApplication

# Core components
from core.database import initialize_database, DATABASE_PATH, get_companies, get_company_config, set_company_config
from core.translation_manager import translation_manager, tr

# Import Views
from ui.views.ride_monitoring_view import RideMonitoringView
from ui.views.ride_entry_view import RideEntryView
from ui.views.data_import_view import DataImportView
from ui.views.drivers_view import DriversView
from ui.views.payroll_view import PayrollView
from ui.views.rules_view import RulesView
from ui.views.reports_view import ReportsView

class CompanySelectionDialog(QDialog):
    def __init__(self, companies, parent=None):
        super().__init__(parent)
        self.companies = companies
        self.selected_company_id = 1
        self.setWindowTitle(tr("Unternehmen auswählen"))
        self.setModal(True)
        self.setMinimumSize(400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(tr("Bitte wählen Sie ein Unternehmen aus:"))
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Company selection
        self.company_combo = QComboBox()
        for company in self.companies:
            self.company_combo.addItem(f"{company['name']} - {company['headquarters_address']}", company['id'])
        layout.addWidget(self.company_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_company_id(self):
        return self.company_combo.currentData()

class AppModeSelectionDialog(QDialog):
    """Dialog zur Auswahl des Anwendungsmodus: Einzel- oder Mehrfachunternehmen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mode = 'single'
        self.setWindowTitle(tr("Anwendungsmodus auswählen"))
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(tr("Anwendungsmodus auswählen"))
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(tr("Wählen Sie aus, wie Sie Ride Guardian Desktop verwenden möchten:"))
        desc.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(desc)
        
        # Single company mode
        single_frame = QFrame()
        single_frame.setStyleSheet("border: 2px solid #007bff; border-radius: 5px; padding: 15px; margin: 5px;")
        single_layout = QVBoxLayout(single_frame)
        
        self.single_radio = QCheckBox(tr("Einzelunternehmen-Modus"))
        self.single_radio.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.single_radio.setChecked(True)
        single_layout.addWidget(self.single_radio)
        
        single_desc = QLabel(tr("Verwalten Sie die Flotte eines Unternehmens. Einfachere Benutzeroberfläche, kein Unternehmenswechsel."))
        single_desc.setWordWrap(True)
        single_layout.addWidget(single_desc)
        
        layout.addWidget(single_frame)
        
        # Multi company mode
        multi_frame = QFrame()
        multi_frame.setStyleSheet("border: 2px solid #28a745; border-radius: 5px; padding: 15px; margin: 5px;")
        multi_layout = QVBoxLayout(multi_frame)
        
        self.multi_radio = QCheckBox(tr("Mehrfachunternehmen-Modus"))
        self.multi_radio.setStyleSheet("font-size: 14px; font-weight: bold;")
        multi_layout.addWidget(self.multi_radio)
        
        multi_desc = QLabel(tr("Verwalten Sie mehrere Unternehmen. Beinhaltet Unternehmensauswahl und separate Daten pro Unternehmen."))
        multi_desc.setWordWrap(True)
        multi_layout.addWidget(multi_desc)
        
        layout.addWidget(multi_frame)
        
        # Connect radio buttons
        self.single_radio.clicked.connect(lambda: self.select_mode('single'))
        self.multi_radio.clicked.connect(lambda: self.select_mode('multi'))
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def select_mode(self, mode):
        self.selected_mode = mode
        self.single_radio.setChecked(mode == 'single')
        self.multi_radio.setChecked(mode == 'multi')
    
    def get_selected_mode(self):
        return self.selected_mode

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_company_id = 1
        self.app_mode = 'single'
        
        self.setWindowTitle(tr("Ride Guardian Desktop - Professionelle Flottenmanagement"))
        self.setGeometry(100, 100, 1100, 700) # Keep this size for now

        # Add Menu Bar for global actions like settings
        self.setup_menu_bar()

        try:
            print(f"Initialisiere erweiterte Datenbank bei: {DATABASE_PATH}")
            initialize_database()
            print("Datenbankinitialisierung erfolgreich abgeschlossen")
        except Exception as e:
            QMessageBox.critical(self, tr("Datenbankfehler"), 
                               tr(f"Fehler beim Initialisieren der Datenbank: {e}\n\n"
                               f"Die Anwendung funktioniert möglicherweise nicht korrekt.\n"
                               f"Bitte überprüfen Sie Ihre Berechtigungen und den Speicherplatz."))

        self.load_app_configuration()
        
        # Create the main container widget and its QVBoxLayout
        main_widget_container = QWidget()
        self.setCentralWidget(main_widget_container)
        overall_layout = QVBoxLayout(main_widget_container)
        overall_layout.setContentsMargins(0, 0, 0, 0)
        overall_layout.setSpacing(0)

        # Company info bar (will be added to overall_layout if in multi-company mode)
        self.info_bar = None # Placeholder for the info_bar
        if self.app_mode == 'multi':
            self.setup_company_info_bar(overall_layout) # Pass the QVBoxLayout

        # Create a widget for the main content (nav + stacked_widget)
        content_widget = QWidget()
        main_content_layout = QHBoxLayout(content_widget) # This will hold nav and stacked_widget
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)

        # Navigation Sidebar
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border-right: 1px solid #d0d0d0;
                padding-top: 20px;
                outline: 0px; /* Remove focus outline */
            }
            QListWidget::item {
                padding: 15px 20px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e0e8f0; /* Lighter blue selection */
                color: #0056b3; /* Darker blue text */
                font-weight: bold;
                border-left: 4px solid #007bff;
            }
            QListWidget::item:hover:!selected {
                background-color: #e9e9e9;
            }
        """)
        main_content_layout.addWidget(self.nav_list)

        # Content Area
        self.stacked_widget = QStackedWidget()
        main_content_layout.addWidget(self.stacked_widget)

        # Add the content_widget (containing nav and stacked) to the overall_layout
        overall_layout.addWidget(content_widget)

        # Show company selection if in multi-company mode (original placement, seems fine)
        # This happens before views are fully populated if it's the first run.
        if self.app_mode == 'multi' and not self.info_bar: # Fallback if setup_company_info_bar wasn't called earlier (e.g. first setup)
             # This condition might be tricky; dialog might need to be shown after main UI setup if it depends on it.
             # For now, assuming initial dialog is okay here.
             # The critical part is that the *persistent* info_bar is in the correct layout.
             pass # Company selection dialog is handled by load_app_configuration & switch_company

        self.add_navigation_item(tr("Überwachung"), RideMonitoringView(self, self.current_company_id))
        self.add_navigation_item(tr("Fahrt eingeben"), RideEntryView(self, self.current_company_id))
        self.add_navigation_item(tr("Daten importieren"), DataImportView(self, self.current_company_id))
        self.add_navigation_item(tr("Fahrer"), DriversView(self, self.current_company_id))
        self.add_navigation_item(tr("Lohnabrechnung"), PayrollView(self, self.current_company_id))
        self.add_navigation_item(tr("Regeln"), RulesView(self, self.current_company_id))
        self.add_navigation_item(tr("Berichte"), ReportsView(self, self.current_company_id))

        # Connect navigation list selection change to switch views
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)

        # Select the first item by default
        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)

    def load_app_configuration(self):
        """Anwendungskonfiguration einschließlich Unternehmensmodus laden"""
        try:
            current_mode = get_company_config(1, 'app_mode')
            
            if current_mode is None:
                # Erstmalige Einrichtung - Benutzer nach Modus fragen
                dialog = AppModeSelectionDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.app_mode = dialog.get_selected_mode()
                    set_company_config(1, 'app_mode', self.app_mode)
                else:
                    self.app_mode = 'single'  # Standard
                    set_company_config(1, 'app_mode', self.app_mode)
            else:
                self.app_mode = current_mode
            
            # Standardunternehmen abrufen wenn Einzelmodus
            if self.app_mode == 'single':
                companies = get_companies()
                if companies:
                    self.current_company_id = companies[0]['id']
                    
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            self.app_mode = 'single'
            self.current_company_id = 1

    def show_company_selection(self):
        """Unternehmensauswahldialog für Mehrfachunternehmen-Modus anzeigen"""
        companies = get_companies()
        if not companies: # Handle case with no companies
            QMessageBox.warning(self, tr("Keine Unternehmen"), tr("Es sind keine Unternehmen in der Datenbank vorhanden. Bitte fügen Sie zuerst ein Unternehmen hinzu."))
            # Optionally, guide user to create a company or switch app to single mode.
            return

        selected_company_id_before_dialog = self.current_company_id

        if len(companies) > 1 or self.app_mode == 'multi': # Ensure dialog shows in multi mode even if only 1 company
            dialog = CompanySelectionDialog(companies, self)
            # Pre-select current company in dialog
            for i in range(dialog.company_combo.count()):
                if dialog.company_combo.itemData(i) == self.current_company_id:
                    dialog.company_combo.setCurrentIndex(i)
                    break
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.current_company_id = dialog.get_selected_company_id()
            else:
                # If dialog is cancelled, keep the current_company_id
                # If it's the very first launch and cancel, default to first company or handle error
                if not selected_company_id_before_dialog and companies:
                     self.current_company_id = companies[0]['id']
                else:
                    self.current_company_id = selected_company_id_before_dialog # Revert to original if cancelled

        elif companies: # Single company exists, or multi-mode with only one company and dialog was skipped
            self.current_company_id = companies[0]['id']
        else: # Should not happen if check at start is done
            self.current_company_id = 1 # Fallback default

        if selected_company_id_before_dialog != self.current_company_id:
            self.refresh_all_views()
            self.update_company_info_bar_text()

    def setup_company_info_bar(self, target_layout: QVBoxLayout): # Target layout is the overall QVBoxLayout
        """Unternehmensinformationsleiste für Mehrfachunternehmen-Modus einrichten"""
        self.info_bar = QFrame() # Store as instance variable
        self.info_bar.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border-bottom: 1px solid #ccc;
                padding: 5px;
                max-height: 40px; /* Max height for the info bar */
            }
            QPushButton {
                padding: 5px 10px;
                font-size: 12px; /* Smaller font for buttons */
            }
            QLabel {
                font-size: 12px; /* Smaller font for label */
            }
        """)
        info_layout = QHBoxLayout(self.info_bar)
        info_layout.setContentsMargins(5,0,5,0) # Reduce internal margins
        info_layout.setSpacing(10)
        
        companies = get_companies()
        current_company = next((c for c in companies if c['id'] == self.current_company_id), None)
        
        self.company_label = QLabel(tr(f"Aktuelles Unternehmen: {current_company['name'] if current_company else 'Unbekannt'}"))
        self.company_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.company_label)
        
        info_layout.addStretch()
        
        switch_btn = QPushButton(tr("Unternehmen wechseln"))
        switch_btn.clicked.connect(self.switch_company)
        info_layout.addWidget(switch_btn)
        
        settings_btn = QPushButton(tr("Einstellungen"))
        settings_btn.clicked.connect(self.show_settings)
        info_layout.addWidget(settings_btn)
        
        # Add info_bar to the passed QVBoxLayout (overall_layout)
        target_layout.insertWidget(0, self.info_bar) # Insert at the top

    def update_company_info_bar_text(self):
        """Updates the text of the company label in the info bar."""
        if self.app_mode == 'multi' and hasattr(self, 'company_label') and self.company_label:
            companies = get_companies()
            current_company = next((c for c in companies if c['id'] == self.current_company_id), None)
            self.company_label.setText(tr(f"Aktuelles Unternehmen: {current_company['name'] if current_company else 'Unbekannt'}"))

    def switch_company(self):
        """Zu einem anderen Unternehmen wechseln"""
        self.show_company_selection()
        # refresh_all_views and update_company_info_bar_text are now called within show_company_selection
        # if the company actually changes.

    def show_settings(self):
        """Anwendungseinstellungen-Dialog anzeigen"""
        dialog = AppModeSelectionDialog(self)
        dialog.setWindowTitle(tr("Anwendungseinstellungen"))
        
        # Aktuellen Modus setzen
        current_mode = get_company_config(1, 'app_mode') or 'single'
        if current_mode == 'single':
            dialog.single_radio.setChecked(True)
        else:
            dialog.multi_radio.setChecked(True)
        dialog.selected_mode = current_mode
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_mode = dialog.get_selected_mode()
            if new_mode != self.app_mode:
                # Modus geändert - Neustart erforderlich
                set_company_config(1, 'app_mode', new_mode)
                QMessageBox.information(self, tr("Einstellungen geändert"), 
                                      tr("Anwendungsmodus geändert. Bitte starten Sie die Anwendung neu, damit die Änderungen wirksam werden."))

    def refresh_all_views(self):
        """Alle Ansichten mit der aktuellen Unternehmens-ID aktualisieren"""
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, 'company_id'):
                widget.company_id = self.current_company_id
            if hasattr(widget, 'refresh_data'):
                widget.refresh_data()

    def add_navigation_item(self, name, widget):
        item = QListWidgetItem(name)
        item.setSizeHint(QSize(0, 50)) # Height of the item
        self.nav_list.addItem(item)
        self.stacked_widget.addWidget(widget)

    def closeEvent(self, event):
        # Ensure child widgets (views) handle their resource cleanup if needed
        # For example, closing database connections held by views
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, "closeEvent"): # Check if the view has a custom close handler
                 widget.closeEvent(event) # Call it explicitly if needed
            elif hasattr(widget, "db_conn") and widget.db_conn: # Basic check for db_conn
                try:
                    widget.db_conn.close()
                    print(f"DB-Verbindung geschlossen für {widget.__class__.__name__}")
                except Exception as e:
                    print(f"Fehler beim Schließen der DB-Verbindung für {widget.__class__.__name__}: {e}")
        super().closeEvent(event)

    def setup_menu_bar(self):
        """Sets up the main menu bar for the application."""
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False) # Ensures menu bar is visible on all OS, especially macOS

        # File Menu (or Application Menu)
        # Using "Datei" (File) as a common menu name
        file_menu = menu_bar.addMenu(tr("&Datei")) 

        # Application Settings Action
        settings_action = QAction(tr("Anwendungseinstellungen..."), self)
        settings_action.triggered.connect(self.show_settings) # Reuses your existing show_settings method
        file_menu.addAction(settings_action)

        # Add other actions like Exit if needed
        file_menu.addSeparator()
        exit_action = QAction(tr("Beenden"), self)
        exit_action.triggered.connect(self.close) # Connect to QMainWindow.close
        file_menu.addAction(exit_action)

def setup_translations(app):
    """Deutsche Übersetzungen für die Anwendung einrichten"""
    try:
        # Übersetzungen mit dem erweiterten Übersetzungsmanager laden
        translation_manager.load_qt_translations(app)
        print("Übersetzungsmanager erfolgreich initialisiert")
        
        # Anwendungssprache auf Deutsch setzen
        QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
        
        return True
        
    except Exception as e:
        print(f"Fehler beim Einrichten der Übersetzungen: {e}")
        return False

def main():
    # Umgebungsvariable für Qt-Skalierung bei Bedarf setzen
    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    # Deutsche Übersetzungen einrichten
    setup_translations(app)
    
    # Stil anwenden (optional)
    # app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    # print("RUNNING LATEST VERSION - ATTEMPTING 1100x700") # Removed verification print
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root) # Projektstamm zum Pfad hinzufügen
    os.chdir(project_root) # Arbeitsverzeichnis ändern
    print(f"Aktuelles Arbeitsverzeichnis: {os.getcwd()}")
    print(f"Python-Pfad: {sys.path}")
    main()

