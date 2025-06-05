import sys
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QGridLayout, QFrame, QScrollArea, QTextEdit, QFileDialog, QProgressBar,
    QGroupBox, QFormLayout, QDialog, QCheckBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QCoreApplication
from PyQt6.QtGui import QFont, QPixmap
import sqlite3
from typing import Dict, List, Optional
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection, get_companies
from core.payroll_calculator import PayrollCalculator
from core.fahrtenbuch_export import FahrtenbuchExporter
from ui.widgets.km_per_driver_widget import KmPerDriverWidget

class ReportGeneratorThread(QThread):
    progress = pyqtSignal(int)
    report_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self, report_type, start_date, end_date, driver_id=None):
        super().__init__()
        self.report_type = report_type
        self.start_date = start_date
        self.end_date = end_date
        self.driver_id = driver_id
        
    def run(self):
        try:
            self.status_update.emit("Connecting to database...")
            db = get_db_connection()
            generator = ReportGenerator(db)
            
            self.progress.emit(20)
            self.status_update.emit("Generating report data...")
            
            if self.report_type == "daily":
                report = generator.generate_daily_report(self.start_date, self.driver_id)
            elif self.report_type == "weekly":
                report = generator.generate_weekly_report(self.start_date, self.end_date)
            elif self.report_type == "monthly":
                report = generator.generate_monthly_report(self.start_date)
            elif self.report_type == "driver_effectiveness":
                report = generator.generate_driver_effectiveness_report(self.start_date, self.end_date)
            elif self.report_type == "compliance":
                report = generator.generate_compliance_report(self.start_date, self.end_date)
            else:
                raise ValueError(f"Unknown report type: {self.report_type}")
            
            self.progress.emit(60)
            self.status_update.emit("Generating charts...")
            
            # Generate charts
            charts = generator.generate_charts(report, self.report_type)
            report['charts'] = charts
            
            self.progress.emit(100)
            self.status_update.emit("Report ready!")
            self.report_ready.emit(report)
            
        except Exception as e:
            self.error.emit(f"Report generation failed: {str(e)}")
        finally:
            if 'db' in locals():
                db.close()

