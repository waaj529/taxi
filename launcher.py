"""
Ride Guardian Desktop - Application Launcher
Allows users to choose between Single Company and Multi-Company versions
"""

import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QFrame, QTextEdit, QGroupBox, QGridLayout,
    QMessageBox, QCheckBox, QSplashScreen, QScrollArea, QSizePolicy, QWidget
)
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QIcon, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize

# Ensure project root in PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.translation_manager import TranslationManager
from core.company_manager import company_manager

class AppLaunchThread(QThread):
    """Thread for launching the selected application version"""
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, app_type, remember_choice=False):
        super().__init__()
        self.app_type = app_type
        self.remember_choice = remember_choice
    
    def run(self):
        try:
            if self.remember_choice:
                # Save the choice for future launches
                self.save_launch_preference(self.app_type)
            
            # Determine which script to run
            if self.app_type == "single":
                script_name = "main_single_company.py"
            else:
                script_name = "main_multi_company.py"
            
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            
            # Launch the application
            if os.path.exists(script_path):
                # Use subprocess to launch the application
                subprocess.Popen([sys.executable, script_path], 
                               cwd=os.path.dirname(__file__))
                self.finished_signal.emit(True, f"Successfully launched {script_name}")
            else:
                self.finished_signal.emit(False, f"Script not found: {script_name}")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Failed to launch application: {str(e)}")
    
    def save_launch_preference(self, app_type):
        """Save the launch preference to a configuration file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '.launcher_config')
            with open(config_path, 'w') as f:
                f.write(f"default_mode={app_type}\n")
        except Exception as e:
            print(f"Could not save launch preference: {e}")

class ResponsiveScrollArea(QScrollArea):
    """Custom scroll area that adapts to content and screen size"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameStyle(QFrame.Shape.NoFrame)

