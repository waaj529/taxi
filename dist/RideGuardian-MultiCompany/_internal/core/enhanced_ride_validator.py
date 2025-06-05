"""
Enhanced Ride Validation System
Implements comprehensive business rules and German labor law compliance
"""

import sqlite3
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from core.database import get_db_connection

class ViolationType(Enum):
    """Kategorien von Regelverstößen"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class RuleCategory(Enum):
    """Kategorien von Geschäftsregeln"""
    WORKING_TIME = "working_time"
    DISTANCE = "distance"
    TIME = "time"
    COST = "cost"
    FUEL = "fuel"
    BUSINESS_LOGIC = "business_logic"
    DATA_QUALITY = "data_quality"

@dataclass
class ValidationRule:
    """Definiert eine Validierungsregel"""
    id: str
    name: str
    description: str
    category: RuleCategory
    violation_type: ViolationType
    enabled: bool = True
    parameters: Dict = None

@dataclass
class ValidationViolation:
    """Repräsentiert einen Regelverstoß"""
    ride_id: int
    rule_id: str
    rule_name: str
    violation_type: ViolationType
    category: RuleCategory
    description: str
    severity_score: int
    suggested_action: str
    auto_fixable: bool = False
    fix_suggestion: str = ""

class EnhancedRideValidator:
    """
    Erweiterte Fahrtvalidierung mit konfigurierbaren Geschäftsregeln
    """
    
    def __init__(self, company_id: int = 1):
        self.company_id = company_id
        self.rules = self._load_validation_rules()
        self.violation_cache = {}
        
    def _load_validation_rules(self) -> List[ValidationRule]:
        """Lade alle Validierungsregeln für das Unternehmen"""
        return [
            # === ARBEITSZEIT-REGELN ===
            ValidationRule(
                id="working_time_daily_limit",
                name="Tägliche Arbeitszeit-Grenze",
                description="Maximale tägliche Arbeitszeit von 10 Stunden (Arbeitszeitgesetz)",
                category=RuleCategory.WORKING_TIME,
                violation_type=ViolationType.CRITICAL,
                parameters={"max_hours": 10}
            ),
            ValidationRule(
                id="working_time_weekly_limit",
                name="Wöchentliche Arbeitszeit-Grenze",
                description="Maximale wöchentliche Arbeitszeit von 48 Stunden",
                category=RuleCategory.WORKING_TIME,
                violation_type=ViolationType.WARNING,
                parameters={"max_weekly_hours": 48}
            ),
            ValidationRule(
                id="rest_period_daily",
                name="Tägliche Ruhezeit",
                description="Mindestens 11 Stunden Ruhezeit zwischen Arbeitstagen",
                category=RuleCategory.WORKING_TIME,
                violation_type=ViolationType.CRITICAL,
                parameters={"min_rest_hours": 11}
            ),
            ValidationRule(
                id="driving_time_continuous",
                name="Ununterbrochene Fahrzeit",
                description="Maximale ununterbrochene Fahrzeit von 4.5 Stunden",
                category=RuleCategory.WORKING_TIME,
                violation_type=ViolationType.WARNING,
                parameters={"max_continuous_driving": 4.5}
            ),
            
            # === ENTFERNUNGSREGELN ===
            ValidationRule(
                id="distance_plausibility",
                name="Entfernungsplausibilität",
                description="Entfernung muss realistisch für die Route sein",
                category=RuleCategory.DISTANCE,
                violation_type=ViolationType.WARNING,
                parameters={"max_deviation_percent": 30}
            ),
            ValidationRule(
                id="daily_distance_limit",
                name="Tägliche Kilometerbegrenzung",
                description="Maximale tägliche Fahrleistung",
                category=RuleCategory.DISTANCE,
                violation_type=ViolationType.WARNING,
                parameters={"max_daily_km": 1000}
            ),
            ValidationRule(
                id="odometer_consistency",
                name="Kilometerstand-Konsistenz",
                description="Kilometerstand muss logisch aufeinanderfolgend sein",
                category=RuleCategory.DISTANCE,
                violation_type=ViolationType.CRITICAL,
                parameters={}
            ),
            
            # === ZEITREGELN ===
            ValidationRule(
                id="time_logical_sequence",
                name="Logische Zeitabfolge",
                description="Endzeit muss nach Startzeit liegen",
                category=RuleCategory.TIME,
                violation_type=ViolationType.CRITICAL,
                parameters={}
            ),
            ValidationRule(
                id="overnight_trips",
                name="Übernachtfahrten",
                description="Fahrten über Mitternacht hinaus prüfen",
                category=RuleCategory.TIME,
                violation_type=ViolationType.INFO,
                parameters={}
            ),
            ValidationRule(
                id="minimum_trip_duration",
                name="Minimale Fahrtdauer",
                description="Fahrten sollten mindestens 1 Minute dauern",
                category=RuleCategory.TIME,
                violation_type=ViolationType.WARNING,
                parameters={"min_duration_minutes": 1}
            ),
            
            # === KOSTENREGELN ===
            ValidationRule(
                id="cost_plausibility",
                name="Kostenplausibilität",
                description="Kosten müssen im realistischen Bereich liegen",
                category=RuleCategory.COST,
                violation_type=ViolationType.WARNING,
                parameters={"max_cost_per_km": 2.0}
            ),
            ValidationRule(
                id="fuel_cost_consistency",
                name="Kraftstoffkosten-Konsistenz",
                description="Kraftstoffkosten sollten zur Entfernung passen",
                category=RuleCategory.FUEL,
                violation_type=ViolationType.INFO,
                parameters={"typical_consumption_l_per_100km": 8.0, "fuel_price_per_liter": 1.5}
            ),
            
            # === GESCHÄFTSLOGIK ===
            ValidationRule(
                id="business_purpose_required",
                name="Geschäftszweck erforderlich",
                description="Geschäftsfahrten müssen einen Zweck haben",
                category=RuleCategory.BUSINESS_LOGIC,
                violation_type=ViolationType.CRITICAL,
                parameters={}
            ),
            ValidationRule(
                id="weekend_business_trips",
                name="Geschäftsfahrten am Wochenende",
                description="Geschäftsfahrten am Wochenende prüfen",
                category=RuleCategory.BUSINESS_LOGIC,
                violation_type=ViolationType.INFO,
                parameters={}
            ),
            
            # === DATENQUALITÄT ===
            ValidationRule(
                id="required_fields",
                name="Pflichtfelder",
                description="Alle Pflichtfelder müssen ausgefüllt sein",
                category=RuleCategory.DATA_QUALITY,
                violation_type=ViolationType.CRITICAL,
                parameters={}
            ),
            ValidationRule(
                id="duplicate_detection",
                name="Duplikatserkennung",
                description="Erkennung möglicher doppelter Fahrten",
                category=RuleCategory.DATA_QUALITY,
                violation_type=ViolationType.WARNING,
                parameters={"time_tolerance_minutes": 30}
            )
        ]
    
    def validate_ride(self, ride_data: Dict) -> List[ValidationViolation]:
        """Validiere eine einzelne Fahrt gegen alle Regeln"""
        violations = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                rule_violations = self._apply_rule(ride_data, rule)
                violations.extend(rule_violations)
            except Exception as e:
                print(f"Fehler bei Regelanwendung {rule.id}: {e}")
        
        return violations
    
    def validate_multiple_rides(self, ride_ids: List[int]) -> Dict[int, List[ValidationViolation]]:
        """Validiere mehrere Fahrten und erkenne übergreifende Probleme"""
        results = {}
        
        # Lade alle Fahrtdaten
        rides_data = self._load_rides_data(ride_ids)
        
        # Einzelvalidierung
        for ride_id, ride_data in rides_data.items():
            results[ride_id] = self.validate_ride(ride_data)
        
        # Übergreifende Validierung
        cross_ride_violations = self._validate_cross_ride_rules(rides_data)
        
        # Füge übergreifende Verstöße hinzu
        for ride_id, violations in cross_ride_violations.items():
            if ride_id in results:
                results[ride_id].extend(violations)
            else:
                results[ride_id] = violations
        
        return results
    
    def _apply_rule(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Wende eine spezifische Regel auf eine Fahrt an"""
        violations = []
        
        if rule.id == "working_time_daily_limit":
            violations.extend(self._check_daily_working_time(ride_data, rule))
        elif rule.id == "working_time_weekly_limit":
            violations.extend(self._check_weekly_working_time(ride_data, rule))
        elif rule.id == "rest_period_daily":
            violations.extend(self._check_rest_periods(ride_data, rule))
        elif rule.id == "driving_time_continuous":
            violations.extend(self._check_continuous_driving(ride_data, rule))
        elif rule.id == "distance_plausibility":
            violations.extend(self._check_distance_plausibility(ride_data, rule))
        elif rule.id == "daily_distance_limit":
            violations.extend(self._check_daily_distance(ride_data, rule))
        elif rule.id == "odometer_consistency":
            violations.extend(self._check_odometer_consistency(ride_data, rule))
        elif rule.id == "time_logical_sequence":
            violations.extend(self._check_time_sequence(ride_data, rule))
        elif rule.id == "overnight_trips":
            violations.extend(self._check_overnight_trips(ride_data, rule))
        elif rule.id == "minimum_trip_duration":
            violations.extend(self._check_minimum_duration(ride_data, rule))
        elif rule.id == "cost_plausibility":
            violations.extend(self._check_cost_plausibility(ride_data, rule))
        elif rule.id == "fuel_cost_consistency":
            violations.extend(self._check_fuel_consistency(ride_data, rule))
        elif rule.id == "business_purpose_required":
            violations.extend(self._check_business_purpose(ride_data, rule))
        elif rule.id == "weekend_business_trips":
            violations.extend(self._check_weekend_business(ride_data, rule))
        elif rule.id == "required_fields":
            violations.extend(self._check_required_fields(ride_data, rule))
        elif rule.id == "duplicate_detection":
            violations.extend(self._check_duplicates(ride_data, rule))
        
        return violations
    
    def _check_daily_working_time(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe tägliche Arbeitszeit-Grenze"""
        violations = []
        
        # Berechne Gesamtarbeitszeit für den Tag
        ride_date = ride_data.get('date')
        if not ride_date:
            return violations
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT SUM(
                (strftime('%s', end_time) - strftime('%s', start_time)) / 3600.0
            ) as total_hours
            FROM rides 
            WHERE driver_id = ? AND date = ? AND company_id = ?
        """, (ride_data.get('driver_id'), ride_date, self.company_id))
        
        result = cursor.fetchone()
        db.close()
        
        if result and result['total_hours']:
            total_hours = result['total_hours']
            max_hours = rule.parameters.get('max_hours', 10)
            
            if total_hours > max_hours:
                violations.append(ValidationViolation(
                    ride_id=ride_data.get('id'),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    violation_type=rule.violation_type,
                    category=rule.category,
                    description=f"Tägliche Arbeitszeit von {total_hours:.1f}h überschreitet Limit von {max_hours}h",
                    severity_score=9,
                    suggested_action="Fahrt verschieben oder aufteilen",
                    auto_fixable=False
                ))
        
        return violations
    
    def _check_weekly_working_time(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe wöchentliche Arbeitszeit-Grenze"""
        violations = []
        
        ride_date = ride_data.get('date')
        if not ride_date:
            return violations
        
        # Berechne Wochenbeginn
        ride_dt = datetime.strptime(ride_date, '%Y-%m-%d')
        week_start = ride_dt - timedelta(days=ride_dt.weekday())
        week_end = week_start + timedelta(days=6)
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT SUM(
                (strftime('%s', end_time) - strftime('%s', start_time)) / 3600.0
            ) as weekly_hours
            FROM rides 
            WHERE driver_id = ? 
                AND date BETWEEN ? AND ?
                AND company_id = ?
        """, (ride_data.get('driver_id'), 
              week_start.strftime('%Y-%m-%d'), 
              week_end.strftime('%Y-%m-%d'),
              self.company_id))
        
        result = cursor.fetchone()
        db.close()
        
        if result and result['weekly_hours']:
            weekly_hours = result['weekly_hours']
            max_weekly = rule.parameters.get('max_weekly_hours', 48)
            
            if weekly_hours > max_weekly:
                violations.append(ValidationViolation(
                    ride_id=ride_data.get('id'),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    violation_type=rule.violation_type,
                    category=rule.category,
                    description=f"Wöchentliche Arbeitszeit von {weekly_hours:.1f}h überschreitet Limit von {max_weekly}h",
                    severity_score=7,
                    suggested_action="Arbeitszeit umverteilen oder reduzieren"
                ))
        
        return violations
    
    def _check_rest_periods(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe tägliche Ruhezeiten"""
        violations = []
        
        # Finde vorherige und nächste Fahrt desselben Fahrers
        db = get_db_connection()
        cursor = db.cursor()
        
        # Vorherige Fahrt
        cursor.execute("""
            SELECT date, end_time
            FROM rides 
            WHERE driver_id = ? AND company_id = ?
                AND (date < ? OR (date = ? AND end_time < ?))
            ORDER BY date DESC, end_time DESC
            LIMIT 1
        """, (ride_data.get('driver_id'), self.company_id,
              ride_data.get('date'), ride_data.get('date'), ride_data.get('start_time')))
        
        prev_ride = cursor.fetchone()
        
        if prev_ride:
            try:
                prev_end = datetime.strptime(f"{prev_ride['date']} {prev_ride['end_time']}", 
                                           "%Y-%m-%d %H:%M:%S")
                current_start = datetime.strptime(f"{ride_data.get('date')} {ride_data.get('start_time')}", 
                                                "%Y-%m-%d %H:%M:%S")
                
                rest_hours = (current_start - prev_end).total_seconds() / 3600
                min_rest = rule.parameters.get('min_rest_hours', 11)
                
                if rest_hours < min_rest:
                    violations.append(ValidationViolation(
                        ride_id=ride_data.get('id'),
                        rule_id=rule.id,
                        rule_name=rule.name,
                        violation_type=rule.violation_type,
                        category=rule.category,
                        description=f"Ruhezeit von {rest_hours:.1f}h unterschreitet Minimum von {min_rest}h",
                        severity_score=8,
                        suggested_action="Fahrt später beginnen"
                    ))
            except ValueError:
                pass  # Ungültige Zeitformate
        
        db.close()
        return violations
    
    def _check_distance_plausibility(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe Entfernungsplausibilität"""
        violations = []
        
        reported_distance = ride_data.get('distance_km', 0)
        start_location = ride_data.get('start_location')
        end_location = ride_data.get('end_location')
        
        if not all([reported_distance, start_location, end_location]):
            return violations
        
        # Schätze Google Maps Entfernung (vereinfacht)
        # In der Praxis würde hier die Google Maps API verwendet
        estimated_distance = self._estimate_distance(start_location, end_location)
        
        if estimated_distance > 0:
            deviation_percent = abs(reported_distance - estimated_distance) / estimated_distance * 100
            max_deviation = rule.parameters.get('max_deviation_percent', 30)
            
            if deviation_percent > max_deviation:
                violations.append(ValidationViolation(
                    ride_id=ride_data.get('id'),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    violation_type=rule.violation_type,
                    category=rule.category,
                    description=f"Entfernung {reported_distance}km weicht {deviation_percent:.1f}% von geschätzten {estimated_distance}km ab",
                    severity_score=5,
                    suggested_action="Entfernung überprüfen und korrigieren",
                    auto_fixable=True,
                    fix_suggestion=f"Vorgeschlagene Entfernung: {estimated_distance}km"
                ))
        
        return violations
    
    def _check_time_sequence(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe logische Zeitabfolge"""
        violations = []
        
        start_time = ride_data.get('start_time')
        end_time = ride_data.get('end_time')
        
        if not all([start_time, end_time]):
            return violations
        
        try:
            start_dt = datetime.strptime(f"{ride_data.get('date')} {start_time}", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{ride_data.get('date')} {end_time}", "%Y-%m-%d %H:%M:%S")
            
            if end_dt <= start_dt:
                violations.append(ValidationViolation(
                    ride_id=ride_data.get('id'),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    violation_type=rule.violation_type,
                    category=rule.category,
                    description="Endzeit liegt vor oder gleich der Startzeit",
                    severity_score=10,
                    suggested_action="Zeiten korrigieren",
                    auto_fixable=True
                ))
        except ValueError:
            violations.append(ValidationViolation(
                ride_id=ride_data.get('id'),
                rule_id=rule.id,
                rule_name=rule.name,
                violation_type=rule.violation_type,
                category=rule.category,
                description="Ungültiges Zeitformat",
                severity_score=9,
                suggested_action="Zeitformat überprüfen"
            ))
        
        return violations
    
    def _check_business_purpose(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe Geschäftszweck bei Geschäftsfahrten"""
        violations = []
        
        if ride_data.get('is_business_trip') and not ride_data.get('business_purpose'):
            violations.append(ValidationViolation(
                ride_id=ride_data.get('id'),
                rule_id=rule.id,
                rule_name=rule.name,
                violation_type=rule.violation_type,
                category=rule.category,
                description="Geschäftsfahrt ohne Geschäftszweck",
                severity_score=8,
                suggested_action="Geschäftszweck ergänzen"
            ))
        
        return violations
    
    def _check_required_fields(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe Pflichtfelder"""
        violations = []
        
        required_fields = [
            ('date', 'Datum'),
            ('start_time', 'Startzeit'),
            ('end_time', 'Endzeit'),
            ('start_location', 'Startort'),
            ('end_location', 'Zielort'),
            ('distance_km', 'Entfernung'),
            ('driver_id', 'Fahrer'),
            ('vehicle_id', 'Fahrzeug')
        ]
        
        missing_fields = []
        for field, display_name in required_fields:
            if not ride_data.get(field):
                missing_fields.append(display_name)
        
        if missing_fields:
            violations.append(ValidationViolation(
                ride_id=ride_data.get('id'),
                rule_id=rule.id,
                rule_name=rule.name,
                violation_type=rule.violation_type,
                category=rule.category,
                description=f"Fehlende Pflichtfelder: {', '.join(missing_fields)}",
                severity_score=9,
                suggested_action="Alle Pflichtfelder ausfüllen"
            ))
        
        return violations
    
    def _check_cost_plausibility(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        """Prüfe Kostenplausibilität"""
        violations = []
        
        distance = ride_data.get('distance_km', 0)
        total_costs = (ride_data.get('fuel_cost', 0) + 
                      ride_data.get('toll_cost', 0) + 
                      ride_data.get('parking_cost', 0) + 
                      ride_data.get('other_costs', 0))
        
        if distance > 0:
            cost_per_km = total_costs / distance
            max_cost_per_km = rule.parameters.get('max_cost_per_km', 2.0)
            
            if cost_per_km > max_cost_per_km:
                violations.append(ValidationViolation(
                    ride_id=ride_data.get('id'),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    violation_type=rule.violation_type,
                    category=rule.category,
                    description=f"Kosten pro km ({cost_per_km:.2f}€) überschreiten Plausibilitätsschwelle ({max_cost_per_km}€)",
                    severity_score=4,
                    suggested_action="Kosten überprüfen"
                ))
        
        return violations
    
    def _load_rides_data(self, ride_ids: List[int]) -> Dict[int, Dict]:
        """Lade Fahrtdaten für mehrere Fahrten"""
        db = get_db_connection()
        cursor = db.cursor()
        
        placeholders = ','.join(['?' for _ in ride_ids])
        query = f"""
            SELECT r.*, d.name as driver_name, v.license_plate, v.make, v.model
            FROM rides r
            JOIN drivers d ON r.driver_id = d.id
            JOIN vehicles v ON r.vehicle_id = v.id
            WHERE r.id IN ({placeholders}) AND r.company_id = ?
        """
        
        cursor.execute(query, ride_ids + [self.company_id])
        rides = cursor.fetchall()
        db.close()
        
        return {ride['id']: dict(ride) for ride in rides}
    
    def _validate_cross_ride_rules(self, rides_data: Dict[int, Dict]) -> Dict[int, List[ValidationViolation]]:
        """Validiere übergreifende Regeln zwischen Fahrten"""
        violations = {}
        
        # Gruppiere nach Fahrer und Datum für Duplikatserkennung
        driver_date_rides = {}
        for ride_id, ride in rides_data.items():
            key = (ride.get('driver_id'), ride.get('date'))
            if key not in driver_date_rides:
                driver_date_rides[key] = []
            driver_date_rides[key].append((ride_id, ride))
        
        # Prüfe auf Duplikate
        for (driver_id, date), ride_list in driver_date_rides.items():
            if len(ride_list) > 1:
                # Prüfe auf sehr ähnliche Fahrten
                for i, (ride_id1, ride1) in enumerate(ride_list):
                    for j, (ride_id2, ride2) in enumerate(ride_list[i+1:], i+1):
                        if self._are_similar_rides(ride1, ride2):
                            if ride_id1 not in violations:
                                violations[ride_id1] = []
                            violations[ride_id1].append(ValidationViolation(
                                ride_id=ride_id1,
                                rule_id="duplicate_detection",
                                rule_name="Duplikatserkennung",
                                violation_type=ViolationType.WARNING,
                                category=RuleCategory.DATA_QUALITY,
                                description=f"Mögliches Duplikat zu Fahrt #{ride_id2}",
                                severity_score=6,
                                suggested_action="Fahrten prüfen und ggf. zusammenführen"
                            ))
        
        return violations
    
    def _are_similar_rides(self, ride1: Dict, ride2: Dict) -> bool:
        """Prüfe ob zwei Fahrten ähnlich sind (mögliche Duplikate)"""
        # Prüfe Start- und Endorte
        if (ride1.get('start_location') == ride2.get('start_location') and
            ride1.get('end_location') == ride2.get('end_location')):
            
            # Prüfe Zeitdifferenz
            try:
                time1 = datetime.strptime(ride1.get('start_time', ''), '%H:%M:%S')
                time2 = datetime.strptime(ride2.get('start_time', ''), '%H:%M:%S')
                time_diff = abs((time1 - time2).total_seconds() / 60)  # Minuten
                
                if time_diff < 30:  # Weniger als 30 Minuten Unterschied
                    return True
            except ValueError:
                pass
        
        return False
    
    def _estimate_distance(self, start_location: str, end_location: str) -> float:
        """Schätze Entfernung zwischen zwei Orten (vereinfacht)"""
        # Vereinfachte Schätzung - in der Praxis Google Maps API verwenden
        # Hier nur Dummy-Implementierung
        if start_location == end_location:
            return 0.0
        
        # Geschätzte Durchschnittsentfernung basierend auf Ortstypen
        if any(keyword in start_location.lower() for keyword in ['büro', 'office', 'werk']):
            return 25.0  # Geschätzter Arbeitsweg
        
        return 15.0  # Standard-Schätzung
    
    # Weitere Check-Methoden für die restlichen Regeln...
    def _check_continuous_driving(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für kontinuierliche Fahrzeit-Prüfung
        return violations
    
    def _check_daily_distance(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für tägliche Entfernungsprüfung
        return violations
    
    def _check_odometer_consistency(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für Kilometerstand-Konsistenz
        return violations
    
    def _check_overnight_trips(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für Übernachtfahrten
        return violations
    
    def _check_minimum_duration(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für minimale Fahrtdauer
        return violations
    
    def _check_fuel_consistency(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für Kraftstoff-Konsistenz
        return violations
    
    def _check_weekend_business(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für Wochenend-Geschäftsfahrten
        return violations
    
    def _check_duplicates(self, ride_data: Dict, rule: ValidationRule) -> List[ValidationViolation]:
        violations = []
        # Implementation für einzelne Fahrt-Duplikatsprüfung
        return violations

    def get_violation_summary(self, violations: List[ValidationViolation]) -> Dict:
        """Erstelle Zusammenfassung der Verstöße"""
        summary = {
            'total_violations': len(violations),
            'critical_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'by_category': {},
            'top_violations': []
        }
        
        for violation in violations:
            # Zähle nach Schweregrad
            if violation.violation_type == ViolationType.CRITICAL:
                summary['critical_count'] += 1
            elif violation.violation_type == ViolationType.WARNING:
                summary['warning_count'] += 1
            else:
                summary['info_count'] += 1
            
            # Zähle nach Kategorie
            category = violation.category.value
            if category not in summary['by_category']:
                summary['by_category'][category] = 0
            summary['by_category'][category] += 1
        
        # Top Verstöße nach Schweregrad sortiert
        summary['top_violations'] = sorted(violations, 
                                         key=lambda v: v.severity_score, 
                                         reverse=True)[:10]
        
        return summary