class ReportGenerator:
    """Advanced reporting engine with dynamic chart generation"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def safe_get(self, row, key, default=0):
        """Safe way to get value from SQLite Row object"""
        try:
            return row[key] if row[key] is not None else default
        except (KeyError, IndexError, TypeError):
            return default
    
    def row_to_dict(self, row):
        """Convert SQLite Row to dictionary"""
        if row is None:
            return {}
        try:
            return dict(row)
        except:
            return {}
        
    def generate_daily_report(self, date: str, driver_id: Optional[int] = None) -> Dict:
        """Generate comprehensive daily report"""
        cursor = self.db.cursor()
        
        # Base query
        base_query = """
            SELECT r.*, d.name as driver_name, d.vehicle
            FROM rides r
            JOIN drivers d ON r.driver_id = d.id
            WHERE DATE(r.pickup_time) = ?
        """
        params = [date]
        
        if driver_id:
            base_query += " AND r.driver_id = ?"
            params.append(driver_id)
            
        cursor.execute(base_query + " ORDER BY r.pickup_time", params)
        rides = cursor.fetchall()
        
        # Calculate metrics
        total_rides = len(rides)
        completed_rides = sum(1 for r in rides if r['status'] == 'Completed')
        violation_rides = sum(1 for r in rides if self.safe_get(r, 'violations') and self.safe_get(r, 'violations') != '[]')
        total_revenue = sum(self.safe_get(r, 'revenue', 0) for r in rides)
        total_distance = sum(self.safe_get(r, 'distance_km', 0) for r in rides)
        
        # Driver performance breakdown
        driver_stats = {}
        for ride in rides:
            driver_name = ride['driver_name']
            if driver_name not in driver_stats:
                driver_stats[driver_name] = {
                    'rides': 0, 'revenue': 0, 'violations': 0, 'distance': 0
                }
            
            driver_stats[driver_name]['rides'] += 1
            driver_stats[driver_name]['revenue'] += self.safe_get(ride, 'revenue', 0)
            driver_stats[driver_name]['distance'] += self.safe_get(ride, 'distance_km', 0)
            
            if self.safe_get(ride, 'violations') and self.safe_get(ride, 'violations') != '[]':
                driver_stats[driver_name]['violations'] += 1
        
        # Hourly distribution
        hourly_stats = {}
        for ride in rides:
            try:
                hour = datetime.fromisoformat(ride['pickup_time']).hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = {'rides': 0, 'revenue': 0}
                hourly_stats[hour]['rides'] += 1
                hourly_stats[hour]['revenue'] += self.safe_get(ride, 'revenue', 0)
            except:
                continue
        
        return {
            'date': date,
            'summary': {
                'total_rides': total_rides,
                'completed_rides': completed_rides,
                'violation_rides': violation_rides,
                'compliance_rate': round((completed_rides / total_rides * 100) if total_rides > 0 else 0, 1),
                'total_revenue': round(total_revenue, 2),
                'total_distance_km': round(total_distance, 2),
                'avg_revenue_per_ride': round(total_revenue / total_rides if total_rides > 0 else 0, 2)
            },
            'driver_breakdown': driver_stats,
            'hourly_distribution': hourly_stats,
            'raw_data': [self.row_to_dict(r) for r in rides]
        }
    
    def generate_weekly_report(self, start_date: str, end_date: str) -> Dict:
        """Generate weekly comparison report"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(r.pickup_time) as ride_date,
                COUNT(*) as total_rides,
                SUM(CASE WHEN r.status = 'Completed' THEN 1 ELSE 0 END) as completed_rides,
                SUM(CASE WHEN r.violations IS NOT NULL AND r.violations != '[]' THEN 1 ELSE 0 END) as violation_rides,
                SUM(COALESCE(r.revenue, 0)) as total_revenue,
                SUM(COALESCE(r.distance_km, 0)) as total_distance,
                COUNT(DISTINCT r.driver_id) as active_drivers
            FROM rides r
            WHERE DATE(r.pickup_time) BETWEEN ? AND ?
            GROUP BY DATE(r.pickup_time)
            ORDER BY ride_date
        """, (start_date, end_date))
        
        daily_stats = cursor.fetchall()
        
        # Weekly totals
        week_totals = {
            'total_rides': sum(self.safe_get(d, 'total_rides', 0) for d in daily_stats),
            'total_revenue': sum(self.safe_get(d, 'total_revenue', 0) for d in daily_stats),
            'total_distance': sum(self.safe_get(d, 'total_distance', 0) for d in daily_stats),
            'avg_compliance_rate': 0
        }
        
        if daily_stats:
            total_completed = sum(self.safe_get(d, 'completed_rides', 0) for d in daily_stats)
            total_rides = sum(self.safe_get(d, 'total_rides', 0) for d in daily_stats)
            week_totals['avg_compliance_rate'] = round(
                (total_completed / total_rides * 100) if total_rides > 0 else 0, 1
            )
        
        # Driver performance for the week
        cursor.execute("""
            SELECT 
                d.name as driver_name,
                COUNT(r.id) as total_rides,
                SUM(COALESCE(r.revenue, 0)) as total_revenue,
                SUM(CASE WHEN r.violations IS NOT NULL AND r.violations != '[]' THEN 1 ELSE 0 END) as violations,
                AVG(COALESCE(r.distance_km, 0)) as avg_distance
            FROM rides r
            JOIN drivers d ON r.driver_id = d.id
            WHERE DATE(r.pickup_time) BETWEEN ? AND ?
            GROUP BY d.id, d.name
            ORDER BY total_revenue DESC
        """, (start_date, end_date))
        
        driver_performance = cursor.fetchall()
        
        return {
            'period': f"{start_date} to {end_date}",
            'week_totals': week_totals,
            'daily_breakdown': [self.row_to_dict(d) for d in daily_stats],
            'driver_performance': [self.row_to_dict(d) for d in driver_performance]
        }
    
    def generate_monthly_report(self, month_year: str) -> Dict:
        """Generate comprehensive monthly report"""
        # Extract year and month
        try:
            year, month = month_year.split('-')
            start_date = f"{year}-{month:0>2}-01"
            
            # Calculate last day of month
            import calendar
            last_day = calendar.monthrange(int(year), int(month))[1]
            end_date = f"{year}-{month:0>2}-{last_day}"
        except:
            raise ValueError("Month should be in YYYY-MM format")
        
        cursor = self.db.cursor()
        
        # Monthly summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rides,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_rides,
                SUM(CASE WHEN violations IS NOT NULL AND violations != '[]' THEN 1 ELSE 0 END) as violation_rides,
                SUM(COALESCE(revenue, 0)) as total_revenue,
                SUM(COALESCE(distance_km, 0)) as total_distance,
                COUNT(DISTINCT driver_id) as active_drivers,
                COUNT(DISTINCT vehicle_plate) as active_vehicles
            FROM rides
            WHERE DATE(pickup_time) BETWEEN ? AND ?
        """, (start_date, end_date))
        
        monthly_summary = cursor.fetchone()
        
        # Weekly breakdown within the month
        cursor.execute("""
            SELECT 
                strftime('%W', pickup_time) as week_number,
                COUNT(*) as rides,
                SUM(COALESCE(revenue, 0)) as revenue
            FROM rides
            WHERE DATE(pickup_time) BETWEEN ? AND ?
            GROUP BY strftime('%W', pickup_time)
            ORDER BY week_number
        """, (start_date, end_date))
        
        weekly_breakdown = cursor.fetchall()
        
        # Top performing drivers
        cursor.execute("""
            SELECT 
                d.name,
                COUNT(r.id) as rides,
                SUM(COALESCE(r.revenue, 0)) as revenue,
                ROUND(AVG(COALESCE(r.distance_km, 0)), 2) as avg_distance,
                SUM(CASE WHEN r.violations IS NOT NULL AND r.violations != '[]' THEN 1 ELSE 0 END) as violations
            FROM rides r
            JOIN drivers d ON r.driver_id = d.id
            WHERE DATE(r.pickup_time) BETWEEN ? AND ?
            GROUP BY d.id, d.name
            ORDER BY revenue DESC
            LIMIT 10
        """, (start_date, end_date))
        
        top_drivers = cursor.fetchall()
        
        # Calculate payroll summary using PayrollCalculator
        payroll_calculator = PayrollCalculator(self.db)
        payroll_summary = {
            'total_payroll': 0,
            'total_bonuses': 0,
            'compliance_issues': 0
        }
        
        try:
            cursor.execute("SELECT id FROM drivers WHERE status = 'Active'")
            active_drivers = cursor.fetchall()
            
            for driver in active_drivers:
                try:
                    payroll = payroll_calculator.calculate_driver_payroll(
                        driver['id'], start_date, end_date
                    )
                    payroll_summary['total_payroll'] += payroll.get('total_pay', 0)
                    payroll_summary['total_bonuses'] += payroll.get('bonuses', {}).get('total_bonuses', 0)
                    if not payroll.get('compliance', {}).get('is_compliant', True):
                        payroll_summary['compliance_issues'] += 1
                except:
                    continue
        except:
            pass
        
        return {
            'month_year': month_year,
            'period': f"{start_date} to {end_date}",
            'summary': self.row_to_dict(monthly_summary),
            'weekly_breakdown': [self.row_to_dict(w) for w in weekly_breakdown],
            'top_drivers': [self.row_to_dict(d) for d in top_drivers],
            'payroll_summary': payroll_summary
        }
    
    def generate_driver_effectiveness_report(self, start_date: str, end_date: str) -> Dict:
        """Generate driver effectiveness analysis"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT 
                d.id,
                d.name,
                COUNT(r.id) as total_rides,
                SUM(COALESCE(r.revenue, 0)) as total_revenue,
                AVG(COALESCE(r.revenue, 0)) as avg_revenue_per_ride,
                SUM(COALESCE(r.distance_km, 0)) as total_distance,
                AVG(COALESCE(r.distance_km, 0)) as avg_distance_per_ride,
                SUM(CASE WHEN r.violations IS NOT NULL AND r.violations != '[]' THEN 1 ELSE 0 END) as violation_count,
                COUNT(CASE WHEN r.status = 'Completed' THEN 1 END) as completed_rides
            FROM drivers d
            LEFT JOIN rides r ON d.id = r.driver_id 
                AND DATE(r.pickup_time) BETWEEN ? AND ?
            WHERE d.status = 'Active'
            GROUP BY d.id, d.name
            HAVING COUNT(r.id) > 0
            ORDER BY total_revenue DESC
        """, (start_date, end_date))
        
        driver_stats = cursor.fetchall()
        
        # Calculate effectiveness metrics
        effectiveness_data = []
        for driver in driver_stats:
            # Revenue per hour (estimate based on 8-hour shifts and ride count)
            estimated_hours = (self.safe_get(driver, 'total_rides', 0) / 3) if self.safe_get(driver, 'total_rides', 0) > 0 else 1  # Rough estimate
            revenue_per_hour = self.safe_get(driver, 'total_revenue', 0) / estimated_hours if estimated_hours > 0 else 0
            
            # Compliance rate
            total_rides = self.safe_get(driver, 'total_rides', 0)
            completed_rides = self.safe_get(driver, 'completed_rides', 0)
            violation_count = self.safe_get(driver, 'violation_count', 0)
            compliance_rate = ((completed_rides - violation_count) / total_rides * 100) if total_rides > 0 else 0
            
            # Efficiency score (combination of revenue/hour and compliance)
            efficiency_score = (revenue_per_hour * 0.7) + (compliance_rate * 0.3)
            
            effectiveness_data.append({
                'driver_id': self.safe_get(driver, 'id'),
                'driver_name': self.safe_get(driver, 'name', ''),
                'total_rides': total_rides,
                'total_revenue': round(self.safe_get(driver, 'total_revenue', 0), 2),
                'avg_revenue_per_ride': round(self.safe_get(driver, 'avg_revenue_per_ride', 0), 2),
                'revenue_per_hour': round(revenue_per_hour, 2),
                'compliance_rate': round(compliance_rate, 1),
                'violation_count': violation_count,
                'efficiency_score': round(efficiency_score, 2),
                'total_distance': round(self.safe_get(driver, 'total_distance', 0), 2),
                'avg_distance_per_ride': round(self.safe_get(driver, 'avg_distance_per_ride', 0), 2)
            })
        
        # Sort by efficiency score
        effectiveness_data.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        return {
            'period': f"{start_date} to {end_date}",
            'driver_effectiveness': effectiveness_data,
            'summary': {
                'total_drivers': len(effectiveness_data),
                'avg_efficiency_score': round(sum(d['efficiency_score'] for d in effectiveness_data) / 
                                            len(effectiveness_data) if effectiveness_data else 0, 2),
                'top_performer': effectiveness_data[0]['driver_name'] if effectiveness_data else None,
                'avg_compliance_rate': round(sum(d['compliance_rate'] for d in effectiveness_data) / 
                                           len(effectiveness_data) if effectiveness_data else 0, 1)
            }
        }
    
    def generate_compliance_report(self, start_date: str, end_date: str) -> Dict:
        """Generate detailed compliance analysis"""
        cursor = self.db.cursor()
        
        # Overall compliance stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rides,
                SUM(CASE WHEN violations IS NULL OR violations = '[]' OR violations = '' THEN 1 ELSE 0 END) as compliant_rides,
                SUM(CASE WHEN violations IS NOT NULL AND violations != '[]' AND violations != '' THEN 1 ELSE 0 END) as violation_rides
            FROM rides
            WHERE DATE(pickup_time) BETWEEN ? AND ?
        """, (start_date, end_date))
        
        overall_stats = cursor.fetchone()
        
        # Violation breakdown by type
        cursor.execute("""
            SELECT violations
            FROM rides
            WHERE DATE(pickup_time) BETWEEN ? AND ?
            AND violations IS NOT NULL AND violations != '[]' AND violations != ''
        """, (start_date, end_date))
        
        violation_records = cursor.fetchall()
        
        # Parse violations and count by type
        violation_types = {}
        for record in violation_records:
            try:
                violations = json.loads(self.safe_get(record, 'violations', '[]'))
                for violation in violations:
                    if 'RULE_1' in violation:
                        violation_types['Shift Start (Rule 1)'] = violation_types.get('Shift Start (Rule 1)', 0) + 1
                    elif 'RULE_2' in violation:
                        violation_types['Pickup Distance (Rule 2)'] = violation_types.get('Pickup Distance (Rule 2)', 0) + 1
                    elif 'RULE_3' in violation:
                        violation_types['Post-ride Logic (Rule 3)'] = violation_types.get('Post-ride Logic (Rule 3)', 0) + 1
                    elif 'RULE_4' in violation:
                        violation_types['Time Gap (Rule 4)'] = violation_types.get('Time Gap (Rule 4)', 0) + 1
                    elif 'RULE_5' in violation:
                        violation_types['Route Logic (Rule 5)'] = violation_types.get('Route Logic (Rule 5)', 0) + 1
                    else:
                        violation_types['Other'] = violation_types.get('Other', 0) + 1
            except:
                violation_types['Parse Error'] = violation_types.get('Parse Error', 0) + 1
        
        # Driver compliance ranking
        cursor.execute("""
            SELECT 
                d.name,
                COUNT(r.id) as total_rides,
                SUM(CASE WHEN r.violations IS NULL OR r.violations = '[]' OR r.violations = '' THEN 1 ELSE 0 END) as compliant_rides,
                SUM(CASE WHEN r.violations IS NOT NULL AND r.violations != '[]' AND r.violations != '' THEN 1 ELSE 0 END) as violation_rides
            FROM drivers d
            JOIN rides r ON d.id = r.driver_id
            WHERE DATE(r.pickup_time) BETWEEN ? AND ?
            GROUP BY d.id, d.name
            HAVING COUNT(r.id) > 0
            ORDER BY (CAST(SUM(CASE WHEN r.violations IS NULL OR r.violations = '[]' OR r.violations = '' THEN 1 ELSE 0 END) AS REAL) / COUNT(r.id)) DESC
        """, (start_date, end_date))
        
        driver_compliance = cursor.fetchall()
        
        # Calculate compliance rates
        driver_compliance_data = []
        for driver in driver_compliance:
            total_rides = self.safe_get(driver, 'total_rides', 0)
            compliant_rides = self.safe_get(driver, 'compliant_rides', 0)
            compliance_rate = (compliant_rides / total_rides * 100) if total_rides > 0 else 0
            driver_compliance_data.append({
                'driver_name': self.safe_get(driver, 'name', ''),
                'total_rides': total_rides,
                'compliant_rides': compliant_rides,
                'violation_rides': self.safe_get(driver, 'violation_rides', 0),
                'compliance_rate': round(compliance_rate, 1)
            })
        
        total_rides = self.safe_get(overall_stats, 'total_rides', 0)
        compliant_rides = self.safe_get(overall_stats, 'compliant_rides', 0)
        overall_compliance_rate = (compliant_rides / total_rides * 100) if total_rides > 0 else 0
        
        return {
            'period': f"{start_date} to {end_date}",
            'overall_compliance_rate': round(overall_compliance_rate, 1),
            'total_rides': total_rides,
            'compliant_rides': compliant_rides,
            'violation_rides': self.safe_get(overall_stats, 'violation_rides', 0),
            'violation_breakdown': violation_types,
            'driver_compliance': driver_compliance_data
        }
    
    def generate_charts(self, report_data: Dict, report_type: str) -> Dict:
        """Generate charts for the report"""
        charts = {}
        chart_dir = os.path.join(PROJECT_ROOT, 'temp_charts')
        os.makedirs(chart_dir, exist_ok=True)
        
        try:
            if report_type == "daily":
                # Revenue by hour chart
                if 'hourly_distribution' in report_data:
                    hourly_data = report_data['hourly_distribution']
                    hours = sorted(hourly_data.keys())
                    revenues = [hourly_data[h]['revenue'] for h in hours]
                    
                    plt.figure(figsize=(10, 6))
                    plt.bar(hours, revenues, color='skyblue')
                    plt.title('Revenue Distribution by Hour')
                    plt.xlabel('Hour of Day')
                    plt.ylabel('Revenue ($)')
                    plt.grid(True, alpha=0.3)
                    
                    chart_path = os.path.join(chart_dir, 'daily_revenue_by_hour.png')
                    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    charts['hourly_revenue'] = chart_path
                
                # Driver performance pie chart
                if 'driver_breakdown' in report_data:
                    driver_data = report_data['driver_breakdown']
                    drivers = list(driver_data.keys())
                    revenues = [driver_data[d]['revenue'] for d in drivers]
                    
                    if revenues and sum(revenues) > 0:
                        plt.figure(figsize=(8, 8))
                        plt.pie(revenues, labels=drivers, autopct='%1.1f%%', startangle=90)
                        plt.title('Revenue Distribution by Driver')
                        
                        chart_path = os.path.join(chart_dir, 'daily_driver_revenue.png')
                        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        charts['driver_revenue'] = chart_path
            
            elif report_type == "weekly":
                # Daily trend line
                if 'daily_breakdown' in report_data:
                    daily_data = report_data['daily_breakdown']
                    dates = [d['ride_date'] for d in daily_data]
                    revenues = [d['total_revenue'] for d in daily_data]
                    rides = [d['total_rides'] for d in daily_data]
                    
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
                    
                    # Revenue trend
                    ax1.plot(dates, revenues, marker='o', linewidth=2, color='green')
                    ax1.set_title('Daily Revenue Trend')
                    ax1.set_ylabel('Revenue ($)')
                    ax1.grid(True, alpha=0.3)
                    ax1.tick_params(axis='x', rotation=45)
                    
                    # Rides trend
                    ax2.plot(dates, rides, marker='s', linewidth=2, color='blue')
                    ax2.set_title('Daily Rides Count')
                    ax2.set_ylabel('Number of Rides')
                    ax2.set_xlabel('Date')
                    ax2.grid(True, alpha=0.3)
                    ax2.tick_params(axis='x', rotation=45)
                    
                    plt.tight_layout()
                    chart_path = os.path.join(chart_dir, 'weekly_trends.png')
                    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    charts['weekly_trends'] = chart_path
            
            elif report_type == "driver_effectiveness":
                # Driver efficiency comparison
                if 'driver_effectiveness' in report_data:
                    driver_data = report_data['driver_effectiveness'][:10]  # Top 10
                    drivers = [d['driver_name'] for d in driver_data]
                    efficiency_scores = [d['efficiency_score'] for d in driver_data]
                    compliance_rates = [d['compliance_rate'] for d in driver_data]
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                    
                    # Efficiency scores
                    ax1.barh(drivers, efficiency_scores, color='lightcoral')
                    ax1.set_title('Driver Efficiency Scores')
                    ax1.set_xlabel('Efficiency Score')
                    
                    # Compliance rates
                    ax2.barh(drivers, compliance_rates, color='lightgreen')
                    ax2.set_title('Driver Compliance Rates (%)')
                    ax2.set_xlabel('Compliance Rate (%)')
                    
                    plt.tight_layout()
                    chart_path = os.path.join(chart_dir, 'driver_effectiveness.png')
                    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    charts['driver_effectiveness'] = chart_path
            
            elif report_type == "compliance":
                # Violation types pie chart
                if 'violation_breakdown' in report_data:
                    violation_data = report_data['violation_breakdown']
                    if violation_data:
                        violation_types = list(violation_data.keys())
                        violation_counts = list(violation_data.values())
                        
                        plt.figure(figsize=(10, 8))
                        plt.pie(violation_counts, labels=violation_types, autopct='%1.1f%%', startangle=90)
                        plt.title('Violation Types Distribution')
                        
                        chart_path = os.path.join(chart_dir, 'violation_breakdown.png')
                        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        charts['violation_breakdown'] = chart_path
        
        except Exception as e:
            print(f"Chart generation error: {e}")
        
        return charts

class PDFReportGenerator:
    """Generate professional PDF reports"""
    
    def __init__(self, report_data, report_type):
        self.report_data = report_data
        self.report_type = report_type
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkgreen
        )
    
    def generate_pdf(self, filename):
        """Generate complete PDF report"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        title = f"Ride Guardian - {self.report_type.replace('_', ' ').title()} Report"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 12))
        
        # Report period
        if 'period' in self.report_data:
            period_text = f"Report Period: {self.report_data['period']}"
            story.append(Paragraph(period_text, self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        if 'summary' in self.report_data:
            summary_data = []
            for key, value in self.report_data['summary'].items():
                if isinstance(value, (int, float)):
                    if 'rate' in key.lower() or 'percentage' in key.lower():
                        formatted_value = f"{value}%"
                    elif 'revenue' in key.lower() or 'pay' in key.lower():
                        formatted_value = f"${value:,.2f}"
                    else:
                        formatted_value = f"{value:,}"
                else:
                    formatted_value = str(value)
                
                summary_data.append([key.replace('_', ' ').title(), formatted_value])
            
            if summary_data:
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 20))
        
        # Add charts if available
        if 'charts' in self.report_data:
            story.append(Paragraph("Visual Analytics", self.heading_style))
            for chart_name, chart_path in self.report_data['charts'].items():
                if os.path.exists(chart_path):
                    try:
                        chart_img = Image(chart_path, width=6*inch, height=4*inch)
                        story.append(chart_img)
                        story.append(Spacer(1, 12))
                    except:
                        continue
        
        # Detailed data tables
        self.add_detailed_tables(story)
        
        # Build PDF
        doc.build(story)
    
    def add_detailed_tables(self, story):
        """Add detailed data tables to PDF"""
        if self.report_type == "driver_effectiveness" and 'driver_effectiveness' in self.report_data:
            story.append(Paragraph("Driver Performance Details", self.heading_style))
            
            data = [['Driver', 'Rides', 'Revenue', 'Efficiency Score', 'Compliance Rate']]
            for driver in self.report_data['driver_effectiveness'][:10]:  # Top 10
                data.append([
                    driver['driver_name'],
                    str(driver['total_rides']),
                    f"${driver['total_revenue']:.2f}",
                    f"{driver['efficiency_score']:.2f}",
                    f"{driver['compliance_rate']}%"
                ])
            
            table = Table(data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.2*inch, 1.1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)

