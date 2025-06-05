#!/usr/bin/env python3
"""
Google Maps API Cache Demo
Demonstrates the enhanced caching system with real-world scenarios
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR))
sys.path.append(PROJECT_ROOT)

from core.google_maps import GoogleMapsIntegration
from core.database import get_db_connection

def demo_cache_efficiency():
    """Demonstriere Cache-Effizienz mit typischen Fahrtenbuch-Szenarien"""
    print("🚗 Google Maps API Cache Demo")
    print("="*50)
    
    # Initialisiere Google Maps Integration
    gm = GoogleMapsIntegration()
    
    # Firmenhauptsitz (typisch für deutsche Taxi-/Transportfirma)
    headquarters = "Hauptbahnhof 1, 60329 Frankfurt am Main"
    
    # Häufige Ziele in und um Frankfurt
    common_destinations = [
        "Flughafen Frankfurt am Main, Frankfurt am Main",
        "Messe Frankfurt, Frankfurt am Main", 
        "Zeil 106, 60313 Frankfurt am Main",  # Einkaufszentrum
        "Sachsenhausen, Frankfurt am Main",
        "Bockenheim, Frankfurt am Main",
        "Höchst, Frankfurt am Main",
        "Bad Homburg vor der Höhe",
        "Offenbach am Main",
        "Darmstadt Hauptbahnhof",
        "Mainz Hauptbahnhof"
    ]
    
    print(f"📍 Firmenstandort: {headquarters}")
    print(f"🎯 Teste {len(common_destinations)} häufige Ziele")
    print(f"🔄 Simuliere typische Fahrtenbuch-Anfragen...\n")
    
    # Phase 1: Erste Fahrt-Berechnungen (sollten API-Aufrufe sein)
    print("Phase 1: Erste Berechnungen (API-Aufrufe erwartet)")
    print("-" * 50)
    
    start_time = time.time()
    first_round_results = []
    
    for i, destination in enumerate(common_destinations[:5], 1):
        print(f"🚖 Fahrt {i}: {headquarters[:30]}... → {destination[:30]}...")
        
        # Hinfahrt
        distance, duration = gm.calculate_distance_and_duration(headquarters, destination)
        first_round_results.append((headquarters, destination, distance, duration))
        
        # Rückfahrt  
        distance_back, duration_back = gm.calculate_distance_and_duration(destination, headquarters)
        first_round_results.append((destination, headquarters, distance_back, duration_back))
        
        print(f"   Hin: {distance:.1f}km, {duration:.0f}min | Zurück: {distance_back:.1f}km, {duration_back:.0f}min")
    
    phase1_time = time.time() - start_time
    print(f"\n⏱️ Phase 1 Zeit: {phase1_time:.2f} Sekunden")
    
    # Phase 2: Wiederholung derselben Routen (sollten Cache-Treffer sein)
    print(f"\nPhase 2: Wiederholung (Cache-Treffer erwartet)")
    print("-" * 50)
    
    start_time = time.time()
    
    for i, (origin, dest, expected_dist, expected_dur) in enumerate(first_round_results[:5], 1):
        print(f"🔄 Wiederholung {i}: {origin[:30]}... → {dest[:30]}...")
        
        distance, duration = gm.calculate_distance_and_duration(origin, dest)
        
        # Prüfe ob Ergebnisse konsistent sind
        dist_match = abs(distance - expected_dist) < 0.1
        dur_match = abs(duration - expected_dur) < 1.0
        
        status = "✅" if dist_match and dur_match else "⚠️"
        print(f"   {status} {distance:.1f}km, {duration:.0f}min (erwartet: {expected_dist:.1f}km, {expected_dur:.0f}min)")
    
    phase2_time = time.time() - start_time
    speedup = phase1_time / phase2_time if phase2_time > 0 else float('inf')
    
    print(f"\n⏱️ Phase 2 Zeit: {phase2_time:.2f} Sekunden")
    print(f"🚀 Geschwindigkeitsgewinn: {speedup:.1f}x schneller")
    
    # Phase 3: Batch-Berechnung (gemischte Cache-Treffer und API-Aufrufe)
    print(f"\nPhase 3: Batch-Berechnung (gemischt)")
    print("-" * 50)
    
    # Mische bekannte und neue Ziele
    batch_origins = [headquarters, common_destinations[0], common_destinations[1]]
    batch_destinations = common_destinations[2:7]  # Teilweise neu
    
    print(f"📊 Batch: {len(batch_origins)} × {len(batch_destinations)} = {len(batch_origins) * len(batch_destinations)} Kombinationen")
    
    start_time = time.time()
    batch_results = gm.batch_calculate_distances(batch_origins, batch_destinations)
    batch_time = time.time() - start_time
    
    print(f"⏱️ Batch-Zeit: {batch_time:.2f} Sekunden")
    
    # Zeige einige Batch-Ergebnisse
    for i, origin in enumerate(batch_origins[:2]):
        for j, dest in enumerate(batch_destinations[:2]):
            if i < len(batch_results) and j < len(batch_results[i]):
                distance, duration = batch_results[i][j]
                print(f"   {origin[:25]}... → {dest[:25]}... | {distance:.1f}km, {duration:.0f}min")
    
    # Phase 4: Cache-Statistiken
    print(f"\nPhase 4: Cache-Statistiken")
    print("-" * 50)
    
    stats = gm.get_cache_efficiency_stats()
    
    print(f"📈 Sitzungsstatistiken:")
    print(f"   Cache-Treffer: {stats['sitzung_cache_treffer']}")
    print(f"   API-Aufrufe: {stats['sitzung_api_aufrufe']}")
    print(f"   Effizienz: {stats['sitzung_cache_effizienz_prozent']:.1f}%")
    
    print(f"\n💰 Kosteneinsparungen:")
    print(f"   Gesparte API-Aufrufe: {stats['geschaetzte_gesparte_api_aufrufe']}")
    print(f"   Geschätzte Einsparung: €{stats['geschaetzte_kosteneinsparung_euro']:.2f}")
    
    print(f"\n📊 Gesamtstatistiken:")
    print(f"   Gespeicherte Routen: {stats['gesamt_zwischengespeicherte_routen']}")
    print(f"   Gesamtverwendungen: {stats['gesamt_cache_verwendungen']}")
    print(f"   Durchschn. Wiederverwendung: {stats['durchschnittliche_wiederverwendung']:.1f}x")
    
    return stats

def demo_address_normalization():
    """Demonstriere Adressnormalisierung für bessere Cache-Effizienz"""
    print("\n🏠 Adressnormalisierung Demo")
    print("="*50)
    
    gm = GoogleMapsIntegration()
    
    # Verschiedene Schreibweisen derselben Adresse
    address_variations = [
        "hauptbahnhof 1, frankfurt am main",
        "Hauptbahnhof 1, Frankfurt am Main", 
        "HAUPTBAHNHOF 1, FRANKFURT AM MAIN",
        "Hauptbahnhof  1,  Frankfurt  am  Main",  # Extra Leerzeichen
        "Hauptbahnhof 1 , Frankfurt am Main",
        "hauptbahnhof 1,frankfurt am main"  # Ohne Leerzeichen
    ]
    
    print("📝 Teste verschiedene Adressschreibweisen:")
    
    destination = "Flughafen Frankfurt am Main"
    
    for i, address in enumerate(address_variations, 1):
        print(f"\n{i}. Original: '{address}'")
        normalized = gm._normalize_address(address)
        print(f"   Normalisiert: '{normalized}'")
        
        # Berechne Entfernung (sollte beim zweiten Mal aus Cache kommen)
        distance, duration = gm.calculate_distance_and_duration(address, destination)
        print(f"   Ergebnis: {distance:.1f}km, {duration:.0f}min")
    
    print(f"\n✅ Alle Variationen sollten dieselben Ergebnisse liefern!")
    print(f"   Cache kann verschiedene Schreibweisen derselben Adresse wiedererkennen.")

def demo_route_optimization():
    """Demonstriere Routenoptimierung für Fahrtenbuch"""
    print("\n🛣️ Routenoptimierung Demo")
    print("="*50)
    
    gm = GoogleMapsIntegration()
    
    # Simuliere Arbeitstag eines Fahrers
    headquarters = "Hauptbahnhof 1, Frankfurt am Main"
    
    daily_routes = [
        # Morgendliche Touren
        (headquarters, "Flughafen Frankfurt am Main"),
        ("Flughafen Frankfurt am Main", "Messe Frankfurt"),
        ("Messe Frankfurt", "Zeil 106, Frankfurt am Main"),
        
        # Mittagstouren
        ("Zeil 106, Frankfurt am Main", "Sachsenhausen, Frankfurt am Main"),
        ("Sachsenhausen, Frankfurt am Main", "Bad Homburg vor der Höhe"),
        ("Bad Homburg vor der Höhe", headquarters),
        
        # Nachmittagstouren
        (headquarters, "Offenbach am Main"),
        ("Offenbach am Main", "Darmstadt"),
        ("Darmstadt", headquarters)
    ]
    
    print(f"📅 Simuliere Arbeitstag mit {len(daily_routes)} Fahrten:")
    
    total_distance = 0
    total_duration = 0
    total_api_calls_before = gm.api_calls
    
    for i, (origin, destination) in enumerate(daily_routes, 1):
        print(f"\n🚖 Fahrt {i}: {origin[:25]}... → {destination[:25]}...")
        
        distance, duration = gm.calculate_distance_and_duration(origin, destination)
        total_distance += distance
        total_duration += duration
        
        print(f"   {distance:.1f}km, {duration:.0f}min")
        
        # Prüfe ob Route logisch ist (für Fahrtenbuch-Validierung)
        if i > 1:
            previous_dest = daily_routes[i-2][1]  # Vorheriges Ziel
            current_origin = origin
            
            # Sollten übereinstimmen für zusammenhängende Routen
            if previous_dest != current_origin:
                print(f"   ⚠️ Routensprung erkannt: {previous_dest} → {current_origin}")
    
    total_api_calls_after = gm.api_calls
    new_api_calls = total_api_calls_after - total_api_calls_before
    
    print(f"\n📊 Tagesbilanz:")
    print(f"   Gesamtstrecke: {total_distance:.1f}km")
    print(f"   Gesamtdauer: {total_duration:.0f}min ({total_duration/60:.1f}h)")
    print(f"   Neue API-Aufrufe: {new_api_calls}")
    print(f"   Cache-Effizienz: {((len(daily_routes) - new_api_calls) / len(daily_routes) * 100):.1f}%")

def demo_excel_like_workflow():
    """Demonstriere Excel-ähnlichen Workflow für Fahrtenbuch"""
    print("\n📊 Excel-ähnlicher Workflow Demo")
    print("="*50)
    
    print("Simuliere Excel-Import von Fahrtdaten mit automatischer Entfernungsberechnung...")
    
    # Simuliere Excel-Daten (normalerweise aus Datei gelesen)
    excel_rides = [
        {"driver": "Max Müller", "pickup": "Hauptbahnhof Frankfurt", "destination": "Flughafen Frankfurt", "date": "2025-06-03"},
        {"driver": "Anna Schmidt", "pickup": "Flughafen Frankfurt", "destination": "Messe Frankfurt", "date": "2025-06-03"},
        {"driver": "Max Müller", "pickup": "Messe Frankfurt", "destination": "Hauptbahnhof Frankfurt", "date": "2025-06-03"},
        {"driver": "Peter Wagner", "pickup": "Hauptbahnhof Frankfurt", "destination": "Bad Homburg", "date": "2025-06-03"},
        {"driver": "Anna Schmidt", "pickup": "Bad Homburg", "destination": "Hauptbahnhof Frankfurt", "date": "2025-06-03"},
    ]
    
    gm = GoogleMapsIntegration()
    
    print(f"📥 Verarbeite {len(excel_rides)} Fahrten aus Excel-Import:")
    
    processed_rides = []
    cache_hits = 0
    api_calls_before = gm.api_calls
    
    for i, ride in enumerate(excel_rides, 1):
        print(f"\n📋 Fahrt {i} - {ride['driver']}:")
        print(f"   {ride['pickup']} → {ride['destination']}")
        
        # Prüfe Cache vorher
        cached_dist, cached_dur = gm.gm.get_address_cache(ride['pickup'], ride['destination']) if hasattr(gm, 'gm') else (None, None)
        was_cached = cached_dist is not None
        
        # Berechne Entfernung und Dauer
        distance, duration = gm.calculate_distance_and_duration(ride['pickup'], ride['destination'])
        
        if was_cached:
            cache_hits += 1
            print(f"   ✅ Cache-Treffer: {distance:.1f}km, {duration:.0f}min")
        else:
            print(f"   🌐 API-Aufruf: {distance:.1f}km, {duration:.0f}min")
        
        # Erweitere Fahrtdaten
        processed_ride = ride.copy()
        processed_ride.update({
            'distance_km': distance,
            'duration_minutes': duration,
            'estimated_cost': distance * 0.30,  # €0.30 pro km Schätzung
            'was_cached': was_cached
        })
        processed_rides.append(processed_ride)
    
    api_calls_after = gm.api_calls
    new_api_calls = api_calls_after - api_calls_before
    
    print(f"\n📈 Import-Statistiken:")
    print(f"   Verarbeitete Fahrten: {len(processed_rides)}")
    print(f"   Cache-Treffer: {cache_hits}/{len(excel_rides)} ({cache_hits/len(excel_rides)*100:.1f}%)")
    print(f"   Neue API-Aufrufe: {new_api_calls}")
    print(f"   Geschätzte gesparte Kosten: €{(len(excel_rides) - new_api_calls) * 0.005:.3f}")
    
    # Zeige verarbeitete Daten
    print(f"\n📊 Verarbeitete Fahrtdaten:")
    total_distance = sum(ride['distance_km'] for ride in processed_rides)
    total_cost = sum(ride['estimated_cost'] for ride in processed_rides)
    
    print(f"   Gesamtstrecke: {total_distance:.1f}km")
    print(f"   Geschätzte Gesamtkosten: €{total_cost:.2f}")
    
    return processed_rides

def main():
    """Hauptfunktion für Cache-Demo"""
    print("🗺️ Google Maps API Cache System Demo")
    print("Demonstriert verbessertes Caching wie in Excel-Implementierung")
    print("="*70)
    
    try:
        # Demo 1: Cache-Effizienz
        stats1 = demo_cache_efficiency()
        
        # Demo 2: Adressnormalisierung
        demo_address_normalization()
        
        # Demo 3: Routenoptimierung
        demo_route_optimization()
        
        # Demo 4: Excel-ähnlicher Workflow
        processed_rides = demo_excel_like_workflow()
        
        # Finale Statistiken
        print(f"\n🎯 Finale Cache-Statistiken")
        print("="*50)
        
        gm = GoogleMapsIntegration()
        final_stats = gm.get_cache_efficiency_stats()
        
        print(f"📊 Gesamt-Cache-Performance:")
        print(f"   Effizienz: {final_stats['sitzung_cache_effizienz_prozent']:.1f}%")
        print(f"   Gesparte API-Aufrufe: {final_stats['geschaetzte_gesparte_api_aufrufe']}")
        print(f"   Kosteneinsparung: €{final_stats['geschaetzte_kosteneinsparung_euro']:.2f}")
        
        print(f"\n✅ Demo abgeschlossen!")
        print(f"   Das Caching-System ist bereit für den Produktiveinsatz.")
        print(f"   Verwenden Sie 'python cache_manager.py analyze' für detaillierte Statistiken.")
        
    except Exception as e:
        print(f"❌ Demo-Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()