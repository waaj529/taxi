import requests
import json
from typing import Dict, List, Tuple, Optional
import os
import hashlib
import re
from datetime import datetime
from core.database import get_address_cache, cache_address_result

class GoogleMapsIntegration:
    """Google Maps API Integration für Entfernungs-, Dauer- und Routenberechnungen mit verbesserter Zwischenspeicherung"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.cache_enabled = True
        self.cache_hits = 0
        self.api_calls = 0
        self.session = requests.Session()  # Reuse connections for better performance
        
    def _normalize_address(self, address: str) -> str:
        """
        Normalisiere Adresse für konsistente Zwischenspeicherung
        Entfernt überflüssige Leerzeichen, normalisiert Großschreibung
        """
        if not address:
            return ""
        
        # Entferne führende/nachfolgende Leerzeichen und doppelte Leerzeichen
        normalized = re.sub(r'\s+', ' ', address.strip())
        
        # Normalisiere Großschreibung für deutsche Adressen
        normalized = normalized.title()
        
        # Spezielle deutsche Abkürzungen normalisieren
        replacements = {
            'Str.': 'Straße',
            'str.': 'Straße',
            'Pl.': 'Platz',
            'pl.': 'Platz',
            'Ave.': 'Avenue',
            'ave.': 'Avenue'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
            
        return normalized
    
    def _get_cache_key(self, origin: str, destination: str) -> str:
        """
        Erstelle eindeutigen Cache-Schlüssel für Adresspaar
        """
        norm_origin = self._normalize_address(origin)
        norm_dest = self._normalize_address(destination)
        
        # Erstelle Hash für konsistente Schlüsselgenerierung
        cache_string = f"{norm_origin}|{norm_dest}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def calculate_distance_and_duration(self, origin: str, destination: str, use_cache: bool = True) -> Tuple[float, float]:
        """
        Berechne Entfernung (km) und Dauer (Minuten) zwischen zwei Standorten mit verbesserter Zwischenspeicherung
        Rückgabe: (entfernung_km, dauer_minuten)
        """
        if not origin or not destination:
            return 0, 0
        
        # Normalisiere Adressen für bessere Cache-Effizienz
        norm_origin = self._normalize_address(origin)
        norm_dest = self._normalize_address(destination)
        
        # Zwischenspeicher zuerst prüfen wenn aktiviert
        if use_cache and self.cache_enabled:
            cached_distance, cached_duration = get_address_cache(norm_origin, norm_dest)
            if cached_distance is not None and cached_duration is not None:
                self.cache_hits += 1
                print(f"✓ Cache-Treffer für {norm_origin} -> {norm_dest}")
                return cached_distance, cached_duration
        
        if not self.api_key:
            # Fallback zu Mock-Berechnung wenn kein API-Schlüssel
            print(f"⚠️ Kein API-Schlüssel - verwende Mock-Berechnung für {norm_origin} -> {norm_dest}")
            return self._mock_calculation(norm_origin, norm_dest)
            
        try:
            self.api_calls += 1
            url = f"{self.base_url}/distancematrix/json"
            params = {
                'origins': norm_origin,
                'destinations': norm_dest,
                'key': self.api_key,
                'units': 'metric',
                'mode': 'driving',
                'traffic_model': 'best_guess',
                'departure_time': 'now',
                'language': 'de',
                'region': 'DE'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['rows']:
                element = data['rows'][0]['elements'][0]
                if element['status'] == 'OK':
                    distance_km = element['distance']['value'] / 1000
                    duration_minutes = element['duration']['value'] / 60
                    
                    # duration_in_traffic verwenden wenn verfügbar (genauer)
                    if 'duration_in_traffic' in element:
                        duration_minutes = element['duration_in_traffic']['value'] / 60
                    
                    # Ergebnis für zukünftige Verwendung zwischenspeichern
                    if use_cache and self.cache_enabled:
                        cache_address_result(norm_origin, norm_dest, distance_km, duration_minutes)
                        print(f"💾 Neues Ergebnis zwischengespeichert für {norm_origin} -> {norm_dest}")
                        
                    return distance_km, duration_minutes
                else:
                    print(f"❌ Google Maps Element-Fehler: {element['status']} für {norm_origin} -> {norm_dest}")
            else:
                print(f"❌ Google Maps API-Fehler: {data.get('status', 'Unknown')} für {norm_origin} -> {norm_dest}")
                    
        except Exception as e:
            print(f"❌ Google Maps API Ausnahme: {e}")
            
        # Fallback zu Mock-Berechnung
        print(f"⚠️ Fallback zur Mock-Berechnung für {norm_origin} -> {norm_dest}")
        return self._mock_calculation(norm_origin, norm_dest)
        
    def validate_address(self, address: str) -> Tuple[bool, str]:
        """
        Validiere und standardisiere eine deutsche Adresse
        Rückgabe: (ist_gültig, standardisierte_adresse)
        """
        if not self.api_key:
            return True, address  # Validierung überspringen wenn kein API-Schlüssel
            
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                'address': address,
                'key': self.api_key,
                'language': 'de',
                'region': 'DE',
                'components': 'country:DE'  # Auf deutsche Adressen beschränken
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                formatted_address = data['results'][0]['formatted_address']
                return True, formatted_address
            else:
                return False, address
                
        except Exception as e:
            print(f"Adressvalidierungsfehler: {e}")
            return True, address  # Original-Adresse bei Fehler zurückgeben
            
    def get_route_waypoints(self, origin: str, destination: str, waypoints: List[str] = None) -> List[Dict]:
        """
        Erhalte detaillierte Routeninformationen mit Wegpunkten
        Rückgabe: Liste der Routenschritte mit Koordinaten und Anweisungen
        """
        if not self.api_key:
            return []
            
        try:
            url = f"{self.base_url}/directions/json"
            params = {
                'origin': origin,
                'destination': destination,
                'key': self.api_key,
                'mode': 'driving',
                'traffic_model': 'best_guess',
                'departure_time': 'now',
                'language': 'de',
                'region': 'DE'
            }
            
            if waypoints:
                params['waypoints'] = '|'.join(waypoints)
                
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['routes']:
                route = data['routes'][0]
                schritte = []
                
                for leg in route['legs']:
                    for step in leg['steps']:
                        schritte.append({
                            'anweisung': step['html_instructions'],
                            'entfernung': step['distance']['value'] / 1000,  # km
                            'dauer': step['duration']['value'] / 60,    # Minuten
                            'startposition': step['start_location'],
                            'endposition': step['end_location']
                        })
                        
                return schritte
                
        except Exception as e:
            print(f"Routenberechnungsfehler: {e}")
            
        return []
        
    def is_location_on_route(self, route_origin: str, route_destination: str, 
                           check_location: str, tolerance_km: float = 2.0) -> bool:
        """
        Prüfe ob ein Standort sinnvoll auf der Route zwischen Start und Ziel liegt
        Verwendet für Regel 5 Validierung (logische Routenprüfung)
        """
        if not self.api_key:
            return True  # Prüfung überspringen wenn kein API-Schlüssel
            
        try:
            # Direkte Entfernung ermitteln (Zwischenspeicher verwenden)
            direkte_entfernung, _ = self.calculate_distance_and_duration(route_origin, route_destination)
            
            # Entfernung über den Prüfstandort ermitteln (Zwischenspeicher verwenden)
            zum_pruefstandort, _ = self.calculate_distance_and_duration(route_origin, check_location)
            vom_pruefstandort, _ = self.calculate_distance_and_duration(check_location, route_destination)
            
            ueber_pruefstandort = zum_pruefstandort + vom_pruefstandort
            
            # Prüfen ob Umweg innerhalb der Toleranz liegt
            umweg = ueber_pruefstandort - direkte_entfernung
            return umweg <= tolerance_km
            
        except Exception as e:
            print(f"Routenvalidierungsfehler: {e}")
            return True  # Standard: Route bei Fehler erlauben
            
    def batch_calculate_distances(self, origins: List[str], destinations: List[str]) -> List[List[Tuple[float, float]]]:
        """
        Berechne Entfernungen und Dauern für mehrere Start-Ziel-Paare mit optimierter Zwischenspeicherung
        Diese Methode minimiert API-Aufrufe durch intelligente Cache-Nutzung
        Rückgabe: Matrix von (entfernung_km, dauer_minuten) Tupeln
        """
        if not origins or not destinations:
            return []
        
        # Normalisiere alle Adressen
        norm_origins = [self._normalize_address(addr) for addr in origins]
        norm_destinations = [self._normalize_address(addr) for addr in destinations]
        
        print(f"🔄 Stapelberechnung für {len(norm_origins)} Starts × {len(norm_destinations)} Ziele")
        
        # Initialisiere Ergebnismatrix
        ergebnisse = []
        nicht_gecachte_paare = []
        cache_treffer = 0
        
        # Erste Phase: Prüfe Cache für alle Kombinationen
        for i, origin in enumerate(norm_origins):
            zeilen_ergebnisse = []
            for j, destination in enumerate(norm_destinations):
                if self.cache_enabled:
                    cached_distance, cached_duration = get_address_cache(origin, destination)
                    if cached_distance is not None and cached_duration is not None:
                        zeilen_ergebnisse.append((cached_distance, cached_duration))
                        cache_treffer += 1
                        continue
                
                # Markiere für API-Aufruf
                nicht_gecachte_paare.append((i, j, origin, destination))
                zeilen_ergebnisse.append(None)  # Platzhalter
            ergebnisse.append(zeilen_ergebnisse)
        
        print(f"✓ {cache_treffer} Cache-Treffer von {len(norm_origins) * len(norm_destinations)} Kombinationen")
        
        # Zweite Phase: API-Aufrufe für nicht gecachte Paare
        if nicht_gecachte_paare and self.api_key:
            print(f"🌐 {len(nicht_gecachte_paare)} API-Aufrufe erforderlich")
            
            # Gruppiere für effiziente Batch-API-Aufrufe
            unique_origins = list(set(pair[2] for pair in nicht_gecachte_paare))
            unique_destinations = list(set(pair[3] for pair in nicht_gecachte_paare))
            
            # Begrenze Batch-Größe (Google Maps API-Limit: 25×25)
            max_batch_size = 25
            
            if len(unique_origins) <= max_batch_size and len(unique_destinations) <= max_batch_size:
                # Einzelner Batch-API-Aufruf
                api_ergebnisse = self._single_batch_api_call(unique_origins, unique_destinations)
                
                # Ergebnisse in Matrix einsetzen
                for i, j, origin, destination in nicht_gecachte_paare:
                    if origin in api_ergebnisse and destination in api_ergebnisse[origin]:
                        ergebnisse[i][j] = api_ergebnisse[origin][destination]
                    else:
                        ergebnisse[i][j] = self._mock_calculation(origin, destination)
            else:
                # Mehrere kleinere Batch-Aufrufe
                print(f"⚡ Aufteilen in kleinere Batches (Limit: {max_batch_size})")
                for pair in nicht_gecachte_paare:
                    i, j, origin, destination = pair
                    ergebnisse[i][j] = self.calculate_distance_and_duration(origin, destination)
        
        # Dritte Phase: Alle verbleibenden None-Werte mit Mock-Berechnungen füllen
        for i, row in enumerate(ergebnisse):
            for j, result in enumerate(row):
                if result is None:
                    ergebnisse[i][j] = self._mock_calculation(norm_origins[i], norm_destinations[j])
        
        self.cache_hits += cache_treffer
        print(f"📊 Stapelberechnung abgeschlossen. Cache-Effizienz: {(cache_treffer / (len(norm_origins) * len(norm_destinations))) * 100:.1f}%")
        
        return ergebnisse
    
    def _single_batch_api_call(self, origins: List[str], destinations: List[str]) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """
        Führe einen einzelnen Batch-API-Aufruf durch und gebe strukturierte Ergebnisse zurück
        """
        try:
            self.api_calls += 1
            url = f"{self.base_url}/distancematrix/json"
            params = {
                'origins': '|'.join(origins),
                'destinations': '|'.join(destinations),
                'key': self.api_key,
                'units': 'metric',
                'mode': 'driving',
                'language': 'de',
                'region': 'DE'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            ergebnisse = {}
            
            if data['status'] == 'OK':
                for i, row in enumerate(data['rows']):
                    origin = origins[i]
                    ergebnisse[origin] = {}
                    
                    for j, element in enumerate(row['elements']):
                        destination = destinations[j]
                        
                        if element['status'] == 'OK':
                            distance_km = element['distance']['value'] / 1000
                            duration_minutes = element['duration']['value'] / 60
                            
                            # duration_in_traffic bevorzugen
                            if 'duration_in_traffic' in element:
                                duration_minutes = element['duration_in_traffic']['value'] / 60
                            
                            ergebnisse[origin][destination] = (distance_km, duration_minutes)
                            
                            # Ergebnis zwischenspeichern
                            if self.cache_enabled:
                                cache_address_result(origin, destination, distance_km, duration_minutes)
                        else:
                            print(f"⚠️ Element-Fehler für {origin} -> {destination}: {element['status']}")
                            ergebnisse[origin][destination] = self._mock_calculation(origin, destination)
            else:
                print(f"❌ Batch-API-Fehler: {data.get('status', 'Unknown')}")
                
            return ergebnisse
            
        except Exception as e:
            print(f"❌ Batch-API-Ausnahme: {e}")
            return {}
    
    def calculate_fuel_consumption(self, distance_km: float, consumption_per_100km: float = 8.5) -> float:
        """
        Berechne Kraftstoffverbrauch basierend auf Entfernung und Fahrzeugverbrauchsrate
        Rückgabe: Kraftstoffverbrauch in Litern
        """
        return (distance_km * consumption_per_100km) / 100
        
    def calculate_trip_cost(self, distance_km: float, fuel_cost_per_liter: float = 1.45, 
                          consumption_per_100km: float = 8.5, additional_costs: float = 0) -> float:
        """
        Berechne Gesamtfahrtkosten einschließlich Kraftstoff und zusätzliche Kosten
        Rückgabe: Gesamtkosten in EUR
        """
        kraftstoffverbrauch = self.calculate_fuel_consumption(distance_km, consumption_per_100km)
        kraftstoffkosten = kraftstoffverbrauch * fuel_cost_per_liter
        return kraftstoffkosten + additional_costs
        
    def get_address_suggestions(self, partial_address: str, region: str = 'DE') -> List[str]:
        """
        Erhalte Adressvorschläge für Autocomplete-Funktionalität
        Rückgabe: Liste vorgeschlagener Adressen
        """
        if not self.api_key or len(partial_address) < 3:
            return []
            
        try:
            url = f"{self.base_url}/place/autocomplete/json"
            params = {
                'input': partial_address,
                'key': self.api_key,
                'language': 'de',
                'components': f'country:{region}',
                'types': 'address'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                return [prediction['description'] for prediction in data['predictions']]
                
        except Exception as e:
            print(f"Adressvorschlagsfehler: {e}")
            
        return []
        
    def _mock_calculation(self, origin: str, destination: str) -> Tuple[float, float]:
        """
        Fallback Mock-Berechnung wenn Google Maps API nicht verfügbar ist
        Basiert auf String-Analyse - bei Bedarf durch ausgereiftere Logik ersetzen
        """
        if not origin or not destination:
            return 0, 0
            
        # Einfacher Mock basierend auf String-Unterschieden
        char_diff = abs(len(origin) - len(destination))
        mock_entfernung = max(1, char_diff * 0.5)  # km
        mock_dauer = mock_entfernung * 2  # Annahme: 30 km/h Durchschnittsgeschwindigkeit
        
        return mock_entfernung, mock_dauer
        
    def get_headquarters_coordinates(self, headquarters_address: str) -> Tuple[float, float]:
        """
        Erhalte Breiten- und Längengrad-Koordinaten für Hauptsitz
        Verwendet für genauere Entfernungsberechnungen
        """
        if not self.api_key:
            return 0.0, 0.0
            
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                'address': headquarters_address,
                'key': self.api_key,
                'language': 'de',
                'region': 'DE'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']
                
        except Exception as e:
            print(f"Geocodierungsfehler: {e}")
            
        return 0.0, 0.0
        
    def clear_cache(self):
        """Lösche den Adresszwischenspeicher (für Tests oder Reset)"""
        from core.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM address_cache")
        conn.commit()
        conn.close()
        print("Adresszwischenspeicher geleert")
        
    def get_cache_stats(self):
        """Erhalte Statistiken über Zwischenspeicherverwendung"""
        from core.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total_entries FROM address_cache")
        gesamt = cursor.fetchone()['total_entries']
        
        cursor.execute("SELECT SUM(use_count) as total_uses FROM address_cache")
        verwendungen = cursor.fetchone()['total_uses'] or 0
        
        cursor.execute("SELECT AVG(use_count) as avg_uses FROM address_cache")
        durchschn_verwendungen = cursor.fetchone()['avg_uses'] or 0
        
        conn.close()
        
        return {
            'total_cached_routes': gesamt,
            'total_cache_hits': verwendungen,
            'average_reuse': round(durchschn_verwendungen, 2)
        }
    
    def get_cache_efficiency_stats(self):
        """
        Erhalte detaillierte Statistiken über Cache-Effizienz und API-Nutzung
        """
        from core.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Grundlegende Cache-Statistiken
        cursor.execute("SELECT COUNT(*) as total_entries FROM address_cache")
        gesamt_eintraege = cursor.fetchone()['total_entries']
        
        cursor.execute("SELECT SUM(use_count) as total_uses FROM address_cache")
        gesamt_verwendungen = cursor.fetchone()['total_uses'] or 0
        
        cursor.execute("SELECT AVG(use_count) as avg_uses FROM address_cache WHERE use_count > 1")
        durchschn_wiederverwendung = cursor.fetchone()['avg_uses'] or 0
        
        # Top wiederverwendete Routen
        cursor.execute("""
            SELECT origin_address, destination_address, use_count, 
                   distance_km, duration_minutes, last_used
            FROM address_cache 
            WHERE use_count > 1
            ORDER BY use_count DESC 
            LIMIT 10
        """)
        top_routen = cursor.fetchall()
        
        # Geschätzte API-Kosten-Einsparungen
        # Annahme: €0.005 pro Google Maps API-Aufruf
        kosten_pro_aufruf = 0.005
        gesparte_aufrufe = gesamt_verwendungen - gesamt_eintraege
        gesparte_kosten = gesparte_aufrufe * kosten_pro_aufruf
        
        # Cache-Effizienz dieser Sitzung
        sitzungs_effizienz = 0
        if self.cache_hits + self.api_calls > 0:
            sitzungs_effizienz = (self.cache_hits / (self.cache_hits + self.api_calls)) * 100
        
        conn.close()
        
        return {
            'gesamt_zwischengespeicherte_routen': gesamt_eintraege,
            'gesamt_cache_verwendungen': gesamt_verwendungen,
            'durchschnittliche_wiederverwendung': round(durchschn_wiederverwendung, 2),
            'top_wiederverwendete_routen': [dict(route) for route in top_routen],
            'geschaetzte_gesparte_api_aufrufe': gesparte_aufrufe,
            'geschaetzte_kosteneinsparung_euro': round(gesparte_kosten, 2),
            'sitzung_cache_treffer': self.cache_hits,
            'sitzung_api_aufrufe': self.api_calls,
            'sitzung_cache_effizienz_prozent': round(sitzungs_effizienz, 1)
        }
    
    def optimize_cache(self):
        """
        Optimiere den Cache durch Entfernung alter, selten genutzter Einträge
        """
        from core.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Entferne Einträge älter als 6 Monate mit nur einer Verwendung
        cursor.execute("""
            DELETE FROM address_cache 
            WHERE use_count = 1 
            AND created_date < datetime('now', '-6 months')
        """)
        
        geloeschte_eintraege = cursor.rowcount
        
        # Aktualisiere Statistiken
        cursor.execute("VACUUM")  # Komprimiere Datenbank
        
        conn.commit()
        conn.close()
        
        print(f"🗂️ Cache optimiert: {geloeschte_eintraege} alte Einträge entfernt")
        return geloeschte_eintraege
    
    def preload_common_routes(self, company_headquarters: str, common_destinations: List[str]):
        """
        Lade häufig verwendete Routen vorab in den Cache
        Nützlich für neue Installationen oder nach Cache-Löschung
        """
        print(f"🔄 Lade {len(common_destinations)} häufige Routen vorab...")
        
        # Von und zur Zentrale
        for destination in common_destinations:
            if destination and destination != company_headquarters:
                # Hin- und Rückweg
                self.calculate_distance_and_duration(company_headquarters, destination)
                self.calculate_distance_and_duration(destination, company_headquarters)
        
        # Zwischen häufigen Zielen
        for i, origin in enumerate(common_destinations):
            for destination in common_destinations[i+1:]:
                if origin and destination and origin != destination:
                    self.calculate_distance_and_duration(origin, destination)
                    self.calculate_distance_and_duration(destination, origin)
        
        print(f"✓ Vorladen abgeschlossen")