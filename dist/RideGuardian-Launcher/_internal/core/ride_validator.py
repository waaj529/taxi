import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

class RideValidator:
    """Kern-Fahrtvalidierungs-Engine zur Umsetzung der 5 kritischen Fahrtregeln"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.headquarters_location = "Zentrale"  # Dies sollte konfigurierbar sein
        
    def validate_ride(self, ride_data: Dict) -> Tuple[bool, List[str]]:
        """
        Fahrt gegen alle Regeln validieren
        Rückgabe: (ist_gültig, liste_der_verstöße)
        """
        violations = []
        
        # Aktuelle Regeln aus Datenbank abrufen
        rules = self._get_rules()
        
        # Regel 1: Schichtbeginn in der Zentrale
        if not self._validate_shift_start(ride_data, rules):
            violations.append("REGEL_1_SCHICHTBEGINN")
            
        # Regel 2: Abholentfernung (max. 24 Min., außer reservierte Fahrten)
        pickup_violation = self._validate_pickup_distance(ride_data, rules)
        if pickup_violation:
            violations.append(pickup_violation)
            
        # Regel 3: Nach-Fahrt-Logik (30min/18min/7km Regeln)
        post_ride_violation = self._validate_post_ride_logic(ride_data, rules)
        if post_ride_violation:
            violations.append(post_ride_violation)
            
        # Regel 4: Zeitabstand zwischen Fahrten (±10 Minuten Toleranz)
        time_gap_violation = self._validate_time_gaps(ride_data, rules)
        if time_gap_violation:
            violations.append(time_gap_violation)
            
        # Regel 5: Logische Routenvalidierung
        route_violation = self._validate_route_logic(ride_data, rules)
        if route_violation:
            violations.append(route_violation)
            
        return len(violations) == 0, violations
        
    def _get_rules(self) -> Dict:
        """Aktuelle Regeln aus Datenbank abrufen"""
        cursor = self.db.cursor()
        cursor.execute("SELECT rule_name, rule_value FROM rules WHERE enabled = 1")
        rules = {}
        for row in cursor.fetchall():
            try:
                # Versuche zuerst als Zahl zu parsen, dann als String
                try:
                    rules[row['rule_name']] = float(row['rule_value'])
                except ValueError:
                    rules[row['rule_name']] = row['rule_value']
            except:
                rules[row['rule_name']] = row['rule_value']
        
        # Standardwerte setzen falls nicht gefunden
        defaults = {
            'max_pickup_distance_minutes': 24,
            'max_next_job_distance_minutes': 30,
            'max_previous_dest_minutes': 18,
            'max_hq_deviation_km': 7,
            'time_tolerance_minutes': 10,
            'shift_start_location': 'Zentrale'
        }
        
        for key, value in defaults.items():
            if key not in rules:
                rules[key] = value
                
        return rules
        
    def _validate_shift_start(self, ride_data: Dict, rules: Dict) -> bool:
        """Regel 1: Fahrer muss Schicht in der Zentrale beginnen"""
        driver_id = ride_data.get('driver_id')
        pickup_time = ride_data.get('pickup_time')
        
        if not driver_id or not pickup_time:
            return False
            
        # Prüfen ob dies die erste Fahrt der Schicht ist
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT pickup_location FROM rides 
            WHERE driver_id = ? AND DATE(pickup_time) = DATE(?) 
            ORDER BY pickup_time ASC LIMIT 1
        """, (driver_id, pickup_time))
        
        first_ride = cursor.fetchone()
        if first_ride and first_ride['pickup_location']:
            # Prüfen ob erste Fahrt von der Zentrale startete
            return self._is_headquarters_location(first_ride['pickup_location'])
            
        return True  # Keine vorherigen Fahrten, daher akzeptabel
        
    def _validate_pickup_distance(self, ride_data: Dict, rules: Dict) -> Optional[str]:
        """Regel 2: Max. Abholentfernung (24 Min.), außer für reservierte Fahrten"""
        is_reserved = ride_data.get('is_reserved', False)
        
        if is_reserved:
            return None  # Keine Entfernungsprüfung für reservierte Fahrten
            
        # Aktuellen Standort des Fahrers abrufen (von vorheriger Fahrt oder Zentrale)
        current_location = self._get_driver_current_location(
            ride_data.get('driver_id'), 
            ride_data.get('pickup_time')
        )
        
        pickup_location = ride_data.get('pickup_location')
        max_distance_minutes = rules.get('max_pickup_distance_minutes', 24)
        
        # Entfernung/Zeit zum Abholort berechnen
        distance_minutes = self._calculate_travel_time(current_location, pickup_location)
        
        if distance_minutes > max_distance_minutes:
            return f"REGEL_2_ABHOLENTFERNUNG_ÜBERSCHRITTEN_{distance_minutes}min"
            
        return None
        
    def _validate_post_ride_logic(self, ride_data: Dict, rules: Dict) -> Optional[str]:
        """Regel 3: Komplexe Nach-Fahrt-Validierungslogik"""
        driver_id = ride_data.get('driver_id')
        current_time = ride_data.get('pickup_time')
        
        # Nächste Auftragsdetails abrufen
        next_job = self._get_next_job(driver_id, current_time)
        if not next_job:
            # Kein nächster Auftrag - sollte zur Zentrale zurückkehren
            return self._validate_return_to_hq(ride_data, rules)
            
        current_destination = ride_data.get('destination')
        next_pickup = next_job.get('pickup_location')
        
        # Fall 1: Neuer Auftrag direkt danach
        distance_to_next = self._calculate_travel_time(current_destination, next_pickup)
        distance_to_prev_dest = self._calculate_travel_time(current_destination, ride_data.get('pickup_location'))
        
        max_next_job_minutes = rules.get('max_next_job_distance_minutes', 30)
        max_prev_dest_minutes = rules.get('max_previous_dest_minutes', 18)
        
        if distance_to_next <= max_next_job_minutes and distance_to_prev_dest <= max_prev_dest_minutes:
            return None  # Gültig
            
        # Fall 2: Zentral-Abweichungsregel prüfen
        return self._validate_hq_deviation(current_destination, next_pickup, rules)
        
    def _validate_hq_deviation(self, current_location: str, next_location: str, rules: Dict) -> Optional[str]:
        """7km Zentral-Abweichungsregel validieren"""
        hq_location = rules.get('shift_start_location', 'Zentrale')
        max_deviation_km = rules.get('max_hq_deviation_km', 7)
        
        # Entfernungen berechnen
        current_to_hq = self._calculate_distance_km(current_location, hq_location)
        next_to_hq = self._calculate_distance_km(next_location, hq_location)
        
        deviation = next_to_hq - current_to_hq
        
        if deviation > max_deviation_km:
            return f"REGEL_3_ZENTRAL_ABWEICHUNG_ÜBERSCHRITTEN_{deviation:.1f}km"
            
        return None
        
    def _validate_time_gaps(self, ride_data: Dict, rules: Dict) -> Optional[str]:
        """Regel 4: Zeitabstand zwischen Fahrten (±10 Minuten Toleranz)"""
        driver_id = ride_data.get('driver_id')
        pickup_time = ride_data.get('pickup_time')
        tolerance_minutes = rules.get('time_tolerance_minutes', 10)
        
        # Vorherige Fahrt-Endzeit abrufen
        prev_ride = self._get_previous_ride(driver_id, pickup_time)
        if not prev_ride:
            return None  # Keine vorherige Fahrt zum Vergleichen
            
        # Zeitabstand berechnen
        try:
            current_time = datetime.fromisoformat(pickup_time.replace('Z', '+00:00'))
            # Fix: 'dropoff_time' statt 'end_time' verwenden um dem Datenbankschema zu entsprechen
            prev_end_time_str = prev_ride.get('dropoff_time')
            if not prev_end_time_str:
                return None  # Keine Abgabezeit zum Vergleichen verfügbar
                
            prev_end_time = datetime.fromisoformat(prev_end_time_str.replace('Z', '+00:00'))
            
            gap_minutes = (current_time - prev_end_time).total_seconds() / 60
            
            if abs(gap_minutes) > tolerance_minutes:
                return f"REGEL_4_ZEITABSTAND_ÜBERSCHRITTEN_{gap_minutes:.1f}min"
                
        except (ValueError, TypeError):
            return "REGEL_4_ZEITABSTAND_PARSE_FEHLER"
            
        return None
        
    def _validate_route_logic(self, ride_data: Dict, rules: Dict) -> Optional[str]:
        """Regel 5: Logische Routenvalidierung während Fahrten"""
        # Prüfen ob Auftrag während einer anderen Fahrt zugewiesen wurde
        if ride_data.get('assigned_during_ride', False):
            # Validieren dass Abholort auf logischer Route liegt
            current_route = ride_data.get('current_route_destination')
            pickup_location = ride_data.get('pickup_location')
            
            if not self._is_on_logical_route(current_route, pickup_location):
                return "REGEL_5_UNLOGISCHE_ROUTE"
                
        return None
        
    def _get_driver_current_location(self, driver_id: int, current_time: str) -> str:
        """Aktuellen Standort des Fahrers basierend auf letzter Fahrt oder Zentrale abrufen"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT destination FROM rides 
            WHERE driver_id = ? AND pickup_time < ? 
            ORDER BY pickup_time DESC LIMIT 1
        """, (driver_id, current_time))
        
        last_ride = cursor.fetchone()
        if last_ride:
            return last_ride['destination']
        else:
            return self.headquarters_location
            
    def _get_next_job(self, driver_id: int, current_time: str) -> Optional[Dict]:
        """Nächsten geplanten Auftrag für Fahrer abrufen"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? AND pickup_time > ? 
            ORDER BY pickup_time ASC LIMIT 1
        """, (driver_id, current_time))
        
        next_ride = cursor.fetchone()
        return dict(next_ride) if next_ride else None
        
    def _get_previous_ride(self, driver_id: int, current_time: str) -> Optional[Dict]:
        """Vorherige Fahrt für Zeitabstandsberechnung abrufen"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM rides 
            WHERE driver_id = ? AND pickup_time < ? 
            ORDER BY pickup_time DESC LIMIT 1
        """, (driver_id, current_time))
        
        prev_ride = cursor.fetchone()
        return dict(prev_ride) if prev_ride else None
        
    def _calculate_travel_time(self, from_location: str, to_location: str) -> float:
        """Reisezeit zwischen Standorten berechnen (Platzhalter - mit Google Maps API integrieren)"""
        # Platzhalter-Implementierung - sollte mit Google Maps API integriert werden
        # Vorerst Mock-Berechnung basierend auf String-Entfernung zurückgeben
        if not from_location or not to_location:
            return 0
            
        # Mock-Berechnung - durch tatsächliche Google Maps API Integration ersetzen
        distance_factor = abs(len(from_location) - len(to_location)) * 2
        return min(distance_factor, 60)  # Bei 60 Minuten begrenzen
        
    def _calculate_distance_km(self, from_location: str, to_location: str) -> float:
        """Entfernung in km zwischen Standorten berechnen"""
        # Platzhalter - sollte mit Google Maps API integriert werden
        if not from_location or not to_location:
            return 0
            
        # Mock-Berechnung
        distance_factor = abs(len(from_location) - len(to_location)) * 0.5
        return distance_factor
        
    def _is_headquarters_location(self, location: str) -> bool:
        """Prüfen ob Standort die Zentrale ist"""
        if not location:
            return False
        return "zentrale" in location.lower() or "hq" in location.lower() or "headquarters" in location.lower()
        
    def _is_on_logical_route(self, current_route: str, pickup_location: str) -> bool:
        """Prüfen ob Abholort auf logischer Route liegt"""
        # Platzhalter - sollte tatsächliche Routenlogik implementieren
        return True  # Vorerst annehmen dass alle Routen logisch sind
        
    def _validate_return_to_hq(self, ride_data: Dict, rules: Dict) -> Optional[str]:
        """Rückkehr zur Zentrale validieren wenn kein nächster Auftrag"""
        destination = ride_data.get('destination')
        
        if not self._is_headquarters_location(destination):
            return "REGEL_3_KEINE_RÜCKKEHR_ZUR_ZENTRALE"
            
        return None
        
    def update_ride_violations(self, ride_id: int, violations: List[str]) -> None:
        """Fahrtdatensatz mit Verstößen aktualisieren"""
        cursor = self.db.cursor()
        violations_json = json.dumps(violations) if violations else None
        status = "Verstoß" if violations else "Abgeschlossen"
        
        cursor.execute("""
            UPDATE rides 
            SET violations = ?, status = ? 
            WHERE id = ?
        """, (violations_json, status, ride_id))
        
        self.db.commit()