class ApplicationLauncher(QDialog):
    """Main launcher dialog for choosing application version"""
    
    def __init__(self):
        super().__init__()
        self.tm = TranslationManager()
        self.selected_mode = "single"  # Default selection
        
        self.setWindowTitle("Ride Guardian Desktop - Launcher")
        self.setModal(True)
        
        # Make window resizable and set responsive size policies
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Get screen geometry for responsive sizing
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Calculate responsive dimensions (percentage of screen size)
        min_width = max(500, int(screen_geometry.width() * 0.25))
        min_height = max(400, int(screen_geometry.height() * 0.4))
        max_width = min(800, int(screen_geometry.width() * 0.7))
        max_height = min(700, int(screen_geometry.height() * 0.8))
        
        # Set size constraints
        self.setMinimumSize(QSize(min_width, min_height))
        self.setMaximumSize(QSize(max_width, max_height))
        
        # Start with optimal size
        optimal_width = min(600, int(screen_geometry.width() * 0.4))
        optimal_height = min(550, int(screen_geometry.height() * 0.6))
        self.resize(QSize(optimal_width, optimal_height))
        
        # Center on screen
        self.move(
            screen_geometry.center().x() - self.width() // 2,
            screen_geometry.center().y() - self.height() // 2
        )
        
        self.init_ui()
        self.load_saved_preference()
    
    def init_ui(self):
        """Initialize the responsive user interface"""
        # Main scroll area for content
        scroll_area = ResponsiveScrollArea()
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)  # Reduced spacing for compactness
        layout.setContentsMargins(20, 20, 20, 20)  # Reduced margins
        
        # Header section
        self.create_responsive_header(layout)
        
        # Version selection section
        self.create_responsive_version_selection(layout)
        
        # Description section
        self.create_responsive_description_section(layout)
        
        # Options section
        self.create_responsive_options_section(layout)
        
        # Buttons section
        self.create_responsive_buttons_section(layout)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        
        # Main dialog layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # Set initial descriptions
        self.update_description()
    
    def create_responsive_header(self, layout):
        """Create the responsive header section with title and logo"""
        header_frame = QFrame()
        header_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # Responsive title font size
        title_font_size = self.calculate_responsive_font_size(24, 16, 32)
        subtitle_font_size = self.calculate_responsive_font_size(12, 10, 16)
        
        # Main title
        title = QLabel("🚗 Ride Guardian Desktop")
        title.setFont(QFont("Arial", title_font_size, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin: 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(self.tm.tr("choose_application_version"))
        subtitle.setFont(QFont("Arial", subtitle_font_size))
        subtitle.setStyleSheet("color: #ecf0f1; margin-top: 5px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)
    
    def create_responsive_version_selection(self, layout):
        """Create the responsive version selection radio buttons"""
        selection_group = QGroupBox(self.tm.tr("select_version"))
        selection_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        font_size = self.calculate_responsive_font_size(12, 10, 14)
        selection_group.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        selection_layout = QVBoxLayout(selection_group)
        selection_layout.setSpacing(10)
        
        # Radio button group
        self.version_group = QButtonGroup()
        
        # Single Company option
        self.single_radio = QRadioButton()
        self.single_radio.setText("🏢 " + self.tm.tr("single_company_mode"))
        self.single_radio.setFont(QFont("Arial", font_size - 1, QFont.Weight.Bold))
        self.single_radio.setStyleSheet("""
            QRadioButton {
                padding: 8px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.single_radio.setChecked(True)  # Default selection
        self.single_radio.toggled.connect(self.on_version_changed)
        self.version_group.addButton(self.single_radio, 0)
        selection_layout.addWidget(self.single_radio)
        
        # Multi-Company option
        self.multi_radio = QRadioButton()
        self.multi_radio.setText("🏬 " + self.tm.tr("multi_company_mode"))
        self.multi_radio.setFont(QFont("Arial", font_size - 1, QFont.Weight.Bold))
        self.multi_radio.setStyleSheet("""
            QRadioButton {
                padding: 8px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.multi_radio.toggled.connect(self.on_version_changed)
        self.version_group.addButton(self.multi_radio, 1)
        selection_layout.addWidget(self.multi_radio)
        
        layout.addWidget(selection_group)
    
    def create_responsive_description_section(self, layout):
        """Create the responsive description section"""
        desc_group = QGroupBox(self.tm.tr("description"))
        desc_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        font_size = self.calculate_responsive_font_size(12, 10, 14)
        desc_group.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Responsive height constraints
        min_height = max(80, int(self.height() * 0.15))
        max_height = max(150, int(self.height() * 0.35))
        self.description_text.setMinimumHeight(min_height)
        self.description_text.setMaximumHeight(max_height)
        
        text_font_size = self.calculate_responsive_font_size(11, 9, 13)
        self.description_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
                font-size: {text_font_size}px;
                line-height: 1.4;
            }}
        """)
        desc_layout.addWidget(self.description_text)
        
        layout.addWidget(desc_group)
    
    def create_responsive_options_section(self, layout):
        """Create the responsive options section"""
        options_group = QGroupBox(self.tm.tr("options"))
        options_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        font_size = self.calculate_responsive_font_size(12, 10, 14)
        options_group.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(8)
        
        checkbox_font_size = self.calculate_responsive_font_size(10, 9, 12)
        
        # Remember choice checkbox
        self.remember_checkbox = QCheckBox(self.tm.tr("remember_choice"))
        self.remember_checkbox.setFont(QFont("Arial", checkbox_font_size))
        self.remember_checkbox.setToolTip(self.tm.tr("remember_choice_tooltip"))
        options_layout.addWidget(self.remember_checkbox)
        
        # Show advanced info checkbox
        self.show_info_checkbox = QCheckBox(self.tm.tr("show_detailed_info"))
        self.show_info_checkbox.setFont(QFont("Arial", checkbox_font_size))
        self.show_info_checkbox.toggled.connect(self.update_description)
        options_layout.addWidget(self.show_info_checkbox)
        
        layout.addWidget(options_group)
    
    def create_responsive_buttons_section(self, layout):
        """Create the responsive buttons section"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Calculate responsive button sizing
        button_font_size = self.calculate_responsive_font_size(11, 9, 13)
        button_padding = "8px 15px" if self.width() < 600 else "10px 20px"
        
        button_style_template = """
            QPushButton {{
                border: none;
                padding: {padding};
                border-radius: 5px;
                font-weight: bold;
                font-size: {font_size}px;
            }}
        """
        
        # Help button
        help_btn = QPushButton("❓ " + self.tm.tr("help"))
        help_btn.setFont(QFont("Arial", button_font_size))
        help_btn.clicked.connect(self.show_help)
        help_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        help_btn.setStyleSheet(button_style_template.format(
            padding=button_padding, font_size=button_font_size
        ) + """
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(help_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton(self.tm.tr("cancel"))
        cancel_btn.setFont(QFont("Arial", button_font_size))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        cancel_btn.setStyleSheet(button_style_template.format(
            padding=button_padding, font_size=button_font_size
        ) + """
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        # Launch button
        self.launch_btn = QPushButton("🚀 " + self.tm.tr("launch_application"))
        self.launch_btn.setFont(QFont("Arial", button_font_size, QFont.Weight.Bold))
        self.launch_btn.clicked.connect(self.launch_application)
        self.launch_btn.setDefault(True)
        self.launch_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        launch_padding = "10px 20px" if self.width() < 600 else "12px 25px"
        self.launch_btn.setStyleSheet(button_style_template.format(
            padding=launch_padding, font_size=button_font_size
        ) + """
            QPushButton {
                background-color: #28a745;
                color: white;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        button_layout.addWidget(self.launch_btn)
        
        layout.addLayout(button_layout)
    
    def calculate_responsive_font_size(self, base_size, min_size, max_size):
        """Calculate responsive font size based on window dimensions"""
        width_factor = max(0.7, min(1.3, self.width() / 600))
        height_factor = max(0.7, min(1.3, self.height() / 500))
        
        # Use average of width and height factors
        scale_factor = (width_factor + height_factor) / 2
        
        responsive_size = int(base_size * scale_factor)
        return max(min_size, min(max_size, responsive_size))
    
    def resizeEvent(self, event):
        """Handle window resize events to update responsive elements"""
        super().resizeEvent(event)
        
        # Update description text height constraints
        if hasattr(self, 'description_text'):
            min_height = max(80, int(self.height() * 0.15))
            max_height = max(150, int(self.height() * 0.35))
            self.description_text.setMinimumHeight(min_height)
            self.description_text.setMaximumHeight(max_height)
        
        # Update font sizes for responsive elements
        self.update_responsive_fonts()
    
    def update_responsive_fonts(self):
        """Update font sizes for responsive design"""
        try:
            # Update header fonts
            if hasattr(self, 'launch_btn'):
                # This indicates the UI has been initialized
                
                # Update button styling with new dimensions
                button_font_size = self.calculate_responsive_font_size(11, 9, 13)
                button_padding = "8px 15px" if self.width() < 600 else "10px 20px"
                
                # Update launch button specifically
                launch_padding = "10px 20px" if self.width() < 600 else "12px 25px"
                
                # Note: In a production app, you might want to store references to all
                # elements that need font updates and update them here
                
        except Exception as e:
            # Silently handle any issues during font updates
            pass
    
    def on_version_changed(self):
        """Handle version selection change"""
        if self.single_radio.isChecked():
            self.selected_mode = "single"
        else:
            self.selected_mode = "multi"
        
        self.update_description()
    
    def update_description(self):
        """Update the description text based on selected version"""
        show_detailed = self.show_info_checkbox.isChecked()
        
        if self.selected_mode == "single":
            if show_detailed:
                description = f"""
<h3>{self.tm.tr("single_company_mode")}</h3>
<p><b>{self.tm.tr("ideal_for")}:</b></p>
<ul>
<li>{self.tm.tr("small_taxi_companies")}</li>
<li>{self.tm.tr("individual_fleet_operators")}</li>
<li>{self.tm.tr("simple_fleet_management")}</li>
</ul>
<p><b>{self.tm.tr("features")}:</b></p>
<ul>
<li>{self.tm.tr("simplified_interface")}</li>
<li>{self.tm.tr("automatic_company_setup")}</li>
<li>{self.tm.tr("all_standard_features")}</li>
</ul>
                """
            else:
                description = f"""
<h3>{self.tm.tr("single_company_mode")}</h3>
<p>{self.tm.tr("single_company_description")}</p>
<p><b>{self.tm.tr("best_for")}:</b> {self.tm.tr("single_company_best_for")}</p>
                """
        else:
            if show_detailed:
                description = f"""
<h3>{self.tm.tr("multi_company_mode")}</h3>
<p><b>{self.tm.tr("ideal_for")}:</b></p>
<ul>
<li>{self.tm.tr("fleet_management_companies")}</li>
<li>{self.tm.tr("multi_location_operations")}</li>
<li>{self.tm.tr("consulting_firms")}</li>
</ul>
<p><b>{self.tm.tr("features")}:</b></p>
<ul>
<li>{self.tm.tr("company_selection_dialog")}</li>
<li>{self.tm.tr("full_company_management")}</li>
<li>{self.tm.tr("data_isolation")}</li>
</ul>
                """
            else:
                description = f"""
<h3>{self.tm.tr("multi_company_mode")}</h3>
<p>{self.tm.tr("multi_company_description")}</p>
<p><b>{self.tm.tr("best_for")}:</b> {self.tm.tr("multi_company_best_for")}</p>
                """
        
        self.description_text.setHtml(description)
    
    def show_help(self):
        """Show responsive help dialog with detailed information"""
        help_text = f"""
<h2>{self.tm.tr("help_title")}</h2>

<h3>{self.tm.tr("version_comparison")}</h3>

<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
<tr>
<th>{self.tm.tr("feature")}</th>
<th>{self.tm.tr("single_company")}</th>
<th>{self.tm.tr("multi_company")}</th>
</tr>
<tr>
<td>{self.tm.tr("complexity")}</td>
<td>{self.tm.tr("simple")}</td>
<td>{self.tm.tr("advanced")}</td>
</tr>
<tr>
<td>{self.tm.tr("company_management")}</td>
<td>{self.tm.tr("automatic")}</td>
<td>{self.tm.tr("full_control")}</td>
</tr>
<tr>
<td>{self.tm.tr("data_separation")}</td>
<td>{self.tm.tr("single_dataset")}</td>
<td>{self.tm.tr("isolated_per_company")}</td>
</tr>
<tr>
<td>{self.tm.tr("switching_companies")}</td>
<td>{self.tm.tr("not_available")}</td>
<td>{self.tm.tr("available")}</td>
</tr>
</table>

<h3>{self.tm.tr("getting_started")}</h3>
<p>{self.tm.tr("help_getting_started")}</p>

<h3>{self.tm.tr("need_help")}</h3>
<p>{self.tm.tr("help_contact_info")}</p>
        """
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle(self.tm.tr("help"))
        help_dialog.setModal(True)
        
        # Make help dialog responsive too
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        help_width = min(700, int(screen_geometry.width() * 0.6))
        help_height = min(500, int(screen_geometry.height() * 0.7))
        help_dialog.resize(help_width, help_height)
        
        # Center help dialog
        help_dialog.move(
            screen_geometry.center().x() - help_dialog.width() // 2,
            screen_geometry.center().y() - help_dialog.height() // 2
        )
        
        layout = QVBoxLayout(help_dialog)
        
        help_text_widget = QTextEdit()
        help_text_widget.setHtml(help_text)
        help_text_widget.setReadOnly(True)
        help_text_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(help_text_widget)
        
        close_btn = QPushButton(self.tm.tr("close"))
        close_btn.clicked.connect(help_dialog.accept)
        close_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout.addWidget(close_btn)
        
        help_dialog.exec()
    
    def load_saved_preference(self):
        """Load saved launch preference if available"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '.launcher_config')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read().strip()
                    if content.startswith('default_mode='):
                        mode = content.split('=')[1]
                        if mode == "multi":
                            self.multi_radio.setChecked(True)
                            self.selected_mode = "multi"
                        self.remember_checkbox.setChecked(True)
        except Exception as e:
            print(f"Could not load launch preference: {e}")
    
    def launch_application(self):
        """Launch the selected application version"""
        self.launch_btn.setEnabled(False)
        self.launch_btn.setText(self.tm.tr("launching"))
        
        # Create and start launch thread
        self.launch_thread = AppLaunchThread(
            self.selected_mode, 
            self.remember_checkbox.isChecked()
        )
        self.launch_thread.finished_signal.connect(self.on_launch_finished)
        self.launch_thread.start()
    
    def on_launch_finished(self, success, message):
        """Handle launch completion"""
        if success:
            # Close the launcher after successful launch
            QTimer.singleShot(1000, self.accept)  # Small delay to show success
        else:
            # Show error message
            QMessageBox.critical(self, self.tm.tr("launch_error"), message)
            self.launch_btn.setEnabled(True)
            self.launch_btn.setText("🚀 " + self.tm.tr("launch_application"))

def check_auto_launch():
    """Check if there's a saved preference for auto-launch"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '.launcher_config')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read().strip()
                if content.startswith('default_mode='):
                    return content.split('=')[1]
    except Exception:
        pass
    return None

def create_splash_screen():
    """Create a responsive splash screen for the launcher"""
    # Get screen size for responsive splash
    screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    
    splash_width = min(400, int(screen_geometry.width() * 0.3))
    splash_height = min(200, int(screen_geometry.height() * 0.15))
    
    splash_pixmap = QPixmap(splash_width, splash_height)
    splash_pixmap.fill(QColor("#3498db"))
    
    painter = QPainter(splash_pixmap)
    painter.setPen(QColor("white"))
    
    # Responsive font size for splash
    font_size = max(12, min(20, int(splash_width / 20)))
    painter.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
    painter.drawText(splash_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, 
                    "🚗 Ride Guardian Desktop\nStarting...")
    painter.end()
    
    return QSplashScreen(splash_pixmap)

def main():
    """Main entry point for the launcher"""
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash = create_splash_screen()
    splash.show()
    app.processEvents()
    
    # Small delay for splash screen
    QTimer.singleShot(1500, splash.close)
    
    # Check for auto-launch preference
    auto_mode = check_auto_launch()
    
    if auto_mode and len(sys.argv) == 1:  # Only auto-launch if no command line args
        # Auto-launch the preferred version
        try:
            if auto_mode == "single":
                script_name = "main_single_company.py"
            else:
                script_name = "main_multi_company.py"
            
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            subprocess.Popen([sys.executable, script_path], 
                           cwd=os.path.dirname(__file__))
            return 0
        except Exception as e:
            print(f"Auto-launch failed: {e}")
            # Fall through to show launcher dialog
    
    # Show launcher dialog
    QTimer.singleShot(1500, lambda: show_launcher(app))
    
    return app.exec()

def show_launcher(app):
    """Show the launcher dialog"""
    launcher = ApplicationLauncher()
    if launcher.exec() == QDialog.DialogCode.Accepted:
        # Application was launched successfully
        pass
    else:
        # User cancelled, exit
        app.quit()

if __name__ == "__main__":
    # Ensure proper working directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.chdir(project_root)
    
    print("Ride Guardian Desktop - Application Launcher")
    print(f"Working directory: {os.getcwd()}")
    
    sys.exit(main())