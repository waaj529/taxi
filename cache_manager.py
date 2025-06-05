#!/usr/bin/env python3
"""
Google Maps API Cache Management Utility
Provides command-line tools for analyzing and optimizing the API cache
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR))
sys.path.append(PROJECT_ROOT)

from core.google_maps import GoogleMapsIntegration
from core.database import get_db_connection

def analyze_cache_efficiency():
    """Analysiere Cache-Effizienz und zeige detaillierte Statistiken"""
    print("🔍 Analysiere Google Maps API Cache...")
    
    gm = GoogleMapsIntegration()
    stats = gm.get_cache_efficiency_stats()
    
    print("\n" + "="*60)
    print("📊 GOOGLE MAPS API CACHE BERICHT")
    print("="*60)
    
    # Grundlegende Statistiken
    print(f"\n🎯 CACHE-EFFIZIENZ:")
    print(f"   Gespeicherte Routen: {stats['gesamt_zwischengespeicherte_routen']}")
    print(f"   Gesamte Verwendungen: {stats['gesamt_cache_verwendungen']}")
    print(f"   Durchschnittliche Wiederverwendung: {stats['durchschnittliche_wiederverwendung']:.2f}x")
    
    # Aktuelle Sitzung
    session_efficiency = stats['sitzung_cache_effizienz_prozent']
    efficiency_icon = "🟢" if session_efficiency >= 80 else "🟡" if session_efficiency >= 50 else "🔴"
    print(f"\n📈 AKTUELLE SITZUNG:")
    print(f"   Cache-Treffer: {stats['sitzung_cache_treffer']}")
    print(f"   API-Aufrufe: {stats['sitzung_api_aufrufe']}")
    print(f"   Effizienz: {efficiency_icon} {session_efficiency:.1f}%")
    
    # Kosteneinsparungen
    print(f"\n💰 KOSTENEINSPARUNGEN:")
    print(f"   Gesparte API-Aufrufe: {stats['geschaetzte_gesparte_api_aufrufe']}")
    print(f"   Geschätzte Einsparung: €{stats['geschaetzte_kosteneinsparung_euro']:.2f}")
    
    # Top wiederverwendete Routen
    if stats['top_wiederverwendete_routen']:
        print(f"\n🚗 TOP WIEDERVERWENDETE ROUTEN:")
        for i, route in enumerate(stats['top_wiederverwendete_routen'][:5], 1):
            origin = route['origin_address'][:30] + "..." if len(route['origin_address']) > 30 else route['origin_address']
            dest = route['destination_address'][:30] + "..." if len(route['destination_address']) > 30 else route['destination_address']
            print(f"   {i}. {origin} → {dest}")
            print(f"      Verwendet: {route['use_count']}x | {route['distance_km']:.1f}km | {route['duration_minutes']:.0f}min")
    
    print("\n" + "="*60)
    
    return stats

def optimize_cache():
    """Optimiere den Cache durch Entfernung alter Einträge"""
    print("🗂️ Optimiere Google Maps API Cache...")
    
    gm = GoogleMapsIntegration()
    deleted_entries = gm.optimize_cache()
    
    print(f"✅ Cache-Optimierung abgeschlossen!")
    print(f"   Entfernte Einträge: {deleted_entries}")
    
    if deleted_entries > 0:
        print("   ↳ Alte, selten genutzte Cache-Einträge wurden entfernt")
    else:
        print("   ↳ Keine Einträge benötigten Optimierung")

def preload_common_routes():
    """Lade häufig verwendete Routen vorab in den Cache"""
    print("🔄 Lade häufige Routen in den Cache...")
    
    # Häufige deutsche Städte/Orte als Beispiel
    common_destinations = [
        "Berlin, Deutschland",
        "Hamburg, Deutschland", 
        "München, Deutschland",
        "Köln, Deutschland",
        "Frankfurt am Main, Deutschland",
        "Stuttgart, Deutschland",
        "Düsseldorf, Deutschland",
        "Leipzig, Deutschland",
        "Dortmund, Deutschland",
        "Essen, Deutschland"
    ]
    
    # Hole Firmenhauptsitz aus Konfiguration
    try:
        from core.database import get_company_config
        headquarters = get_company_config(1, 'headquarters_address') or 'Muster Str 1, 45451 MusterStadt'
    except:
        headquarters = 'Muster Str 1, 45451 MusterStadt'
    
    print(f"   Firmenhauptsitz: {headquarters}")
    print(f"   Häufige Ziele: {len(common_destinations)}")
    
    gm = GoogleMapsIntegration()
    gm.preload_common_routes(headquarters, common_destinations)
    
    print("✅ Vorladen abgeschlossen!")

def export_cache_report(filename: str = None):
    """Exportiere Cache-Bericht als CSV"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"google_maps_cache_report_{timestamp}.csv"
    
    print(f"📁 Exportiere Cache-Bericht nach {filename}...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT origin_address, destination_address, distance_km, duration_minutes,
               use_count, created_date, last_used
        FROM address_cache
        ORDER BY use_count DESC, last_used DESC
    """)
    
    cache_entries = cursor.fetchall()
    conn.close()
    
    with open(filename, 'w', encoding='utf-8') as f:
        # CSV Header
        f.write("Von,Nach,Entfernung_km,Dauer_min,Verwendungen,Erstellt,Letzte_Nutzung\n")
        
        for entry in cache_entries:
            f.write(f'"{entry["origin_address"]}","{entry["destination_address"]}",'
                   f'{entry["distance_km"]},{entry["duration_minutes"]},'
                   f'{entry["use_count"]},{entry["created_date"]},{entry["last_used"]}\n')
    
    print(f"✅ Bericht exportiert: {len(cache_entries)} Einträge")
    print(f"   Datei: {os.path.abspath(filename)}")

def clear_cache():
    """Lösche den gesamten Cache (mit Bestätigung)"""
    print("🗑️ Cache leeren...")
    
    response = input("⚠️ Sind Sie sicher? Alle Cache-Einträge werden gelöscht (j/N): ")
    if response.lower() not in ['j', 'ja', 'y', 'yes']:
        print("❌ Abgebrochen.")
        return
    
    gm = GoogleMapsIntegration()
    gm.clear_cache()
    
    print("✅ Cache vollständig geleert!")

def show_cache_usage_by_timeframe():
    """Zeige Cache-Nutzung nach Zeitrahmen"""
    print("📅 Cache-Nutzung nach Zeitrahmen...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timeframes = [
        ("Heute", "date(last_used) = date('now')"),
        ("Letzte Woche", "last_used >= datetime('now', '-7 days')"),
        ("Letzter Monat", "last_used >= datetime('now', '-30 days')"),
        ("Letztes Jahr", "last_used >= datetime('now', '-365 days')")
    ]
    
    print("\n📊 CACHE-NUTZUNG NACH ZEITRAHMEN:")
    for name, condition in timeframes:
        cursor.execute(f"""
            SELECT COUNT(*) as entries, SUM(use_count) as total_uses
            FROM address_cache 
            WHERE {condition}
        """)
        result = cursor.fetchone()
        entries = result['entries'] or 0
        uses = result['total_uses'] or 0
        print(f"   {name:15} | Einträge: {entries:4} | Verwendungen: {uses:4}")
    
    conn.close()

def monitor_live_cache():
    """Live-Monitoring des Caches (experimentell)"""
    print("📡 Live Cache-Monitoring...")
    print("Drücken Sie Ctrl+C zum Beenden\n")
    
    try:
        gm = GoogleMapsIntegration()
        last_stats = gm.get_cache_efficiency_stats()
        
        while True:
            import time
            time.sleep(5)  # Überprüfe alle 5 Sekunden
            
            current_stats = gm.get_cache_efficiency_stats()
            
            # Prüfe auf Änderungen
            if (current_stats['sitzung_cache_treffer'] != last_stats['sitzung_cache_treffer'] or 
                current_stats['sitzung_api_aufrufe'] != last_stats['sitzung_api_aufrufe']):
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                hits = current_stats['sitzung_cache_treffer']
                calls = current_stats['sitzung_api_aufrufe']
                efficiency = current_stats['sitzung_cache_effizienz_prozent']
                
                print(f"[{timestamp}] Treffer: {hits:3} | API: {calls:3} | Effizienz: {efficiency:5.1f}%")
                last_stats = current_stats
                
    except KeyboardInterrupt:
        print("\n👋 Monitoring beendet.")

def main():
    parser = argparse.ArgumentParser(
        description="Google Maps API Cache Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python cache_manager.py analyze          # Zeige Cache-Statistiken
  python cache_manager.py optimize         # Optimiere Cache
  python cache_manager.py preload          # Lade häufige Routen vor
  python cache_manager.py export           # Exportiere Cache-Bericht
  python cache_manager.py clear            # Lösche gesamten Cache
  python cache_manager.py timeframe        # Zeige Nutzung nach Zeit
  python cache_manager.py monitor          # Live-Monitoring
        """
    )
    
    parser.add_argument('command', choices=[
        'analyze', 'optimize', 'preload', 'export', 'clear', 'timeframe', 'monitor'
    ], help='Auszuführender Befehl')
    
    parser.add_argument('--export-file', '-f', type=str,
                       help='Dateiname für Cache-Export (nur bei export)')
    
    args = parser.parse_args()
    
    print("🗺️ Google Maps API Cache Manager")
    print("-" * 40)
    
    try:
        if args.command == 'analyze':
            analyze_cache_efficiency()
            
        elif args.command == 'optimize':
            optimize_cache()
            
        elif args.command == 'preload':
            preload_common_routes()
            
        elif args.command == 'export':
            export_cache_report(args.export_file)
            
        elif args.command == 'clear':
            clear_cache()
            
        elif args.command == 'timeframe':
            show_cache_usage_by_timeframe()
            
        elif args.command == 'monitor':
            monitor_live_cache()
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()