class ExportWorker(QThread):
    """Worker thread for handling export operations without blocking the UI"""
    
    finished = pyqtSignal(str)  # Signal with result message
    progress = pyqtSignal(int)  # Signal with progress percentage
    error = pyqtSignal(str)     # Signal with error message
    
    def __init__(self, export_type, company_id, driver_id=None, start_date=None, end_date=None):
        super().__init__()
        self.export_type = export_type
        self.company_id = company_id
        self.driver_id = driver_id
        self.start_date = start_date
        self.end_date = end_date
        
    def run(self):
        try:
            self.progress.emit(10)
            
            exporter = FahrtenbuchExporter(self.company_id)
            
            self.progress.emit(30)
            
            if self.export_type == 'fahrtenbuch_excel':
                output_path = exporter.export_fahrtenbuch_excel(
                    driver_id=self.driver_id,
                    start_date=self.start_date,
                    end_date=self.end_date
                )
            elif self.export_type == 'fahrtenbuch_pdf':
                output_path = exporter.export_fahrtenbuch_pdf(
                    driver_id=self.driver_id,
                    start_date=self.start_date,
                    end_date=self.end_date
                )
            else:
                raise ValueError(f"Unbekannter Export-Typ: {self.export_type}")
                
            self.progress.emit(100)
            self.finished.emit(f"Export erfolgreich erstellt: {output_path}")
            
        except Exception as e:
            self.error.emit(f"Fehler beim Export: {str(e)}")

