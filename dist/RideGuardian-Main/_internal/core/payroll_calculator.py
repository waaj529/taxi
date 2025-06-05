import sqlite3
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP
import calendar

class PayrollCalculator:
    """Erweiterte Lohnberechnungs-Engine mit Lohn-Compliance und Bonus-Logik"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def calculate_driver_payroll(self, driver_id: int, start_date: str, end_date: str) -> Dict:
        """
        Berechne umfassende Lohnabrechnung für einen Fahrer für den angegebenen Zeitraum
        Gibt detaillierte Lohnaufschlüsselung mit Compliance-Prüfungen zurück
        """
        # Fahrerinformationen abrufen
        driver_info = self._get_driver_info(driver_id)
        if not driver_info:
            raise ValueError(f"Fahrer {driver_id} nicht gefunden")
            
        # Regeln abrufen
        rules = self._get_payroll_rules()
        
        # Fahrten für den Zeitraum abrufen
        rides = self._get_rides_for_period(driver_id, start_date, end_date)
        
        # Grundarbeitszeiten berechnen
        work_hours = self._calculate_work_hours(rides, rules)
        
        # Grundlohn berechnen
        base_pay = self._calculate_base_pay(work_hours, rules)
        
        # Boni berechnen
        bonuses = self._calculate_bonuses(rides, work_hours, rules)
        
        # Gesamtlohn berechnen
        total_pay = base_pay + bonuses['total']
        
        # Mindestlohn-Compliance-Prüfung
        compliance = self._check_minimum_wage_compliance(
            work_hours, total_pay, rules, driver_id
        )
        
        # Lohndatensatz erstellen
        payroll_data = {
            'driver_id': driver_id,
            'driver_name': driver_info['name'],
            'period_start': start_date,
            'period_end': end_date,
            'total_rides': len(rides),
            'work_hours': {
                'regular_hours': work_hours['regular_hours'],
                'night_hours': work_hours['night_hours'],
                'weekend_hours': work_hours['weekend_hours'],
                'holiday_hours': work_hours['holiday_hours'],
                'total_hours': work_hours['total_hours']
            },
            'base_pay': round(base_pay, 2),
            'bonuses': {
                'night_bonus': round(bonuses['night'], 2),
                'weekend_bonus': round(bonuses['weekend'], 2),
                'holiday_bonus': round(bonuses['holiday'], 2),
                'performance_bonus': round(bonuses['performance'], 2),
                'total_bonuses': round(bonuses['total'], 2)
            },
            'total_pay': round(total_pay, 2),
            'compliance': compliance,
            'revenue_generated': sum(ride.get('revenue', 0) or 0 for ride in rides),
            'violation_count': len([r for r in rides if r.get('violations') and r['violations'] != '[]']),
            'compliance_rate': self._calculate_compliance_rate(rides)
        }
        
        # In Datenbank speichern
        self._save_payroll_record(payroll_data)
        
        return payroll_data
        
    def _get_driver_info(self, driver_id: int) -> Optional[Dict]:
        """Fahrerinformationen abrufen"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def _get_payroll_rules(self) -> Dict:
        """Lohnbezogene Regeln aus der Datenbank abrufen"""
        cursor = self.db.cursor()
        cursor.execute("SELECT rule_name, rule_value FROM rules WHERE enabled = 1")
        rules = {}
        
        for row in cursor.fetchall():
            try:
                # Versuche als Zahl zu parsen
                rules[row['rule_name']] = float(row['rule_value'])
            except ValueError:
                rules[row['rule_name']] = row['rule_value']
                
        # Standardwerte setzen
        defaults = {
            'minimum_wage_hourly': 12.41,
            'night_bonus_rate': 15.0,  # %
            'weekend_bonus_rate': 10.0,  # %
            'holiday_bonus_rate': 25.0,  # %
            'performance_bonus_threshold': 95.0,  # % Compliance-Rate
            'performance_bonus_rate': 5.0,  # %
            'night_start_hour': 22,
            'night_end_hour': 6,
            'break_duration_minutes': 30,
            'max_continuous_hours': 8,
            'overtime_threshold_hours': 40,
            'overtime_rate_multiplier': 1.5
        }
        
        for key, value in defaults.items():
            if key not in rules:
                rules[key] = value
                
        return rules
        
    def _get_rides_for_period(self, driver_id: int, start_date: str, end_date: str) -> List[Dict]:
        """Alle Fahrten für Fahrer im angegebenen Zeitraum abrufen"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? 
            AND DATE(pickup_time) BETWEEN ? AND ?
            AND status = 'Completed'
            ORDER BY pickup_time ASC
        """, (driver_id, start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
        
    def _calculate_work_hours(self, rides: List[Dict], rules: Dict) -> Dict:
        """Detaillierte Arbeitszeit-Aufschlüsselung berechnen"""
        if not rides:
            return {
                'regular_hours': 0, 'night_hours': 0, 'weekend_hours': 0, 
                'holiday_hours': 0, 'total_hours': 0, 'shifts': []
            }
            
        # Fahrten nach Tag gruppieren um Schichten zu berechnen
        daily_rides = {}
        for ride in rides:
            ride_date = datetime.fromisoformat(ride['pickup_time']).date()
            if ride_date not in daily_rides:
                daily_rides[ride_date] = []
            daily_rides[ride_date].append(ride)
            
        total_regular = 0
        total_night = 0
        total_weekend = 0
        total_holiday = 0
        shifts = []
        
        for date, day_rides in daily_rides.items():
            # Schichtbeginn und -ende berechnen
            shift_start = min(datetime.fromisoformat(r['pickup_time']) for r in day_rides)
            
            # Schichtende schätzen (letzte Abholung + geschätzte Fahrtdauer)
            last_ride_start = max(datetime.fromisoformat(r['pickup_time']) for r in day_rides)
            estimated_ride_duration = timedelta(hours=1)  # 1 Stunde pro Fahrt annehmen
            shift_end = last_ride_start + estimated_ride_duration
            
            # Schichtdauer berechnen
            shift_duration = (shift_end - shift_start).total_seconds() / 3600  # Stunden
            
            # Pflichtpausenzeit hinzufügen
            break_hours = rules.get('break_duration_minutes', 30) / 60
            if shift_duration > 6:  # Pause für Schichten länger als 6 Stunden hinzufügen
                shift_duration += break_hours
                
            # Stunden kategorisieren
            is_weekend = date.weekday() >= 5  # Samstag = 5, Sonntag = 6
            is_holiday = self._is_holiday(date)
            
            night_hours = self._calculate_night_hours(shift_start, shift_end, rules)
            regular_hours = shift_duration - night_hours
            
            if is_holiday:
                total_holiday += shift_duration
            elif is_weekend:
                total_weekend += shift_duration
            else:
                total_regular += regular_hours
                total_night += night_hours
                
            shifts.append({
                'date': date.isoformat(),
                'start_time': shift_start.isoformat(),
                'end_time': shift_end.isoformat(),
                'total_hours': round(shift_duration, 2),
                'night_hours': round(night_hours, 2),
                'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'rides_count': len(day_rides)
            })
            
        return {
            'regular_hours': round(total_regular, 2),
            'night_hours': round(total_night, 2),
            'weekend_hours': round(total_weekend, 2),
            'holiday_hours': round(total_holiday, 2),
            'total_hours': round(total_regular + total_night + total_weekend + total_holiday, 2),
            'shifts': shifts
        }
        
    def _calculate_night_hours(self, shift_start: datetime, shift_end: datetime, rules: Dict) -> float:
        """Während der Nachtzeit gearbeitete Stunden berechnen"""
        night_start_hour = int(rules.get('night_start_hour', 22))
        night_end_hour = int(rules.get('night_end_hour', 6))
        
        night_hours = 0
        current = shift_start
        
        while current < shift_end:
            hour = current.hour
            
            # Prüfen ob aktuelle Stunde Nachtzeit ist
            if hour >= night_start_hour or hour < night_end_hour:
                # Berechnen wie viel von dieser Stunde gearbeitet wurde
                next_hour = current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                hour_end = min(next_hour, shift_end)
                worked_minutes = (hour_end - current).total_seconds() / 60
                night_hours += worked_minutes / 60
                
            current = current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
        return night_hours
        
    def _is_holiday(self, date) -> bool:
        """Prüfen ob Datum ein Feiertag ist (vereinfacht - kann erweitert werden)"""
        # Dies ist eine vereinfachte Implementierung - Sie sollten eine ordentliche Feiertag-Bibliothek integrieren
        # oder eine Feiertage-Tabelle in der Datenbank verwalten
        holidays_2025 = [
            (1, 1),   # Neujahr
            (12, 25), # Weihnachten
            (12, 26), # 2. Weihnachtsfeiertag
            # Weitere Feiertage nach Bedarf hinzufügen
        ]
        
        return (date.month, date.day) in holidays_2025
        
    def _calculate_base_pay(self, work_hours: Dict, rules: Dict) -> float:
        """Grundlohn einschließlich Überstunden berechnen"""
        regular_rate = rules.get('minimum_wage_hourly', 12.41)
        overtime_threshold = rules.get('overtime_threshold_hours', 40)
        overtime_multiplier = rules.get('overtime_rate_multiplier', 1.5)
        
        total_hours = work_hours['total_hours']
        
        if total_hours <= overtime_threshold:
            return total_hours * regular_rate
        else:
            regular_pay = overtime_threshold * regular_rate
            overtime_hours = total_hours - overtime_threshold
            overtime_pay = overtime_hours * regular_rate * overtime_multiplier
            return regular_pay + overtime_pay
            
    def _calculate_bonuses(self, rides: List[Dict], work_hours: Dict, rules: Dict) -> Dict:
        """Alle Bonus-Arten berechnen"""
        base_hourly_rate = rules.get('minimum_wage_hourly', 12.41)
        
        # Nachtbonus
        night_rate = rules.get('night_bonus_rate', 15.0) / 100
        night_bonus = work_hours['night_hours'] * base_hourly_rate * night_rate
        
        # Wochenendbonus
        weekend_rate = rules.get('weekend_bonus_rate', 10.0) / 100
        weekend_bonus = work_hours['weekend_hours'] * base_hourly_rate * weekend_rate
        
        # Feiertagsbonus
        holiday_rate = rules.get('holiday_bonus_rate', 25.0) / 100
        holiday_bonus = work_hours['holiday_hours'] * base_hourly_rate * holiday_rate
        
        # Leistungsbonus
        compliance_rate = self._calculate_compliance_rate(rides)
        performance_threshold = rules.get('performance_bonus_threshold', 95.0)
        performance_rate = rules.get('performance_bonus_rate', 5.0) / 100
        
        performance_bonus = 0
        if compliance_rate >= performance_threshold:
            total_revenue = sum(ride.get('revenue', 0) or 0 for ride in rides)
            performance_bonus = total_revenue * performance_rate
            
        return {
            'night': night_bonus,
            'weekend': weekend_bonus,
            'holiday': holiday_bonus,
            'performance': performance_bonus,
            'total': night_bonus + weekend_bonus + holiday_bonus + performance_bonus
        }
        
    def _calculate_compliance_rate(self, rides: List[Dict]) -> float:
        """Compliance-Rate für Fahrten berechnen"""
        if not rides:
            return 100.0
            
        violation_count = 0
        for ride in rides:
            violations = ride.get('violations')
            if violations and violations not in ['[]', '', None]:
                violation_count += 1
                
        return ((len(rides) - violation_count) / len(rides)) * 100
        
    def _check_minimum_wage_compliance(self, work_hours: Dict, total_pay: float, 
                                     rules: Dict, driver_id: int) -> Dict:
        """Mindestlohn-Compliance einschließlich Boni prüfen"""
        minimum_wage = rules.get('minimum_wage_hourly', 12.41)
        total_hours = work_hours['total_hours']
        
        if total_hours == 0:
            return {
                'is_compliant': True,
                'required_minimum': 0,
                'actual_hourly': 0,
                'shortfall': 0,
                'warning': None
            }
            
        actual_hourly = total_pay / total_hours
        required_minimum = minimum_wage * total_hours
        shortfall = max(0, required_minimum - total_pay)
        
        is_compliant = shortfall == 0
        warning = None
        
        if not is_compliant:
            warning = (f"Mindestlohnverstoß: Fahrer {driver_id} verdiente "
                      f"{actual_hourly:.2f}€/Stunde ({total_pay:.2f}€ gesamt) "
                      f"aber Mindestlohn ist {minimum_wage:.2f}€/Stunde "
                      f"({required_minimum:.2f}€ gesamt). "
                      f"Fehlbetrag: {shortfall:.2f}€")
                      
        return {
            'is_compliant': is_compliant,
            'required_minimum': round(required_minimum, 2),
            'actual_hourly': round(actual_hourly, 2),
            'shortfall': round(shortfall, 2),
            'warning': warning
        }
        
    def _save_payroll_record(self, payroll_data: Dict) -> int:
        """Lohndatensatz in Datenbank speichern"""
        cursor = self.db.cursor()
        
        # Prüfen ob Datensatz bereits existiert
        cursor.execute("""
            SELECT id FROM payroll 
            WHERE driver_id = ? AND period_start_date = ? AND period_end_date = ?
        """, (payroll_data['driver_id'], payroll_data['period_start'], payroll_data['period_end']))
        
        existing = cursor.fetchone()
        
        compliance_status = "Konform" if payroll_data['compliance']['is_compliant'] else "Verstoß"
        
        if existing:
            # Vorhandenen Datensatz aktualisieren
            cursor.execute("""
                UPDATE payroll SET
                    hours = ?, base_pay = ?, bonuses = ?, total_pay = ?, 
                    compliance_status = ?
                WHERE id = ?
            """, (
                payroll_data['work_hours']['total_hours'],
                payroll_data['base_pay'],
                payroll_data['bonuses']['total_bonuses'],
                payroll_data['total_pay'],
                compliance_status,
                existing['id']
            ))
            payroll_id = existing['id']
        else:
            # Neuen Datensatz einfügen
            cursor.execute("""
                INSERT INTO payroll (
                    driver_id, period_start_date, period_end_date, 
                    hours, base_pay, bonuses, total_pay, compliance_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payroll_data['driver_id'],
                payroll_data['period_start'],
                payroll_data['period_end'],
                payroll_data['work_hours']['total_hours'],
                payroll_data['base_pay'],
                payroll_data['bonuses']['total_bonuses'],
                payroll_data['total_pay'],
                compliance_status
            ))
            payroll_id = cursor.lastrowid
            
        self.db.commit()
        return payroll_id
        
    def generate_payroll_report(self, driver_ids: List[int], start_date: str, end_date: str) -> Dict:
        """Umfassenden Lohnbericht für mehrere Fahrer generieren"""
        report = {
            'period': {'start': start_date, 'end': end_date},
            'drivers': [],
            'summary': {
                'total_drivers': len(driver_ids),
                'total_hours': 0,
                'total_pay': 0,
                'total_bonuses': 0,
                'compliance_issues': 0,
                'average_hourly': 0
            }
        }
        
        total_hours = 0
        total_pay = 0
        total_bonuses = 0
        compliance_issues = 0
        
        for driver_id in driver_ids:
            try:
                payroll_data = self.calculate_driver_payroll(driver_id, start_date, end_date)
                report['drivers'].append(payroll_data)
                
                total_hours += payroll_data['work_hours']['total_hours']
                total_pay += payroll_data['total_pay']
                total_bonuses += payroll_data['bonuses']['total_bonuses']
                
                if not payroll_data['compliance']['is_compliant']:
                    compliance_issues += 1
                    
            except Exception as e:
                print(f"Fehler bei der Lohnberechnung für Fahrer {driver_id}: {e}")
                
        report['summary'].update({
            'total_hours': round(total_hours, 2),
            'total_pay': round(total_pay, 2),
            'total_bonuses': round(total_bonuses, 2),
            'compliance_issues': compliance_issues,
            'average_hourly': round(total_pay / total_hours if total_hours > 0 else 0, 2)
        })
        
        return report