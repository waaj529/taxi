"""
Company Management System for Ride Guardian Desktop
Handles single-company and multi-company modes
"""

import os
import sys
from typing import List, Dict, Optional, Union
from datetime import datetime

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(PROJECT_ROOT)

from core.database import get_db_connection, get_company_config, set_company_config
from core.translation_manager import TranslationManager

class CompanyManager:
    """Manages company operations and modes for the application"""
    
    SINGLE_COMPANY_MODE = 'single'
    MULTI_COMPANY_MODE = 'multi'
    
    def __init__(self):
        self.tm = TranslationManager()
        self.current_company_id = 1
        self.app_mode = self.SINGLE_COMPANY_MODE
        self._companies_cache = None
        
    def initialize_app_mode(self) -> str:
        """Initialize and return the application mode"""
        try:
            # Check if mode is already configured
            stored_mode = get_company_config(1, 'app_mode')
            
            if stored_mode is None:
                # First time setup - default to single company mode
                self.app_mode = self.SINGLE_COMPANY_MODE
                self.save_app_mode(self.app_mode)
                
                # Ensure default company exists
                self.ensure_default_company()
            else:
                self.app_mode = stored_mode
                
            return self.app_mode
            
        except Exception as e:
            print(f"Error initializing app mode: {e}")
            self.app_mode = self.SINGLE_COMPANY_MODE
            return self.app_mode
    
    def save_app_mode(self, mode: str):
        """Save the application mode to database"""
        try:
            self.app_mode = mode
            set_company_config(1, 'app_mode', mode)
        except Exception as e:
            print(f"Error saving app mode: {e}")
    
    def is_single_company_mode(self) -> bool:
        """Check if application is in single company mode"""
        return self.app_mode == self.SINGLE_COMPANY_MODE
    
    def is_multi_company_mode(self) -> bool:
        """Check if application is in multi company mode"""
        return self.app_mode == self.MULTI_COMPANY_MODE
    
    def get_companies(self) -> List[Dict]:
        """Get list of all active companies"""
        if self._companies_cache is None:
            self._load_companies()
        return self._companies_cache or []
    
    def _load_companies(self):
        """Load companies from database"""
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT id, name, headquarters_address, phone, email, is_active
                FROM companies 
                WHERE is_active = 1
                ORDER BY name
            """)
            
            self._companies_cache = cursor.fetchall()
            db.close()
            
        except Exception as e:
            print(f"Error loading companies: {e}")
            self._companies_cache = []
    
    def get_current_company(self) -> Optional[Dict]:
        """Get current active company"""
        companies = self.get_companies()
        return next((c for c in companies if c['id'] == self.current_company_id), None)
    
    def set_current_company(self, company_id: int):
        """Set the current active company"""
        self.current_company_id = company_id
    
    def ensure_default_company(self):
        """Ensure a default company exists for single company mode"""
        try:
            companies = self.get_companies()
            if not companies:
                self.create_default_company()
                self._companies_cache = None  # Clear cache
                
        except Exception as e:
            print(f"Error ensuring default company: {e}")
    
    def create_default_company(self):
        """Create a default company for single company mode"""
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO companies (id, name, headquarters_address, phone, email, is_active)
                VALUES (1, ?, ?, ?, ?, 1)
            """, (
                "Mein Unternehmen",
                "Hauptstraße 1, 12345 Musterstadt",
                "+49 123 456789",
                "info@meinunternehmen.de"
            ))
            
            db.commit()
            db.close()
            
        except Exception as e:
            print(f"Error creating default company: {e}")
    
    def add_company(self, name: str, address: str = "", phone: str = "", email: str = "") -> bool:
        """Add a new company"""
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            cursor.execute("""
                INSERT INTO companies (name, headquarters_address, phone, email, is_active, created_date)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """, (name, address, phone, email))
            
            db.commit()
            db.close()
            
            # Clear cache to reload companies
            self._companies_cache = None
            return True
            
        except Exception as e:
            print(f"Error adding company: {e}")
            return False
    
    def update_company(self, company_id: int, name: str, address: str = "", phone: str = "", email: str = "") -> bool:
        """Update an existing company"""
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            cursor.execute("""
                UPDATE companies 
                SET name = ?, headquarters_address = ?, phone = ?, email = ?
                WHERE id = ?
            """, (name, address, phone, email, company_id))
            
            db.commit()
            db.close()
            
            # Clear cache to reload companies
            self._companies_cache = None
            return True
            
        except Exception as e:
            print(f"Error updating company: {e}")
            return False
    
    def delete_company(self, company_id: int) -> bool:
        """Soft delete a company (mark as inactive)"""
        if company_id == 1:
            # Never delete the default company
            return False
            
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            # Check if company has associated data
            cursor.execute("SELECT COUNT(*) as count FROM rides WHERE company_id = ?", (company_id,))
            ride_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM drivers WHERE company_id = ?", (company_id,))
            driver_count = cursor.fetchone()['count']
            
            if ride_count > 0 or driver_count > 0:
                # Company has data, just mark as inactive
                cursor.execute("""
                    UPDATE companies SET is_active = 0 WHERE id = ?
                """, (company_id,))
            else:
                # No data, safe to delete
                cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
            
            db.commit()
            db.close()
            
            # Clear cache to reload companies
            self._companies_cache = None
            return True
            
        except Exception as e:
            print(f"Error deleting company: {e}")
            return False
    
    def get_company_statistics(self, company_id: int) -> Dict:
        """Get statistics for a specific company"""
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            # Get ride count
            cursor.execute("SELECT COUNT(*) as count FROM rides WHERE company_id = ?", (company_id,))
            ride_count = cursor.fetchone()['count']
            
            # Get driver count
            cursor.execute("SELECT COUNT(*) as count FROM drivers WHERE company_id = ? AND status = 'Active'", (company_id,))
            driver_count = cursor.fetchone()['count']
            
            # Get total revenue for current month
            cursor.execute("""
                SELECT SUM(revenue) as total_revenue 
                FROM rides 
                WHERE company_id = ? 
                AND strftime('%Y-%m', pickup_time) = strftime('%Y-%m', 'now')
                AND status = 'Completed'
            """, (company_id,))
            result = cursor.fetchone()
            monthly_revenue = result['total_revenue'] or 0
            
            # Get vehicle count
            cursor.execute("SELECT COUNT(*) as count FROM vehicles WHERE company_id = ?", (company_id,))
            vehicle_count = cursor.fetchone()['count']
            
            db.close()
            
            return {
                'ride_count': ride_count,
                'driver_count': driver_count,
                'monthly_revenue': monthly_revenue,
                'vehicle_count': vehicle_count
            }
            
        except Exception as e:
            print(f"Error getting company statistics: {e}")
            return {
                'ride_count': 0,
                'driver_count': 0,
                'monthly_revenue': 0,
                'vehicle_count': 0
            }

# Global company manager instance
company_manager = CompanyManager()