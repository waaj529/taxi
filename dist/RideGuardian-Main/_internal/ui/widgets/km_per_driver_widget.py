import sys
import os
from datetime import datetime, timedelta

from PyQt6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QDate

# Adjust import path based on project structure
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from core import analysis_service # Assuming analysis_service.py is in core
from core.translation_manager import TranslationManager # For UI text

class KmPerDriverWidget(QWidget):
    def __init__(self, company_id: int, start_date: QDate, end_date: QDate, parent=None):
        super().__init__(parent)
        self.company_id = company_id
        # Convert QDate to datetime for analysis_service
        self.start_date = datetime(start_date.year(), start_date.month(), start_date.day())
        self.end_date = datetime(end_date.year(), end_date.month(), end_date.day(), 23, 59, 59) # End of day

        self.tm = TranslationManager()
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Header with Title and Save Button ---
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.tm.tr("km_per_driver_chart_title")) # Default text if key not found
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)

        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.save_button = QPushButton(self.tm.tr("save_chart"))
        self.save_button.setToolTip(self.tm.tr("save_chart_tooltip"))
        self.save_button.setStyleSheet("padding: 5px 10px; font-size: 12px;")
        self.save_button.clicked.connect(self.save_chart_as_png)
        header_layout.addWidget(self.save_button)
        
        main_layout.addLayout(header_layout)

        # --- Query data & build bar series ---
        try:
            data_df = analysis_service.km_per_driver(self.company_id, self.start_date, self.end_date)
        except Exception as e:
            print(f"Error fetching data for KmPerDriverWidget: {e}")
            error_label = QLabel(self.tm.tr("chart_data_error"))
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)
            return

        if data_df.empty:
            no_data_label = QLabel(self.tm.tr("no_data_for_chart"))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("font-style: italic; color: #777;")
            main_layout.addWidget(no_data_label)
            self.save_button.setEnabled(False) # Disable save if no data
            return

        bar_set = QBarSet(self.tm.tr("kilometers"))
        # Ensure values are float or int for QBarSet
        bar_set.append([float(val) if val is not None else 0.0 for val in data_df["km"].values])
        
        # Apply a color - corporate green or similar
        bar_set.setColor(QColor("#009E60"))


        series = QBarSeries()
        series.append(bar_set)

        self.chart = QChart() # Store chart as instance variable for saving
        self.chart.addSeries(series)
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        chart_title_text = self.tm.tr("period_chart_title")
        self.chart.setTitle(chart_title_text.format(
            start_date=self.start_date.strftime("%d.%m.%Y"),
            end_date=self.end_date.strftime("%d.%m.%Y"))
        )
        self.chart.titleFont().setPointSize(10)


        # Axis with driver names
        axis_x = QBarCategoryAxis()
        axis_x.append(list(data_df["driver"].values))
        
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        # Optional: Add Y-axis for clarity, Qt creates a default one if not specified
        # axis_y = QValueAxis()
        # chart.addAxis(axis_y, Qt.AlignLeft)
        # series.attachAxis(axis_y)

        self.chart.legend().setVisible(False) # Legend not really needed for single bar set

        # Apply a theme
        self.chart.setTheme(QChart.ChartTheme.ChartThemeLight)

        self.chart_view = QChartView(self.chart) # Store view for saving
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(300) # Ensure it's not too small

        main_layout.addWidget(self.chart_view)

    def update_chart_data(self, company_id: int, start_date: QDate, end_date: QDate):
        self.company_id = company_id
        self.start_date = datetime(start_date.year(), start_date.month(), start_date.day())
        self.end_date = datetime(end_date.year(), end_date.month(), end_date.day(), 23, 59, 59)

        # Clear existing series and axes if any from a previous build
        if hasattr(self, 'chart'):
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
        
        # Remove the old chart_view if it exists
        if hasattr(self, 'chart_view'):
            # Find the chart_view in the layout and remove it
            for i in reversed(range(self.layout().count())): 
                item = self.layout().itemAt(i)
                if item.widget() == self.chart_view:
                    widget_to_remove = item.widget()
                    self.layout().removeWidget(widget_to_remove)
                    widget_to_remove.deleteLater()
                    break
            del self.chart_view
            del self.chart
        
        # Remove no_data_label or error_label if they exist
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QLabel) and item.widget() != self.findChild(QLabel, "title_label"): # Don't remove title
                 # More robust check: if its text matches no_data or error text
                if self.tm.tr("no_data_for_chart") in item.widget().text() or self.tm.tr("chart_data_error") in item.widget().text():
                    widget_to_remove = item.widget()
                    self.layout().removeWidget(widget_to_remove)
                    widget_to_remove.deleteLater()
                    break
        
        # Re-fetch data and build UI components that depend on data
        try:
            data_df = analysis_service.km_per_driver(self.company_id, self.start_date, self.end_date)
        except Exception as e:
            print(f"Error fetching data for KmPerDriverWidget update: {e}")
            error_label = QLabel(self.tm.tr("chart_data_error"))
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout().addWidget(error_label)
            self.save_button.setEnabled(False)
            return

        if data_df.empty:
            no_data_label = QLabel(self.tm.tr("no_data_for_chart"))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("font-style: italic; color: #777;")
            self.layout().addWidget(no_data_label)
            self.save_button.setEnabled(False)
            return

        self.save_button.setEnabled(True)
        bar_set = QBarSet(self.tm.tr("kilometers"))
        bar_set.append([float(val) if val is not None else 0.0 for val in data_df["km"].values])
        bar_set.setColor(QColor("#009E60"))

        series = QBarSeries()
        series.append(bar_set)

        self.chart = QChart()
        self.chart.addSeries(series)
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart_title_text = self.tm.tr("period_chart_title")
        self.chart.setTitle(chart_title_text.format(
            start_date=self.start_date.strftime("%d.%m.%Y"),
            end_date=self.end_date.strftime("%d.%m.%Y"))
        )
        self.chart.titleFont().setPointSize(10)

        axis_x = QBarCategoryAxis()
        axis_x.append(list(data_df["driver"].values))
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        self.chart.legend().setVisible(False)
        self.chart.setTheme(QChart.ChartTheme.ChartThemeLight)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(300)
        self.layout().addWidget(self.chart_view)


    def save_chart_as_png(self):
        if not hasattr(self, 'chart_view') or not self.chart_view.chart():
            # This case should ideally be prevented by disabling the button if chart isn't generated
            print("Chart not available for saving.")
            return

        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QStandardPaths
        
        # Default filename suggestion
        default_filename = f"km_pro_fahrer_{self.start_date.strftime('%Y-%m-%d')}_{self.end_date.strftime('%Y-%m-%d')}.png"
        
        # Get user's Pictures directory or Desktop as fallback
        save_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        if not save_dir:
            save_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tm.tr("save_chart_dialog_title"),
            os.path.join(save_dir, default_filename),
            self.tm.tr("image_files_filter")
        )

        if file_path:
            pixmap = self.chart_view.grab()
            if pixmap.save(file_path, "PNG"):
                print(f"Chart saved to {file_path}")
                # Optionally, show a success message to the user via QMessageBox
                # QMessageBox.information(self, self.tm.tr("success"), self.tm.tr("chart_saved_success", "Diagramm erfolgreich gespeichert."))
            else:
                print(f"Failed to save chart to {file_path}")
                # QMessageBox.warning(self, self.tm.tr("error"), self.tm.tr("chart_saved_error", "Fehler beim Speichern des Diagramms."))

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # --- Mocking for standalone test ---
    # You would need a running DB with data for real testing via analysis_service
    # This mock allows UI to render
    class MockAnalysisService:
        def km_per_driver(self, company_id, start_date, end_date):
            import pandas as pd
            # Simulate some data
            if start_date.month == datetime.now().month : # More data for current month
                 return pd.DataFrame({'driver': ['Fahrer A', 'Fahrer B', 'Fahrer C', 'Fahrer D'], 
                                     'km': [1200.5, 950.2, 1500.0, 750.8]})
            else: # Less data for other months
                 return pd.DataFrame({'driver': ['Fahrer A', 'Fahrer B'], 
                                     'km': [300.0, 450.7]})


    original_analysis_service = analysis_service # Store original
    analysis_service = MockAnalysisService() # Replace with mock
    
    # Dummy dates for testing KmPerDriverWidget
    current_qdate = QDate.currentDate()
    start_qdate = current_qdate.addMonths(-1).addDays(-current_qdate.day() +1) # First day of last month
    end_qdate = start_qdate.addMonths(1).addDays(-1) # Last day of last month

    widget = KmPerDriverWidget(company_id=1, start_date=start_qdate, end_date=end_qdate)
    widget.setWindowTitle("Km pro Fahrer Test")
    widget.setGeometry(100, 100, 700, 500) # Give it some size
    widget.show()

    # Test update_chart_data
    def test_update():
        print("Updating chart data...")
        new_start_qdate = QDate.currentDate().addDays(-QDate.currentDate().day() +1) # This month
        new_end_qdate = QDate.currentDate()
        widget.update_chart_data(company_id=1, start_date=new_start_qdate, end_date=new_end_qdate)

    # Add a button to test update
    update_button = QPushButton("Update auf aktuellen Monat")
    update_button.clicked.connect(test_update)
    
    test_window = QWidget()
    test_layout = QVBoxLayout(test_window)
    test_layout.addWidget(widget)
    test_layout.addWidget(update_button)
    test_window.setWindowTitle("Chart Test")
    test_window.setGeometry(100,100,700,600)
    test_window.show()
    
    analysis_service = original_analysis_service # Restore original

    sys.exit(app.exec()) 