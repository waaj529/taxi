"""
Ride Guardian Desktop - Single Company Version
Simplified interface for managing one company's fleet operations
"""

import sys
import os

# Ensure project root in PYTHONPATH before imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QStackedWidget, QMessageBox, 
                            QLabel, QFrame, QPushButton, QButtonGroup, QSizePolicy,
                            QSplashScreen, QProgressBar)
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtCore import QSize, QTranslator, QLocale, QCoreApplication, QTimer, Qt

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

class SingleCompanyMainWindow(QMainWindow):
    """Main window for single company version"""
    
    def __init__(self):
        super().__init__()
        
        self.tm = TranslationManager()
        self.nav_button_group = QButtonGroup()
        
        # Ensure any existing dialogs are closed
        QApplication.instance().closeAllWindows()
        
        # Initialize single company mode
        company_manager.save_app_mode(company_manager.SINGLE_COMPANY_MODE)
        company_manager.initialize_app_mode()
        company_manager.ensure_default_company()
        
        # Set current company to the default/only company
        companies = company_manager.get_companies()
        if companies:
            company_manager.set_current_company(companies[0]['id'])
            current_company = companies[0]
            self.setWindowTitle(f"Ride Guardian Desktop - {current_company['name']}")
        else:
            self.setWindowTitle("Ride Guardian Desktop - Flottenmanagement")
        
        # Set window properties
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize Database with proper error handling
        try:
            print(f"Initialisiere Datenbank bei: {DATABASE_PATH}")
            initialize_database()
            print("Datenbankinitialisierung erfolgreich abgeschlossen")
        except Exception as e:
            # Ensure any dialogs are properly handled
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle(self.tm.tr("database_error"))
            error_msg.setText(f"{self.tm.tr('database_init_error')}: {e}")
            error_msg.setDetailedText(f"{self.tm.tr('app_may_not_work_correctly')}")
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()
            error_msg.deleteLater()
        
        # Use QTimer to ensure UI is fully initialized before showing
        QTimer.singleShot(100, self.init_ui)
    
    def showEvent(self, event):
        """Override showEvent to ensure proper window activation"""
        super().showEvent(event)
        # Ensure this window is active and on top
        self.raise_()
        self.activateWindow()
        
        # Close any lingering dialogs after a short delay
        QTimer.singleShot(500, self.cleanup_dialogs)
    
    def cleanup_dialogs(self):
        """Clean up any stuck dialogs"""
        app = QApplication.instance()
        if app:
            # Find and close any orphaned dialogs
            for widget in app.allWidgets():
                if (hasattr(widget, 'isModal') and widget.isModal() and 
                    widget != self and widget.isVisible()):
                    print(f"Closing stuck dialog: {widget.__class__.__name__}")
                    widget.close()
                    widget.deleteLater()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Enhanced header with navigation
        self.setup_enhanced_header()
        
        # Content Area (full width)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #f8f9fa;
                border: none;
            }
        """)
        main_layout.addWidget(self.stacked_widget)
        
        # Add navigation items and corresponding views
        self.add_navigation_items()
        
        # Select the first item by default (Dashboard)
        if self.stacked_widget.count() > 0:
            self.switch_view(0)
    
    def setup_enhanced_header(self):
        """Setup enhanced header with company info and navigation"""
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-bottom: 3px solid #3498db;
            }
        """)
        
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # Top company info bar
        company_bar = QFrame()
        company_bar.setFixedHeight(50)
        company_bar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: none;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        company_layout = QHBoxLayout(company_bar)
        company_layout.setContentsMargins(20, 8, 20, 8)
        
        # Company name and title
        current_company = company_manager.get_current_company()
        if current_company:
            company_name = QLabel(current_company['name'])
            company_name.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        else:
            company_name = QLabel("Ride Guardian Desktop")
            company_name.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        company_layout.addWidget(company_name)
        
        # Subtitle
        subtitle = QLabel(self.tm.tr("fleet_management_system"))
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #bdc3c7; margin-left: 15px;")
        company_layout.addWidget(subtitle)
        
        company_layout.addStretch()
        
        # Quick stats
        stats = company_manager.get_company_statistics(company_manager.current_company_id)
        stats_text = f"{self.tm.tr('drivers')}: {stats['driver_count']} | {self.tm.tr('monthly_revenue')}: €{stats['monthly_revenue']:.2f}"
        stats_label = QLabel(stats_text)
        stats_label.setFont(QFont("Arial", 10))
        stats_label.setStyleSheet("color: #95a5a6;")
        company_layout.addWidget(stats_label)
        
        header_layout.addWidget(company_bar)
        
        # Navigation bar
        nav_bar = QFrame()
        nav_bar.setFixedHeight(60)
        nav_bar.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border: none;
            }
        """)
        
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(20, 10, 20, 10)
        nav_layout.setSpacing(5)
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("dashboard", "📊 " + self.tm.tr("dashboard")),
            ("ride_monitoring", "🚗 " + self.tm.tr("ride_monitoring")),
            ("add_ride", "➕ " + self.tm.tr("add_ride")),
            ("data_import", "📥 " + self.tm.tr("data_import")),
            ("drivers", "👥 " + self.tm.tr("drivers")),
            ("payroll", "💰 " + self.tm.tr("payroll")),
            ("rules", "📋 " + self.tm.tr("rules")),
            ("reports", "📊 " + self.tm.tr("reports"))
        ]
        
        for i, (key, text) in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumWidth(120)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #bdc3c7;
                    border: 2px solid transparent;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #3c5266;
                    color: white;
                    border-color: #3498db;
                }
                QPushButton:checked {
                    background-color: #3498db;
                    color: white;
                    border-color: #2980b9;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(lambda checked, index=i: self.switch_view(index))
            self.nav_button_group.addButton(btn, i)
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        header_layout.addWidget(nav_bar)
        
        # Add header to main layout
        main_widget = self.centralWidget()
        main_widget.layout().insertWidget(0, header_container)
    
    def switch_view(self, index):
        """Switch to the specified view"""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            # Update button states
            for i, btn in enumerate(self.nav_buttons):
                btn.setChecked(i == index)
    
    def add_navigation_items(self):
        """Add navigation items and their corresponding views"""
        company_id = company_manager.current_company_id
        
        # Navigation items with their views
        nav_views = [
            DashboardView(self),
            RideMonitoringView(self, company_id),
            RideEntryView(self, company_id),
            DataImportView(self, company_id),
            DriversView(self, company_id),
            PayrollView(self, company_id),
            RulesView(self, company_id),
            ReportsView(self, company_id)
        ]
        
        for widget in nav_views:
            self.stacked_widget.addWidget(widget)
    
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
    """Main entry point for single company version"""
    app = QApplication(sys.argv)
    
    # Ensure clean application state
    app.setQuitOnLastWindowClosed(True)
    
    # Setup translations
    setup_translations(app)
    
    # Apply application style
    app.setStyle("Fusion")
    
    # Close any existing windows/dialogs before creating main window
    app.closeAllWindows()
    
    # Create and show main window
    window = SingleCompanyMainWindow()
    
    # Ensure proper window management
    window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    window.show()
    
    # Force window to front and activate
    window.raise_()
    window.activateWindow()
    
    # Clean up any remaining dialogs after app starts
    def cleanup_startup_dialogs():
        for widget in app.allWidgets():
            if (hasattr(widget, 'isModal') and widget.isModal() and 
                widget != window and widget.isVisible()):
                print(f"Cleaning up startup dialog: {widget.__class__.__name__}")
                widget.close()
                widget.deleteLater()
    
    # Schedule cleanup after application has fully started
    QTimer.singleShot(1000, cleanup_startup_dialogs)
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    # Ensure proper working directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.chdir(project_root)
    
    print(f"Ride Guardian Desktop - Single Company Version")
    print(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    main()