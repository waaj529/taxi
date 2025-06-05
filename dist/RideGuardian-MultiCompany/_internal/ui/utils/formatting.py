"""
UI Formatting Utilities for German Localization
Handles date/time formatting, currency display, and measurement units
"""

from PyQt6.QtCore import QDateTime, QDate, QTime
from datetime import datetime
from typing import Union, Optional


class GermanFormatter:
    """Formatting utilities for German UI display"""
    
    @staticmethod
    def format_datetime(dt: Union[str, datetime, QDateTime], include_seconds: bool = False) -> str:
        """Format datetime in German 24-hour format"""
        if isinstance(dt, str):
            # Parse string datetime
            try:
                if 'T' in dt:
                    dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                else:
                    dt_obj = datetime.strptime(dt.split('.')[0], "%Y-%m-%d %H:%M:%S")
                
                if include_seconds:
                    return dt_obj.strftime("%d.%m.%Y %H:%M:%S")
                else:
                    return dt_obj.strftime("%d.%m.%Y %H:%M")
            except:
                return dt  # Return original if parsing fails
                
        elif isinstance(dt, datetime):
            if include_seconds:
                return dt.strftime("%d.%m.%Y %H:%M:%S")
            else:
                return dt.strftime("%d.%m.%Y %H:%M")
                
        elif isinstance(dt, QDateTime):
            if include_seconds:
                return dt.toString("dd.MM.yyyy HH:mm:ss")
            else:
                return dt.toString("dd.MM.yyyy HH:mm")
        
        return str(dt)
    
    @staticmethod
    def format_date(date: Union[str, datetime, QDate]) -> str:
        """Format date in German format"""
        if isinstance(date, str):
            try:
                if len(date) == 10:  # Assume YYYY-MM-DD format
                    dt_obj = datetime.strptime(date, "%Y-%m-%d")
                    return dt_obj.strftime("%d.%m.%Y")
                else:
                    # Try to extract date from datetime string
                    dt_obj = datetime.strptime(date.split()[0], "%Y-%m-%d")
                    return dt_obj.strftime("%d.%m.%Y")
            except:
                return date
                
        elif isinstance(date, datetime):
            return date.strftime("%d.%m.%Y")
            
        elif isinstance(date, QDate):
            return date.toString("dd.MM.yyyy")
        
        return str(date)
    
    @staticmethod
    def format_time(time: Union[str, datetime, QTime], include_seconds: bool = False) -> str:
        """Format time in German 24-hour format"""
        if isinstance(time, str):
            try:
                # Handle various time formats
                if ':' in time:
                    parts = time.split(':')
                    if len(parts) >= 2:
                        hour = int(parts[0])
                        minute = int(parts[1])
                        second = int(parts[2]) if len(parts) > 2 else 0
                        
                        if include_seconds:
                            return f"{hour:02d}:{minute:02d}:{second:02d}"
                        else:
                            return f"{hour:02d}:{minute:02d}"
                return time
            except:
                return time
                
        elif isinstance(time, datetime):
            if include_seconds:
                return time.strftime("%H:%M:%S")
            else:
                return time.strftime("%H:%M")
                
        elif isinstance(time, QTime):
            if include_seconds:
                return time.toString("HH:mm:ss")
            else:
                return time.toString("HH:mm")
        
        return str(time)
    
    @staticmethod
    def format_currency(amount: Union[float, int, str], symbol: str = "€") -> str:
        """Format currency in German format with Euro symbol"""
        try:
            # Convert to float if string
            if isinstance(amount, str):
                amount = float(amount.replace(',', '.'))
            
            # Format with German decimal separator
            formatted = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"{symbol} {formatted}"
        except:
            return f"{symbol} {amount}"
    
    @staticmethod
    def format_distance(distance: Union[float, int, str], unit: str = "km") -> str:
        """Format distance with German formatting"""
        try:
            if isinstance(distance, str):
                distance = float(distance.replace(',', '.'))
            
            # Format with one decimal place
            formatted = f"{distance:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"{formatted} {unit}"
        except:
            return f"{distance} {unit}"
    
    @staticmethod
    def format_percentage(value: Union[float, int, str]) -> str:
        """Format percentage with German formatting"""
        try:
            if isinstance(value, str):
                value = float(value.replace(',', '.'))
            
            formatted = f"{value:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"{formatted}%"
        except:
            return f"{value}%"
    
    @staticmethod
    def parse_german_date(date_str: str) -> Optional[datetime]:
        """Parse German date format to datetime"""
        try:
            return datetime.strptime(date_str, "%d.%m.%Y")
        except:
            try:
                return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            except:
                try:
                    return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
                except:
                    return None


# Convenience functions for quick access
def format_datetime(dt, include_seconds=False):
    return GermanFormatter.format_datetime(dt, include_seconds)

def format_date(date):
    return GermanFormatter.format_date(date)

def format_time(time, include_seconds=False):
    return GermanFormatter.format_time(time, include_seconds)

def format_currency(amount, symbol="€"):
    return GermanFormatter.format_currency(amount, symbol)

def format_distance(distance, unit="km"):
    return GermanFormatter.format_distance(distance, unit)

def format_percentage(value):
    return GermanFormatter.format_percentage(value) 