class FahrtenbuchExportDialog(QDialog):
    """Dialog for configuring Fahrtenbuch export options"""
    
    def __init__(self, company_id, parent=None):
        super().__init__(parent)
        self.company_id = company_id
        self.setWindowTitle(self.tr("Fahrtenbuch exportieren"))
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(500, 450)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(self.tr("Fahrtenbuch Export-Einstellungen"))
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Export format group
        format_group = QGroupBox(self.tr("Export-Format"))
        format_layout = QVBoxLayout(format_group)
        
        self.excel_radio = QCheckBox(self.tr("Excel (.xlsx)"))
        self.excel_radio.setChecked(True)
        format_layout.addWidget(self.excel_radio)
        
        self.pdf_radio = QCheckBox(self.tr("PDF (.pdf)"))
        format_layout.addWidget(self.pdf_radio)
        
        layout.addWidget(format_group)
        
        # Date range group
        date_group = QGroupBox(self.tr("Datumsbereich"))
        date_layout = QFormLayout(date_group)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        date_layout.addRow(self.tr("Von:"), self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addRow(self.tr("Bis:"), self.end_date)
        
        layout.addWidget(date_group)
        
        # Driver selection group
        driver_group = QGroupBox(self.tr("Fahrer-Auswahl"))
        driver_layout = QFormLayout(driver_group)
        
        self.driver_combo = QComboBox()
        self.driver_combo.addItem(self.tr("Alle Fahrer"), None)
        self.load_drivers()
        driver_layout.addRow(self.tr("Fahrer:"), self.driver_combo)
        
        layout.addWidget(driver_group)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.tr("Abbrechen"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.export_btn = QPushButton(self.tr("Exportieren"))
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.export_btn.clicked.connect(self.start_export)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
        
    def load_drivers(self):
        """Load drivers for the current company"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name FROM drivers 
                WHERE company_id = ? AND status = 'Active'
                ORDER BY name
            """, (self.company_id,))
            
            drivers = cursor.fetchall()
            
            for driver in drivers:
                self.driver_combo.addItem(driver['name'], driver['id'])
                
            conn.close()
            
        except Exception as e:
            QMessageBox.warning(self, self.tr("Warnung"), 
                              self.tr(f"Fehler beim Laden der Fahrer: {e}"))
            
    def start_export(self):
        """Start the export process"""
        
        # Validate inputs
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, self.tr("Ungültiger Datumsbereich"),
                              self.tr("Das Startdatum muss vor dem Enddatum liegen."))
            return
            
        if not self.excel_radio.isChecked() and not self.pdf_radio.isChecked():
            QMessageBox.warning(self, self.tr("Kein Format ausgewählt"),
                              self.tr("Bitte wählen Sie mindestens ein Export-Format aus."))
            return
            
        # Disable export button and show progress
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText(self.tr("Export wird vorbereitet..."))
        
        # Get selected values
        driver_id = self.driver_combo.currentData()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        # Start export workers
        self.export_workers = []
        
        if self.excel_radio.isChecked():
            worker = ExportWorker('fahrtenbuch_excel', self.company_id, driver_id, start_date, end_date)
            worker.finished.connect(self.on_export_finished)
            worker.progress.connect(self.on_export_progress)
            worker.error.connect(self.on_export_error)
            self.export_workers.append(worker)
            worker.start()
            
        if self.pdf_radio.isChecked():
            worker = ExportWorker('fahrtenbuch_pdf', self.company_id, driver_id, start_date, end_date)
            worker.finished.connect(self.on_export_finished)
            worker.progress.connect(self.on_export_progress)
            worker.error.connect(self.on_export_error)
            self.export_workers.append(worker)
            worker.start()
            
    def on_export_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        
    def on_export_finished(self, message):
        """Handle successful export completion"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
        # Check if all workers are finished
        if all(not worker.isRunning() for worker in self.export_workers):
            self.export_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
            # Show completion message
            QMessageBox.information(self, self.tr("Export abgeschlossen"),
                                  self.tr("Alle Exporte wurden erfolgreich erstellt."))
            
    def on_export_error(self, error_message):
        """Handle export error"""
        self.status_label.setText(error_message)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, self.tr("Export-Fehler"), error_message)

class ReportsView(QWidget):
    def __init__(self, parent=None, company_id=1):
        super().__init__(parent)
        self.parent_window = parent
        self.company_id = company_id
        self.current_quick_export_worker = None
        self.db_conn = get_db_connection() # For direct DB access if needed in this view
        self.exporter = FahrtenbuchExporter(company_id=self.company_id)
        self.tm = QCoreApplication.instance().property("translation_manager")
        
        # Initialize UI
        self.init_ui()
        
        # Load initial data
        self.refresh_data()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.tr("Berichte & Export"))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton(self.tr("Aktualisieren"))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
                border-radius: 5px;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d5dbdb;
            }
        """)
        
        # Add tabs
        self.create_fahrtenbuch_tab()
        self.create_stundenzettel_tab()
        self.create_analytics_tab()
        
        main_layout.addWidget(self.tab_widget)
        
    def create_fahrtenbuch_tab(self):
        """Create the Fahrtenbuch (logbook) export tab"""
        
        fahrtenbuch_widget = QWidget()
        layout = QVBoxLayout(fahrtenbuch_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title and description
        title = QLabel(self.tr("Fahrtenbuch Export"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        description = QLabel(self.tr("Exportieren Sie Fahrtenbücher in Excel- oder PDF-Format. "
                                   "Die Exporte entsprechen den deutschen gesetzlichen Anforderungen "
                                   "und enthalten alle erforderlichen Informationen."))
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(description)
        
        # Quick export buttons
        quick_export_group = QGroupBox(self.tr("Schnell-Export"))
        quick_layout = QGridLayout(quick_export_group)
        
        # Current month export
        current_month_btn = QPushButton(self.tr("Aktueller Monat (Excel)"))
        current_month_btn.setStyleSheet(self.get_button_style("#27ae60"))
        current_month_btn.clicked.connect(self.export_current_month_excel)
        quick_layout.addWidget(current_month_btn, 0, 0)
        
        # Last month export
        last_month_btn = QPushButton(self.tr("Letzter Monat (Excel)"))
        last_month_btn.setStyleSheet(self.get_button_style("#27ae60"))
        last_month_btn.clicked.connect(self.export_last_month_excel)
        quick_layout.addWidget(last_month_btn, 0, 1)
        
        # Current month PDF
        current_month_pdf_btn = QPushButton(self.tr("Aktueller Monat (PDF)"))
        current_month_pdf_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        current_month_pdf_btn.clicked.connect(self.export_current_month_pdf)
        quick_layout.addWidget(current_month_pdf_btn, 1, 0)
        
        # Last month PDF
        last_month_pdf_btn = QPushButton(self.tr("Letzter Monat (PDF)"))
        last_month_pdf_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        last_month_pdf_btn.clicked.connect(self.export_last_month_pdf)
        quick_layout.addWidget(last_month_pdf_btn, 1, 1)
        
        layout.addWidget(quick_export_group)
        
        # Custom export button
        custom_export_btn = QPushButton(self.tr("Erweiterte Export-Optionen"))
        custom_export_btn.setStyleSheet(self.get_button_style("#3498db"))
        custom_export_btn.clicked.connect(self.show_custom_export_dialog)
        layout.addWidget(custom_export_btn)
        
        # Statistics section
        stats_group = QGroupBox(self.tr("Statistiken"))
        stats_layout = QFormLayout(stats_group)
        
        self.total_rides_label = QLabel("0")
        stats_layout.addRow(self.tr("Gesamte Fahrten:"), self.total_rides_label)
        
        self.total_distance_label = QLabel("0 km")
        stats_layout.addRow(self.tr("Gesamtentfernung:"), self.total_distance_label)
        
        self.active_drivers_label = QLabel("0")
        stats_layout.addRow(self.tr("Aktive Fahrer:"), self.active_drivers_label)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(fahrtenbuch_widget, self.tr("Fahrtenbuch"))
        
    def create_stundenzettel_tab(self):
        """Create the Stundenzettel (timesheet) export tab"""
        
        stundenzettel_widget = QWidget()
        layout = QVBoxLayout(stundenzettel_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title = QLabel(self.tr("Stundenzettel Export"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        description = QLabel(self.tr("Exportieren Sie Stundenzettel für die Lohnabrechnung. "
                                   "Die Exporte enthalten alle Arbeitszeiten, Pausen und "
                                   "Zuschläge nach deutschen Arbeitsrechtsbestimmungen."))
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(description)
        
        # Coming soon placeholder
        coming_soon = QLabel(self.tr("Stundenzettel-Export wird in einer zukünftigen Version verfügbar sein."))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("color: #95a5a6; font-style: italic; font-size: 14px; padding: 50px;")
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        
        self.tab_widget.addTab(stundenzettel_widget, self.tr("Stundenzettel"))
        
    def create_analytics_tab(self):
        """Create the analytics and statistics tab"""
        
        analytics_widget = QWidget()
        main_layout = QVBoxLayout(analytics_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 1. Filter/Controls GroupBox
        controls_group = QGroupBox(self.tr("analyse_filter_title", "Filter & Optionen"))
        controls_layout = QHBoxLayout(controls_group) # Use QHBoxLayout for horizontal arrangement

        form_layout = QFormLayout() # For date selectors

        self.analytics_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day() + 1))
        self.analytics_start_date_edit.setCalendarPopup(True)
        self.analytics_start_date_edit.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow(self.tr("analyse_start_date", "Startdatum:"), self.analytics_start_date_edit)

        self.analytics_end_date_edit = QDateEdit(QDate.currentDate())
        self.analytics_end_date_edit.setCalendarPopup(True)
        self.analytics_end_date_edit.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow(self.tr("analyse_end_date", "Enddatum:"), self.analytics_end_date_edit)
        
        controls_layout.addLayout(form_layout)
        controls_layout.addStretch(1) # Add stretch to push button to the right

        self.refresh_analytics_button = QPushButton(self.tr("analyse_refresh_button", "Aktualisieren"))
        self.refresh_analytics_button.clicked.connect(self.refresh_analytics_charts)
        self.refresh_analytics_button.setStyleSheet(self.get_button_style("#007bff"))
        self.refresh_analytics_button.setFixedHeight(35) # Match date edit height
        controls_layout.addWidget(self.refresh_analytics_button)
        
        main_layout.addWidget(controls_group)
        
        # 2. Scroll Area for Charts
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }") # Cleaner look
        
        self.charts_container_widget = QWidget() # Widget to hold the grid of charts
        self.charts_layout = QGridLayout(self.charts_container_widget) # Grid layout for charts
        self.charts_layout.setSpacing(20) # Spacing between chart widgets

        # Placeholder: Initially add the KmPerDriverWidget
        # In a real scenario, you might load default charts or based on user prefs
        
        # Set initial dates for the first chart load
        initial_start_qdate = self.analytics_start_date_edit.date()
        initial_end_qdate = self.analytics_end_date_edit.date()

        self.km_per_driver_chart = KmPerDriverWidget(self.company_id, initial_start_qdate, initial_end_qdate)
        self.charts_layout.addWidget(self.km_per_driver_chart, 0, 0) # Add to grid row 0, col 0

        # Example: Add another placeholder chart widget if you had one
        # self.another_chart_widget = AnotherChartWidget(self.company_id, initial_start_qdate, initial_end_qdate)
        # self.charts_layout.addWidget(self.another_chart_widget, 0, 1) # Add to grid row 0, col 1
        
        # self.charts_layout.setRowStretch(1, 1) # Add stretch to push charts to top if few
        # self.charts_layout.setColumnStretch(2, 1)

        scroll_area.setWidget(self.charts_container_widget)
        main_layout.addWidget(scroll_area)

        return analytics_widget

    def refresh_analytics_charts(self):
        start_qdate = self.analytics_start_date_edit.date()
        end_qdate = self.analytics_end_date_edit.date()

        if start_qdate > end_qdate:
            QMessageBox.warning(self, self.tr("date_error_title", "Datumsfehler"), 
                                self.tr("date_error_message_start_after_end", "Das Startdatum darf nicht nach dem Enddatum liegen."))
            return

        # Update existing charts
        if hasattr(self, 'km_per_driver_chart') and self.km_per_driver_chart:
            self.km_per_driver_chart.update_chart_data(self.company_id, start_qdate, end_qdate)
        
        # If you add more charts, update them here as well
        # if hasattr(self, 'another_chart_widget') and self.another_chart_widget:
        #     self.another_chart_widget.update_chart_data(self.company_id, start_qdate, end_qdate)
        
        print(f"Analytics charts refreshed for company {self.company_id} from {start_qdate.toString()} to {end_qdate.toString()}")
        
    def get_button_style(self, color):
        """Get consistent button styling"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.8);
            }}
            QPushButton:pressed {{
                background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.6);
            }}
        """
        
    def export_current_month_excel(self):
        """Export current month to Excel"""
        start_date = QDate.currentDate().addDays(-QDate.currentDate().day() + 1)
        end_date = QDate.currentDate()
        self.run_quick_export('excel', start_date, end_date)
        
    def export_last_month_excel(self):
        """Export last month to Excel"""
        last_month = QDate.currentDate().addMonths(-1)
        start_date = QDate(last_month.year(), last_month.month(), 1)
        end_date = start_date.addMonths(1).addDays(-1)
        self.run_quick_export('excel', start_date, end_date)
        
    def export_current_month_pdf(self):
        """Export current month to PDF"""
        start_date = QDate.currentDate().addDays(-QDate.currentDate().day() + 1)
        end_date = QDate.currentDate()
        self.run_quick_export('pdf', start_date, end_date)
        
    def export_last_month_pdf(self):
        """Export last month to PDF"""
        last_month = QDate.currentDate().addMonths(-1)
        start_date = QDate(last_month.year(), last_month.month(), 1)
        end_date = start_date.addMonths(1).addDays(-1)
        self.run_quick_export('pdf', start_date, end_date)
        
    def run_quick_export(self, format_type, start_date, end_date):
        """Run a quick export with predefined settings"""
        
        export_type = f'fahrtenbuch_{format_type}'
        start_date_str = start_date.toString("yyyy-MM-dd")
        end_date_str = end_date.toString("yyyy-MM-dd")
        
        # Store worker as instance variable to prevent premature garbage collection
        self.current_quick_export_worker = ExportWorker(export_type, self.company_id, None, start_date_str, end_date_str)
        
        # Create and configure QProgressDialog
        progress_dialog = QProgressDialog(self.tr("Export wird erstellt..."), self.tr("Abbrechen"), 0, 100, self)
        progress_dialog.setWindowTitle(self.tr("Export läuft"))
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoClose(True) # Automatically close when progress reaches maximum
        progress_dialog.setAutoReset(True) # Reset when finished or cancelled

        # Connect worker signals to dialog and handlers
        self.current_quick_export_worker.progress.connect(progress_dialog.setValue)
        
        def on_finished(message):
            progress_dialog.setValue(100) # Ensure dialog shows completion
            QMessageBox.information(self, self.tr("Export abgeschlossen"), message)
            self.current_quick_export_worker = None # Clear reference
            
        def on_error(error_message):
            progress_dialog.cancel() # Close the progress dialog
            QMessageBox.critical(self, self.tr("Export-Fehler"), error_message)
            self.current_quick_export_worker = None # Clear reference
        
        # Connect cancel button of progress dialog to worker's terminate (if applicable) or a handler
        # For simplicity, we'll just allow it to cancel the dialog. 
        # Proper cancellation might require ExportWorker to have a terminate/cancel method.
        progress_dialog.canceled.connect(lambda: self.handle_export_cancellation(progress_dialog))

        self.current_quick_export_worker.finished.connect(on_finished)
        self.current_quick_export_worker.error.connect(on_error)
        self.current_quick_export_worker.start()
        progress_dialog.exec() # Show the dialog modally

    def handle_export_cancellation(self, progress_dialog):
        if self.current_quick_export_worker and self.current_quick_export_worker.isRunning():
            # Attempt to terminate the worker. Note: QThread.terminate() is discouraged.
            # A cooperative cancellation mechanism in ExportWorker would be better.
            # self.current_quick_export_worker.terminate() # Use with caution
            pass # For now, just let the dialog close. The worker might continue.
        QMessageBox.information(self, self.tr("Export abgebrochen"), self.tr("Der Exportvorgang wurde abgebrochen."))
        self.current_quick_export_worker = None # Clear reference
        if progress_dialog.isVisible():
            progress_dialog.cancel() # Ensure dialog is closed
        
    def show_custom_export_dialog(self):
        """Show the custom export configuration dialog"""
        dialog = FahrtenbuchExportDialog(self.company_id, self)
        dialog.exec()
        
    def refresh_data(self):
        """Refresh statistics and data"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get total rides
            cursor.execute("SELECT COUNT(*) as count FROM rides WHERE company_id = ?", (self.company_id,))
            total_rides = cursor.fetchone()['count']
            self.total_rides_label.setText(str(total_rides))
            
            # Get total distance
            cursor.execute("SELECT SUM(gefahrene_kilometer) as total FROM rides WHERE company_id = ? AND gefahrene_kilometer IS NOT NULL", (self.company_id,))
            result = cursor.fetchone()
            total_distance = result['total'] if result['total'] else 0
            self.total_distance_label.setText(f"{total_distance:.1f} km")
            
            # Get active drivers
            cursor.execute("SELECT COUNT(*) as count FROM drivers WHERE company_id = ? AND status = 'Active'", (self.company_id,))
            active_drivers = cursor.fetchone()['count']
            self.active_drivers_label.setText(str(active_drivers))
            
            conn.close()
            
        except Exception as e:
            print(f"Error refreshing data: {e}")
            
    def tr(self, source_text, disambiguation=None, n=-1):
        # Helper to use the global translator
        if self.tm:
            return self.tm.tr(source_text, disambiguation, n)
        return QCoreApplication.translate("ReportsView", source_text, disambiguation, n)

