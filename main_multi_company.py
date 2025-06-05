"""
Ride Guardian Desktop - Multi-Company Version
Advanced interface for managing multiple companies' fleet operations
"""

import sys
import os

# Ensure project root in PYTHONPATH before imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QListWidget, QStackedWidget, QListWidgetItem, QMessageBox, 
                            QComboBox, QLabel, QFrame, QDialog, QDialogButtonBox, QLineEdit,
                            QFormLayout, QPushButton, QGroupBox, QGridLayout, QTextEdit)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, QTranslator, QLocale, QCoreApplication

# Core components
from core.database import initialize_database, DATABASE_PATH
from core.company_manager import company_manager
from core.translation_manager import TranslationManager

# Import Views
from ui.views.ride_monitoring_view import RideMonitoringView
from ui.views.ride_entry_view import RideEntryView
from ui.views.data_import_view import DataImportView
from ui.views.drivers_view import DriversView
from ui.views.payroll_view import PayrollView
from ui.views.rules_view import RulesView
from ui.views.reports_view import ReportsView
from ui.views.dashboard_view import DashboardView

class CompanySelectionDialog(QDialog):
    """Dialog for selecting a company in multi-company mode"""
    
    def __init__(self, companies, parent=None):
        super().__init__(parent)
        self.companies = companies
        self.selected_company_id = companies[0]['id'] if companies else 1
        self.tm = TranslationManager()
        
        self.setWindowTitle(self.tm.tr("select_company"))
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(self.tm.tr("select_company_to_manage"))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Company selection
        self.company_combo = QComboBox()
        self.company_combo.setMinimumHeight(40)
        self.company_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        for company in self.companies:
            # Convert sqlite3.Row to dict if needed
            if hasattr(company, 'keys'):
                company_dict = dict(company)
            else:
                company_dict = company
            
            display_text = f"{company_dict['name']}"
            if company_dict.get('headquarters_address'):
                display_text += f" - {company_dict['headquarters_address']}"
            self.company_combo.addItem(display_text, company_dict['id'])
        
        layout.addWidget(QLabel(self.tm.tr("company") + ":"))
        layout.addWidget(self.company_combo)
        
        # Company details
        details_group = QGroupBox(self.tm.tr("company_details"))
        details_layout = QGridLayout(details_group)
        
        self.name_label = QLabel()
        self.address_label = QLabel()
        self.phone_label = QLabel()
        self.email_label = QLabel()
        
        details_layout.addWidget(QLabel(self.tm.tr("name") + ":"), 0, 0)
        details_layout.addWidget(self.name_label, 0, 1)
        details_layout.addWidget(QLabel(self.tm.tr("address") + ":"), 1, 0)
        details_layout.addWidget(self.address_label, 1, 1)
        details_layout.addWidget(QLabel(self.tm.tr("phone") + ":"), 2, 0)
        details_layout.addWidget(self.phone_label, 2, 1)
        details_layout.addWidget(QLabel(self.tm.tr("email") + ":"), 3, 0)
        details_layout.addWidget(self.email_label, 3, 1)
        
        layout.addWidget(details_group)
        
        # Update details when selection changes
        self.company_combo.currentIndexChanged.connect(self.update_company_details)
        self.update_company_details()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        manage_btn = QPushButton(self.tm.tr("manage_companies"))
        manage_btn.clicked.connect(self.manage_companies)
        button_layout.addWidget(manage_btn)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tm.tr("select"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tm.tr("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def update_company_details(self):
        """Update company details display"""
        current_index = self.company_combo.currentIndex()
        if current_index >= 0 and current_index < len(self.companies):
            company = self.companies[current_index]
            # Convert sqlite3.Row to dict if needed
            if hasattr(company, 'keys'):
                company_dict = dict(company)
            else:
                company_dict = company
                
            self.name_label.setText(company_dict.get('name', ''))
            self.address_label.setText(company_dict.get('headquarters_address', ''))
            self.phone_label.setText(company_dict.get('phone', ''))
            self.email_label.setText(company_dict.get('email', ''))
    
    def manage_companies(self):
        """Open company management dialog"""
        dialog = CompanyManagementDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh companies list
            self.companies = company_manager.get_companies()
            current_id = self.get_selected_company_id()
            
            self.company_combo.clear()
            for company in self.companies:
                # Convert sqlite3.Row to dict if needed
                if hasattr(company, 'keys'):
                    company_dict = dict(company)
                else:
                    company_dict = company
                    
                display_text = f"{company_dict['name']}"
                if company_dict.get('headquarters_address'):
                    display_text += f" - {company_dict['headquarters_address']}"
                self.company_combo.addItem(display_text, company_dict['id'])
            
            # Try to restore selection
            for i in range(self.company_combo.count()):
                if self.company_combo.itemData(i) == current_id:
                    self.company_combo.setCurrentIndex(i)
                    break

    def get_selected_company_id(self):
        """Get the selected company ID"""
        return self.company_combo.currentData()

class CompanyManagementDialog(QDialog):
    """Dialog for managing companies (add, edit, delete)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tm = TranslationManager()
        
        self.setWindowTitle(self.tm.tr("manage_companies"))
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_companies()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(self.tm.tr("company_management"))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Company list
        self.company_list = QListWidget()
        self.company_list.setMinimumHeight(200)
        layout.addWidget(self.company_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton(self.tm.tr("add_company"))
        add_btn.clicked.connect(self.add_company)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton(self.tm.tr("edit_company"))
        edit_btn.clicked.connect(self.edit_company)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton(self.tm.tr("delete_company"))
        delete_btn.clicked.connect(self.delete_company)
        delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton(self.tm.tr("close"))
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_companies(self):
        """Load companies into the list"""
        self.company_list.clear()
        companies = company_manager.get_companies()
        
        for company in companies:
            # Convert sqlite3.Row to dict if needed
            if hasattr(company, 'keys'):
                company_dict = dict(company)
            else:
                company_dict = company
                
            item_text = f"{company_dict['name']}"
            if company_dict.get('headquarters_address'):
                item_text += f"\n{company_dict['headquarters_address']}"
            
            item = QListWidgetItem(item_text)
            item.setData(256, company_dict['id'])  # Store company ID
            self.company_list.addItem(item)
    
    def add_company(self):
        """Add a new company"""
        dialog = CompanyEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            company_data = dialog.get_company_data()
            if company_manager.add_company(**company_data):
                QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("company_added_successfully"))
                self.load_companies()
            else:
                QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("failed_to_add_company"))
    
    def edit_company(self):
        """Edit selected company"""
        current_item = self.company_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tm.tr("warning"), self.tm.tr("please_select_company"))
            return
        
        company_id = current_item.data(256)
        companies = company_manager.get_companies()
        company = next((c for c in companies if c['id'] == company_id), None)
        
        if company:
            # Convert sqlite3.Row to dict if needed
            if hasattr(company, 'keys'):
                company_dict = dict(company)
            else:
                company_dict = company
                
            dialog = CompanyEditDialog(self, company_dict)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                company_data = dialog.get_company_data()
                if company_manager.update_company(company_id, **company_data):
                    QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("company_updated_successfully"))
                    self.load_companies()
                else:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("failed_to_update_company"))
    
    def delete_company(self):
        """Delete selected company"""
        current_item = self.company_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tm.tr("warning"), self.tm.tr("please_select_company"))
            return
        
        company_id = current_item.data(256)
        if company_id == 1:
            QMessageBox.warning(self, self.tm.tr("warning"), self.tm.tr("cannot_delete_default_company"))
            return
        
        companies = company_manager.get_companies()
        company = next((c for c in companies if c['id'] == company_id), None)
        
        if company:
            # Convert sqlite3.Row to dict if needed
            if hasattr(company, 'keys'):
                company_dict = dict(company)
            else:
                company_dict = company
                
            reply = QMessageBox.question(
                self, self.tm.tr("confirm_delete"),
                f"{self.tm.tr('confirm_delete_company')} '{company_dict['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if company_manager.delete_company(company_id):
                    QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("company_deleted_successfully"))
                    self.load_companies()
                else:
                    QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("failed_to_delete_company"))

class CompanyEditDialog(QDialog):
    """Dialog for editing company information"""
    
    def __init__(self, parent=None, company_data=None):
        super().__init__(parent)
        self.company_data = company_data
        self.tm = TranslationManager()
        
        title = self.tm.tr("edit_company") if company_data else self.tm.tr("add_company")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 300)
        self.init_ui()
        
        if company_data:
            self.populate_fields()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.tm.tr("company_name"))
        form_layout.addRow(self.tm.tr("name") + ":", self.name_edit)
        
        self.address_edit = QTextEdit()
        self.address_edit.setPlaceholderText(self.tm.tr("company_address"))
        self.address_edit.setMaximumHeight(80)
        form_layout.addRow(self.tm.tr("address") + ":", self.address_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText(self.tm.tr("phone_number"))
        form_layout.addRow(self.tm.tr("phone") + ":", self.phone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText(self.tm.tr("email_address"))
        form_layout.addRow(self.tm.tr("email") + ":", self.email_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tm.tr("save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tm.tr("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_fields(self):
        """Populate form fields with existing company data"""
        if self.company_data:
            self.name_edit.setText(self.company_data.get('name', ''))
            self.address_edit.setPlainText(self.company_data.get('headquarters_address', ''))
            self.phone_edit.setText(self.company_data.get('phone', ''))
            self.email_edit.setText(self.company_data.get('email', ''))
    
    def get_company_data(self):
        """Get company data from form"""
        return {
            'name': self.name_edit.text().strip(),
            'address': self.address_edit.toPlainText().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip()
        }

class MultiCompanyMainWindow(QMainWindow):
    """Main window for multi-company version"""
    
    def __init__(self):
        super().__init__()
        
        self.tm = TranslationManager()
        
        # Initialize multi-company mode
        company_manager.save_app_mode(company_manager.MULTI_COMPANY_MODE)
        company_manager.initialize_app_mode()
        
        # Show company selection dialog
        self.show_company_selection()
        
        # Set window title
        current_company = company_manager.get_current_company()
        if current_company:
            self.setWindowTitle(f"Ride Guardian Desktop - {current_company['name']} (Multi-Company)")
        else:
            self.setWindowTitle("Ride Guardian Desktop - Multi-Company Mode")
        
        # Set window properties
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize Database
        try:
            print(f"Initialisiere Datenbank bei: {DATABASE_PATH}")
            initialize_database()
            print("Datenbankinitialisierung erfolgreich abgeschlossen")
        except Exception as e:
            QMessageBox.critical(self, self.tm.tr("database_error"), 
                               f"{self.tm.tr('database_init_error')}: {e}\n\n"
                               f"{self.tm.tr('app_may_not_work_correctly')}")
        
        self.init_ui()
    
    def show_company_selection(self):
        """Show company selection dialog"""
        companies = company_manager.get_companies()
        if not companies:
            # No companies exist, create default
            company_manager.ensure_default_company()
            companies = company_manager.get_companies()
        
        if len(companies) == 1:
            # Only one company, select it automatically
            company_manager.set_current_company(companies[0]['id'])
        else:
            # Multiple companies, show selection dialog
            dialog = CompanySelectionDialog(companies, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                company_manager.set_current_company(dialog.get_selected_company_id())
            else:
                # User cancelled, select first company
                company_manager.set_current_company(companies[0]['id'])
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Company info bar
        self.setup_company_info_bar()
        
        # Create main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Navigation Sidebar
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(220)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding-top: 10px;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 15px 20px;
                border-bottom: 1px solid #34495e;
                margin: 0px 5px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #34495e;
            }
        """)
        content_layout.addWidget(self.nav_list)
        
        # Content Area
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #f8f9fa;
            }
        """)
        content_layout.addWidget(self.stacked_widget)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        
        # Add navigation items and corresponding views
        self.add_navigation_items()
        
        # Connect navigation
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # Select the first item by default
        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)
    
    def setup_company_info_bar(self):
        """Setup company information bar for multi-company mode"""
        info_bar = QFrame()
        info_bar.setFixedHeight(50)
        info_bar.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border-bottom: 2px solid #2c3e50;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(20, 10, 20, 10)
        
        # Current company info
        current_company = company_manager.get_current_company()
        company_text = f"{self.tm.tr('current_company')}: {current_company['name']}" if current_company else self.tm.tr("no_company_selected")
        self.company_label = QLabel(company_text)
        self.company_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.company_label)
        
        info_layout.addStretch()
        
        # Company statistics
        if current_company:
            stats = company_manager.get_company_statistics(company_manager.current_company_id)
            stats_text = f"{self.tm.tr('drivers')}: {stats['driver_count']} | {self.tm.tr('rides')}: {stats['ride_count']} | {self.tm.tr('monthly_revenue')}: €{stats['monthly_revenue']:.2f}"
            stats_label = QLabel(stats_text)
            stats_label.setFont(QFont("Arial", 10))
            info_layout.addWidget(stats_label)
        
        info_layout.addStretch()
        
        # Action buttons
        switch_btn = QPushButton(self.tm.tr("switch_company"))
        switch_btn.clicked.connect(self.switch_company)
        switch_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        info_layout.addWidget(switch_btn)
        
        manage_btn = QPushButton(self.tm.tr("manage_companies"))
        manage_btn.clicked.connect(self.manage_companies)
        manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        info_layout.addWidget(manage_btn)
        
        # Add to main layout
        main_widget = self.centralWidget()
        if main_widget.layout() is None:
            layout = QVBoxLayout(main_widget)
        else:
            layout = main_widget.layout()
        layout.insertWidget(0, info_bar)
    
    def switch_company(self):
        """Switch to a different company"""
        self.show_company_selection()
        self.refresh_all_views()
        self.update_company_info_bar()
        
        # Update window title
        current_company = company_manager.get_current_company()
        if current_company:
            self.setWindowTitle(f"Ride Guardian Desktop - {current_company['name']} (Multi-Company)")
    
    def manage_companies(self):
        """Open company management dialog"""
        dialog = CompanyManagementDialog(self)
        dialog.exec()
        
        # Refresh company info after management
        self.update_company_info_bar()
    
    def update_company_info_bar(self):
        """Update the company information bar"""
        current_company = company_manager.get_current_company()
        if current_company:
            company_text = f"{self.tm.tr('current_company')}: {current_company['name']}"
            self.company_label.setText(company_text)
    
    def add_navigation_items(self):
        """Add navigation items and their corresponding views"""
        company_id = company_manager.current_company_id
        
        # Navigation items with their views
        nav_items = [
            (self.tm.tr("dashboard"), DashboardView(self)),
            (self.tm.tr("ride_monitoring"), RideMonitoringView(self, company_id)),
            (self.tm.tr("add_ride"), RideEntryView(self, company_id)),
            (self.tm.tr("data_import"), DataImportView(self, company_id)),
            (self.tm.tr("drivers"), DriversView(self, company_id)),
            (self.tm.tr("payroll"), PayrollView(self, company_id)),
            (self.tm.tr("rules"), RulesView(self, company_id)),
            (self.tm.tr("reports"), ReportsView(self, company_id))
        ]
        
        for name, widget in nav_items:
            self.add_navigation_item(name, widget)
    
    def add_navigation_item(self, name, widget):
        """Add a navigation item and its corresponding widget"""
        item = QListWidgetItem(name)
        item.setSizeHint(QSize(0, 50))
        self.nav_list.addItem(item)
        self.stacked_widget.addWidget(widget)
    
    def refresh_all_views(self):
        """Refresh all views with the current company ID"""
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, 'company_id'):
                widget.company_id = company_manager.current_company_id
            if hasattr(widget, 'refresh_data'):
                widget.refresh_data()
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Cleanup resources
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, "closeEvent"):
                widget.closeEvent(event)
            elif hasattr(widget, "db") and widget.db:
                try:
                    widget.db.close()
                    print(f"DB-Verbindung geschlossen für {widget.__class__.__name__}")
                except Exception as e:
                    print(f"Fehler beim Schließen der DB-Verbindung für {widget.__class__.__name__}: {e}")
        
        super().closeEvent(event)

def setup_translations(app):
    """Setup German translations for the application"""
    try:
        tm = TranslationManager()
        # Load translations
        QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
        print("Übersetzungen erfolgreich geladen")
        return True
    except Exception as e:
        print(f"Fehler beim Laden der Übersetzungen: {e}")
        return False

def main():
    """Main entry point for multi-company version"""
    app = QApplication(sys.argv)
    
    # Setup translations
    setup_translations(app)
    
    # Apply application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MultiCompanyMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    # Ensure proper working directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.chdir(project_root)
    
    print(f"Ride Guardian Desktop - Multi-Company Version")
    print(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    main()