"""
Translation Manager for Ride Guardian Desktop
Handles German localization throughout the application
"""

import os
from PyQt6.QtCore import QTranslator, QCoreApplication, QLocale
from typing import Dict, Optional

class TranslationManager:
    """Manages translations for the Ride Guardian Desktop application"""
    
    def __init__(self):
        self.translators = []
        self.current_language = 'de'  # Default to German
        self.translations = {}
        self.load_manual_translations()
        
    def load_manual_translations(self):
        """Load manual translations for immediate use"""
        self.translations = {
            # Main Window
            'Ride Guardian Desktop - Professional Fleet Management': 'Ride Guardian Desktop - Professionelle Flottenmanagement',
            'Database Error': 'Datenbankfehler',
            'Failed to initialize database': 'Fehler beim Initialisieren der Datenbank',
            'The application might not function correctly': 'Die Anwendung funktioniert möglicherweise nicht korrekt',
            'Please check your permissions and disk space': 'Bitte überprüfen Sie Ihre Berechtigungen und den Speicherplatz',
            'Monitoring': 'Überwachung',
            'Ride Entry': 'Fahrt eingeben',
            'Data Import': 'Daten importieren',
            'Drivers': 'Fahrer',
            'Payroll': 'Lohnabrechnung',
            'Rules': 'Regeln',
            'Reports': 'Berichte',
            'Select Company': 'Unternehmen auswählen',
            'Please select a company:': 'Bitte wählen Sie ein Unternehmen aus:',
            'Current Company:': 'Aktuelles Unternehmen:',
            'Switch Company': 'Unternehmen wechseln',

            # Single Company Application specific translations
            'dashboard': 'Dashboard',
            'ride_monitoring': 'Fahrtüberwachung',
            'add_ride': 'Fahrt hinzufügen',
            'data_import': 'Datenimport',
            'drivers': 'Fahrer',
            'payroll': 'Lohnabrechnung',
            'rules': 'Regeln',
            'reports': 'Berichte',
            'fleet_management_system': 'Flottenmanagement-System',
            'monthly_revenue': 'Monatsumsatz',
            'database_error': 'Datenbankfehler',
            'database_init_error': 'Fehler bei der Datenbankinitialisierung',
            'app_may_not_work_correctly': 'Die Anwendung funktioniert möglicherweise nicht korrekt',
            
            # Dashboard specific translations
            'dashboard_title': 'Dashboard - Flottenverwaltung',
            'loading_statistics': 'Lade Statistiken...',
            'search_and_filter': 'Suchen und Filtern',
            'search': 'Suchen',
            'search_placeholder': 'In allen Daten suchen...',
            'clear': 'Löschen',
            'date': 'Datum',
            'rides_management': 'Fahrtverwaltung',
            'drivers_management': 'Fahrerverwaltung',
            'search_results': 'Suchergebnisse',
            'database_management': 'Datenbankverwaltung',
            'ready': 'Bereit',
            
            # CRUD Operations
            'add_new_ride': 'Neue Fahrt hinzufügen',
            'edit_selected_ride': 'Ausgewählte Fahrt bearbeiten',
            'delete_selected_ride': 'Ausgewählte Fahrt löschen',
            'add_new_driver': 'Neuen Fahrer hinzufügen',
            'edit_selected_driver': 'Ausgewählten Fahrer bearbeiten', 
            'delete_selected_driver': 'Ausgewählten Fahrer löschen',
            'edit_ride': 'Fahrt bearbeiten',
            'edit_driver': 'Fahrer bearbeiten',
            
            # Dialog fields
            'pickup_date': 'Abholdatum',
            'dropoff_date': 'Ankunftsdatum',
            'pickup_address': 'Abholadresse',
            'destination_address': 'Zieladresse',
            'distance': 'Entfernung',
            'duration': 'Dauer',
            'minutes': 'Minuten',
            'vehicle_description': 'Fahrzeugbeschreibung',
            'violations_description': 'Verstöße (Beschreibung)',
            'select_driver': 'Fahrer auswählen',
            'driver_name': 'Fahrername',
            'suspended': 'Gesperrt',
            
            # Validation messages
            'please_select_driver': 'Bitte wählen Sie einen Fahrer aus',
            'please_fill_locations': 'Bitte füllen Sie Abhol- und Zielort aus',
            'duplicate_ride_error': 'Eine identische Fahrt existiert bereits',
            'duplicate_driver_error': 'Ein Fahrer mit diesem Namen existiert bereits',
            'please_select_ride_to_edit': 'Bitte wählen Sie eine Fahrt zum Bearbeiten aus',
            'please_select_ride_to_delete': 'Bitte wählen Sie eine Fahrt zum Löschen aus',
            'please_select_driver_to_edit': 'Bitte wählen Sie einen Fahrer zum Bearbeiten aus',
            'please_select_driver_to_delete': 'Bitte wählen Sie einen Fahrer zum Löschen aus',
            'please_enter_driver_name': 'Bitte geben Sie einen Fahrernamen ein',
            'invalid_data_format': 'Ungültiges Datenformat',
            'action_cannot_undone': 'Diese Aktion kann nicht rückgängig gemacht werden',
            
            # Search functionality
            'no_search_performed': 'Keine Suche durchgeführt',
            'please_enter_search_term': 'Bitte geben Sie einen Suchbegriff ein',
            'search_completed': 'Suche abgeschlossen - {} Ergebnisse gefunden',
            'search_results_info': '{} Ergebnisse für "{}"',
            'search_cleared': 'Suche gelöscht',
            'search_error': 'Suchfehler',
            'failed_to_perform_search': 'Fehler beim Durchführen der Suche',
            'type': 'Typ',
            'date_time': 'Datum/Zeit',
            'from_location': 'Von (Ort)',
            'to_location_vehicle': 'Nach (Ort/Fahrzeug)',
            'ride': 'Fahrt',
            'driver': 'Fahrer',
            
            # Filter functionality
            'filter_applied': 'Filter angewendet - {} Ergebnisse für {}',
            'filter_error': 'Filterfehler',
            'failed_to_apply_filters': 'Fehler beim Anwenden der Filter',
            
            # Database management
            'database_information': 'Datenbankinformationen',
            'loading_database_info': 'Lade Datenbankinformationen...',
            'database_operations': 'Datenbankoperationen',
            'warning_cannot_undo': 'WARNUNG: Diese Operationen können nicht rückgängig gemacht werden!',
            'clear_all_rides': 'Alle Fahrten löschen',
            'clear_all_drivers': 'Alle Fahrer löschen',
            'clear_entire_database': 'Gesamte Datenbank löschen',
            'confirm_database_operation': 'Datenbankoperation bestätigen',
            'confirm_perform_operation': 'Sind Sie sicher, dass Sie diese Operation durchführen möchten',
            'permanent_delete_warning': 'ALLE DATEN WERDEN PERMANENT GELÖSCHT!',
            'type_confirm_instruction': 'Geben Sie "CONFIRM" ein, um fortzufahren',
            'final_confirmation': 'Endgültige Bestätigung',
            'type_confirm_to_proceed': 'Geben Sie "CONFIRM" ein, um fortzufahren:',
            'cancelled': 'Abgebrochen',
            'operation_cancelled': 'Operation abgebrochen',
            'database_operation_completed': 'Datenbankoperation abgeschlossen',
            'database_statistics': 'Datenbankstatistiken',
            'database_size': 'Datenbankgröße',
            'companies': 'Unternehmen',
            
            # Status messages and errors
            'ride_added_successfully': 'Fahrt erfolgreich hinzugefügt',
            'ride_updated_successfully': 'Fahrt erfolgreich aktualisiert',
            'ride_deleted_successfully': 'Fahrt erfolgreich gelöscht',
            'driver_added_successfully': 'Fahrer erfolgreich hinzugefügt',
            'driver_updated_successfully': 'Fahrer erfolgreich aktualisiert',
            'driver_deleted_successfully': 'Fahrer erfolgreich gelöscht',
            'failed_to_add_ride': 'Fehler beim Hinzufügen der Fahrt',
            'failed_to_edit_ride': 'Fehler beim Bearbeiten der Fahrt',
            'failed_to_delete_ride': 'Fehler beim Löschen der Fahrt',
            'failed_to_add_driver': 'Fehler beim Hinzufügen des Fahrers',
            'failed_to_edit_driver': 'Fehler beim Bearbeiten des Fahrers',
            'failed_to_delete_driver': 'Fehler beim Löschen des Fahrers',
            'failed_to_load_rides': 'Fehler beim Laden der Fahrten',
            'failed_to_load_drivers': 'Fehler beim Laden der Fahrer',
            'ride_not_found': 'Fahrt nicht gefunden',
            'driver_not_found': 'Fahrer nicht gefunden',
            'confirm_delete_driver': 'Fahrer löschen bestätigen',
            'driver_has_rides': 'Dieser Fahrer hat {} Fahrten',
            'deleting_driver_warning': 'Das Löschen des Fahrers hat keine Auswirkungen auf die Fahrten',
            'error_loading_stats': 'Fehler beim Laden der Statistiken',
            'error_loading_db_info': 'Fehler beim Laden der Datenbankinformationen',
            'today_revenue': 'Heutiger Umsatz',
            'unknown_operation': 'Unbekannte Operation',
            
            # Table headers and data
            'distance_km': 'Entfernung (km)',
            'duration_minutes': 'Dauer (Min.)',
            'pickup_time': 'Abholzeit',
            'pickup_location': 'Abholort',
            'destination': 'Zielort',
            'vehicle': 'Fahrzeug',
            'name': 'Name',
            
            # Button labels and operations that were missing
            'add_record': 'Datensatz hinzufügen',
            'edit_record': 'Datensatz bearbeiten',
            'delete_record': 'Datensatz löschen',
            'refresh': 'Aktualisieren',
            'clear_all': 'Alle löschen',
            'apply_filters': 'Filter anwenden',
            'record_operations': 'Datensatzoperationen',
            
            # Summary and filter labels
            'summary': 'Zusammenfassung',
            'filters': 'Filter',
            'total_rides': 'Fahrten gesamt',
            'active_drivers': 'Aktive Fahrer',
            'violations': 'Verstöße',
            'compliance': 'Konformität',
            'all_drivers': 'Alle Fahrer',
            'all_status': 'Alle Status',
            'from': 'Von',
            'to': 'Bis',
            
            # Ride-related translations
            'vehicle_plate': 'Kennzeichen',
            'route': 'Route',
            'status': 'Status',
            'revenue': 'Umsatz',
            'unknown': 'Unbekannt',
            
            # Status values
            'pending': 'Ausstehend',
            'in_progress': 'In Bearbeitung',
            'completed': 'Abgeschlossen',
            'violation': 'Verstoß',
            'imported': 'Importiert',
            'cancelled': 'Storniert',
            'active': 'Aktiv',
            'inactive': 'Inaktiv',
            
            # Dialog and action translations
            'save': 'Speichern',
            'cancel': 'Abbrechen',
            'success': 'Erfolg',
            'error': 'Fehler',
            'warning': 'Warnung',
            'view_ride_details': 'Fahrtdetails anzeigen',
            'select_ride_to_edit': 'Wählen Sie eine Fahrt zum Bearbeiten aus',
            'select_ride_to_delete': 'Wählen Sie eine Fahrt zum Löschen aus',
            'confirm_delete': 'Löschen bestätigen',
            'confirm_delete_ride': 'Fahrt löschen bestätigen',
            'for_driver': 'für Fahrer',
            'confirm_clear_all': 'Alle löschen bestätigen',
            'confirm_clear_all_rides': 'Sind Sie sicher, dass Sie alle Fahrten löschen möchten?',
            'all_rides_cleared': 'Alle Fahrten wurden gelöscht',
            'failed_to_clear_rides': 'Fehler beim Löschen der Fahrten',
            
            # Fahrtenbuch (Logbook) Export
            'Logbook': 'Fahrtenbuch',
            'Timesheet': 'Stundenzettel',
            'Employee': 'Mitarbeiter',
            'Personnel Number': 'Personalnummer',
            'Company': 'Unternehmen',
            'Vehicle': 'Fahrzeug',
            'Plate Number': 'Kennzeichen',
            'Driver': 'Fahrer',
            'Date': 'Datum',
            'Time': 'Uhrzeit',
            'Start': 'Fahrtbeginn',
            'End': 'Fahrtende',
            'Start Date/Time': 'Datum/Uhrzeit Schichtbeginn',
            'End Date/Time': 'Datum/Uhrzeit Schichtende',
            'Pickup Location': 'Abholort',
            'Destination': 'Zielort',
            'Location of Job Assignment': 'Standort des Fahrzeugs bei Auftragsübermittlung',
            'Reserve': 'Reserve',
            'Is Reserve': 'Ist Reserve',
            'Distance': 'gefahrene Kilometer',
            'Kilometers': 'Kilometer',
            'Vehicle Plate': 'Kennzeichen',
            'Activity': 'Tätigkeit',
            'Shift': 'Schicht',
            'Total Work Time': 'Gesamte Arbeitszeit',
            'Break Time': 'Pause (Min.)',
            'Actual Work Time': 'Reale Arbeitszeit',
            'Early Shift': 'Frühschicht',
            'Night Shift': 'Nachtschicht',
            'Hours': 'Std.',
            'Total Work Time (Month/Hours)': 'Gesamte Arbeitszeit (Monat/Std.)',
            'Total Work Time (Early Shift, Month/Hours)': 'Gesamte Arbeitszeit (Frühschicht, Monat/Std.)',
            'Total Work Time (Night Shift, Month/Hours)': 'Gesamte Arbeitszeit (Nachtschicht, Monat/Std.)',
            'Total Gross Wage': 'Gesamtbruttolohn',
            'Hourly Wage': 'Stundenlohn',
            'Night Supplement': 'Nachtzuschlag',
            'Employee Signature': 'Unterschrift Mitarbeiter',
            'Supervisor Signature': 'Unterschrift Vorgesetzter',
            'Notes': 'Notizen',
            'Company Location:': 'Betriebssitz des Unternehmens:',
            
            # Export functionality
            'Export Logbook': 'Fahrtenbuch exportieren',
            'Export to Excel': 'Nach Excel exportieren',
            'Export to PDF': 'Nach PDF exportieren',
            'Export Timesheet': 'Stundenzettel exportieren',
            'Select Date Range': 'Datumsbereich auswählen',
            'From': 'Von',
            'To': 'Bis',
            'Select Driver': 'Fahrer auswählen',
            'All Drivers': 'Alle Fahrer',
            'Current Month (Excel)': 'Aktueller Monat (Excel)',
            'Last Month (Excel)': 'Letzter Monat (Excel)',
            'Current Month (PDF)': 'Aktueller Monat (PDF)',
            'Last Month (PDF)': 'Letzter Monat (PDF)',
            'Advanced Export Options': 'Erweiterte Export-Optionen',
            
            # Buttons and common actions
            'Yes': 'Ja',
            'No': 'Nein',
            'OK': 'OK',
            'Cancel': 'Abbrechen',
            'Save': 'Speichern',
            'Delete': 'Löschen',
            'Edit': 'Bearbeiten',
            'Add': 'Hinzufügen',
            'Close': 'Schließen',
            'Export': 'Exportieren',
            'Import': 'Importieren',
            'Print': 'Drucken',
            'Settings': 'Einstellungen',
            'Help': 'Hilfe',
            'About': 'Über',
            'File': 'Datei',
            'Open': 'Öffnen',
            'Start Export': 'Export starten',
            'Refresh': 'Aktualisieren',
            'Apply Filters': 'Filter anwenden',
            'Clear All': 'Alle löschen',
            
            # Status and messages
            'Error': 'Fehler',
            'Warning': 'Warnung',
            'Information': 'Information',
            'Success': 'Erfolg',
            'Loading...': 'Laden...',
            'Processing...': 'Verarbeitung...',
            'Export completed successfully': 'Export erfolgreich abgeschlossen',
            'Export failed': 'Export fehlgeschlagen',
            'No data found for selected criteria': 'Keine Daten für die ausgewählten Kriterien gefunden',
            'Please select a valid date range': 'Bitte wählen Sie einen gültigen Datumsbereich',
            
            # Common fields
            'Name': 'Name',
            'Address': 'Adresse',
            'Phone': 'Telefon',
            'Email': 'E-Mail',
            'Status': 'Status',
            'Active': 'Aktiv',
            'Inactive': 'Inaktiv',
            'Available': 'Verfügbar',
            'In Use': 'In Benutzung',
            'Maintenance': 'Wartung',
            'Make': 'Marke',
            'Model': 'Modell',
            'Year': 'Jahr',
            'Color': 'Farbe',
            'Total KM': 'Gesamtkilometer',
            'Last Maintenance Date': 'Letztes Wartungsdatum',
            
            # Analytics / Chart View specific
            'km_per_driver_chart_title': 'Kilometer pro Fahrer',
            'save_chart': 'Als PNG speichern',
            'save_chart_tooltip': 'Diagramm als PNG-Bild speichern',
            'chart_data_error': 'Fehler beim Laden der Diagrammdaten.',
            'no_data_for_chart': 'Keine Daten für den ausgewählten Zeitraum verfügbar.',
            'period_chart_title': 'Zeitraum: {start_date} – {end_date}',
            'save_chart_dialog_title': 'Diagramm speichern unter...',
            'image_files_filter': 'PNG-Bilder (*.png)',
            'analyse_filter_title': 'Filter & Optionen',
            'analyse_start_date': 'Startdatum:',
            'analyse_end_date': 'Enddatum:',
            'analyse_refresh_button': 'Aktualisieren',
            'date_error_title': 'Datumsfehler',
            'date_error_message_start_after_end': 'Das Startdatum darf nicht nach dem Enddatum liegen.',
            
            # Data Import
            'Import Mode:': 'Import-Modus:',
            'Validate and Import': 'Validieren und Importieren',
            'Start Import': 'Import starten',
            'Import Failed': 'Import fehlgeschlagen',
            'Validation Errors/Issues:': 'Validierungsfehler/Probleme:',
            'Missing required columns:': 'Fehlende erforderliche Spalten:',
            'Driver Name, Date/Time, Pickup Address, Destination, Vehicle Plate': 'Fahrername, Datum/Uhrzeit, Abholadresse, Ziel, Fahrzeugkennzeichen',
            'Select Excel File (.xlsx, .xls)': 'Excel-Datei auswählen (.xlsx, .xls)',
            'Excel File:': 'Excel-Datei:',
            
            # Rules and compliance
            'Compliance': 'Konformität',
            'Violations': 'Verstöße',
            'Revenue': 'Umsatz',
            'Rule': 'Regel',
            'Description': 'Beschreibung',
            'Value': 'Wert',
            'Enabled': 'Aktiviert',
            
            # Driver/Vehicle management  
            'Add New Driver': 'Neuen Fahrer hinzufügen',
            'Add New Vehicle': 'Neues Fahrzeug hinzufügen',
            'Driver Name': 'Fahrername',
            'Enter driver\'s full name': 'Vollständigen Namen des Fahrers eingeben',
            'Total Drivers': 'Fahrer gesamt',
            'Total Rides': 'Fahrten gesamt',
            'Add Driver': '+ Fahrer hinzufügen',
            'Driver Management': 'Fahrerverwaltung',
            'Add, edit, and monitor driver performance': 'Fahrer hinzufügen, bearbeiten und Leistung überwachen',
            'Shift': 'Schicht',
            'Rides': 'Fahrten',
            'Earnings': 'Verdienst',
            
            # Additional German translations for Drivers View
            'Fahrer hinzufügen': 'Fahrer hinzufügen',
            'Name des Fahrers': 'Name des Fahrers',
            'Vollständigen Namen des Fahrers eingeben': 'Vollständigen Namen des Fahrers eingeben',
            'Fahrzeugnummer': 'Fahrzeugnummer',
            'z.B.: ABC-1234': 'z.B.: ABC-1234',
            'Aktiv': 'Aktiv',
            'Inaktiv': 'Inaktiv',
            'Abbrechen': 'Abbrechen',
            'Fahrzeug hinzufügen': 'Fahrzeug hinzufügen',
            'Kennzeichen': 'Kennzeichen',
            'Geben Sie die Fahrzeugnummer ein': 'Geben Sie die Fahrzeugnummer ein',
            'z.B., B-TX 1234': 'z.B., B-TX 1234',
            'Marke': 'Marke',
            'Fahrzeughersteller': 'Fahrzeughersteller',
            'z.B., Toyota, BMW, Mercedes': 'z.B., Toyota, BMW, Mercedes',
            'Modell': 'Modell',
            'Fahrzeugmodell': 'Fahrzeugmodell',
            'z.B., Camry, X5, E-Klasse': 'z.B., Camry, X5, E-Klasse',
            'Baujahr': 'Baujahr',
            'Farbe': 'Farbe',
            'Fahrzeugfarbe': 'Fahrzeugfarbe',
            'z.B., Weiß, Schwarz, Rot': 'z.B., Weiß, Schwarz, Rot',
            'Verfügbar': 'Verfügbar',
            'In Benutzung': 'In Benutzung',
            'Wartung': 'Wartung',
            'Gesamt KM': 'Gesamt KM',
            'Letztes Wartungsdatum': 'Letztes Wartungsdatum',
            'Fahrer- und Fahrzeugverwaltung': 'Fahrer- und Fahrzeugverwaltung',
            'Verwalten Sie Fahrer, Fahrzeuge und verfolgen Sie Leistungskennzahlen': 'Verwalten Sie Fahrer, Fahrzeuge und verfolgen Sie Leistungskennzahlen',
            'Fahrer': 'Fahrer',
            'Fahrzeuge': 'Fahrzeuge',
            'Gesamtfahrer': 'Gesamtfahrer',
            'Gesamtfahrten': 'Gesamtfahrten',
            'Fahrerverwaltung': 'Fahrerverwaltung',
            'Fügen Sie Fahrer hinzu, bearbeiten Sie sie und überwachen Sie die Leistung': 'Fügen Sie Fahrer hinzu, bearbeiten Sie sie und überwachen Sie die Leistung',
            'Fahrer hinzufügen': 'Fahrer hinzufügen',
            'Schicht': 'Schicht',
            'Stunden': 'Stunden',
            'Fahrten': 'Fahrten',
            'Einnahmen': 'Einnahmen',
            'Verstöße': 'Verstöße',
            'Gesamtfahrzeuge': 'Gesamtfahrzeuge',
            'Fahrzeugflottenverwaltung': 'Fahrzeugflottenverwaltung',
            'Überwachen Sie den Fahrzeugstatus, die Wartung und die Zuordnungen': 'Überwachen Sie den Fahrzeugstatus, die Wartung und die Zuordnungen',
            'Fahrzeug hinzufügen': 'Fahrzeug hinzufügen',
            'Marke/Modell': 'Marke/Modell',
            'Letzte Wartung': 'Letzte Wartung',
            'Zugew. Fahrer': 'Zugew. Fahrer',

            # Drivers & Vehicles Management Page
            'Drivers & Vehicles Management': 'Fahrer- und Fahrzeugverwaltung',
            'Manage drivers, vehicles, and track performance metrics': 'Fahrer und Fahrzeuge verwalten sowie Leistungsmetriken verfolgen',
            'Total Vehicles': 'Fahrzeuge gesamt',
            'Vehicle Fleet Management': 'Fuhrparkverwaltung',
            'Monitor vehicle status, maintenance and assignments': 'Fahrzeugstatus, Wartung und Zuweisungen überwachen',
            'Add Vehicle': '+ Fahrzeug hinzufügen',
            
            # Table Headers
            'Vehicle': 'Fahrzeug',
            'Violations': 'Verstöße',
            'Make/Model': 'Marke/Modell',
            'Last Maintenance': 'Letzte Wartung',
            'Assigned Driver': 'Zugewiesener Fahrer',
            
            # Vehicle Dialog
            'Enter vehicle plate number': 'Fahrzeugkennzeichen eingeben',
            'e.g., ABC-1234': 'z.B. ABC-1234',
            'e.g., B-TX 1234': 'z.B. B-TX 1234',
            'Vehicle manufacturer': 'Fahrzeughersteller',
            'e.g., Toyota, BMW, Mercedes': 'z.B. Toyota, BMW, Mercedes',
            'Vehicle model': 'Fahrzeugmodell',
            'e.g., Camry, X5, E-Class': 'z.B. Camry, X5, E-Klasse',
            'Vehicle color': 'Fahrzeugfarbe',
            'e.g., White, Black, Red': 'z.B. Weiß, Schwarz, Rot',
            
            # Status and Messages
            'Success': 'Erfolg',
            'Driver added successfully!': 'Fahrer erfolgreich hinzugefügt!',
            'Vehicle added successfully!': 'Fahrzeug erfolgreich hinzugefügt!',
            'Invalid Input': 'Ungültige Eingabe',
            'Driver name is required.': 'Fahrername ist erforderlich.',
            'Plate number is required.': 'Kennzeichen ist erforderlich.',
            'Database Error': 'Datenbankfehler',
            'Failed to add driver': 'Fehler beim Hinzufügen des Fahrers',
            'Failed to add vehicle': 'Fehler beim Hinzufügen des Fahrzeugs',
            'Failed to load drivers': 'Fehler beim Laden der Fahrer',
            'Failed to load vehicles data': 'Fehler beim Laden der Fahrzeugdaten',
            'Duplicate Entry': 'Doppelter Eintrag',
            'A vehicle with this plate number already exists.': 'Ein Fahrzeug mit diesem Kennzeichen existiert bereits.',
            'No Database': 'Keine Datenbank',
            'Database connection not available.': 'Datenbankverbindung nicht verfügbar.',
            'No Vehicle': 'Kein Fahrzeug',
            'Day': 'Tag',
            'N/A': 'N/V',
            
            # Launcher-specific translations
            'choose_application_version': 'Wählen Sie die Anwendungsversion',
            'select_version': 'Version auswählen',
            'single_company_mode': 'Einzelunternehmen-Modus',
            'multi_company_mode': 'Mehrfachunternehmen-Modus',
            'description': 'Beschreibung',
            'options': 'Optionen',
            'remember_choice': 'Auswahl merken',
            'remember_choice_tooltip': 'Diese Auswahl für zukünftige Starts speichern',
            'show_detailed_info': 'Detaillierte Informationen anzeigen',
            'help': 'Hilfe',
            'launch_application': 'Anwendung starten',
            'launching': 'Wird gestartet...',
            'launch_error': 'Startfehler',
            'close': 'Schließen',
            
            # Version descriptions
            'single_company_description': 'Vereinfachte Benutzeroberfläche für die Verwaltung eines einzelnen Unternehmens. Automatische Einrichtung und optimierte Navigation.',
            'multi_company_description': 'Erweiterte Benutzeroberfläche für die Verwaltung mehrerer Unternehmen. Vollständige Unternehmensverwaltung und Datentrennung.',
            'single_company_best_for': 'Kleine Taxiunternehmen und individuelle Flottenoperatoren',
            'multi_company_best_for': 'Flottenmanagement-Unternehmen und Multi-Standort-Betriebe',
            
            # Detailed feature descriptions
            'ideal_for': 'Ideal für',
            'features': 'Funktionen',
            'best_for': 'Am besten geeignet für',
            'small_taxi_companies': 'Kleine Taxiunternehmen',
            'individual_fleet_operators': 'Individuelle Flottenoperatoren',
            'simple_fleet_management': 'Einfaches Flottenmanagement',
            'simplified_interface': 'Vereinfachte Benutzeroberfläche',
            'automatic_company_setup': 'Automatische Unternehmenseinrichtung',
            'all_standard_features': 'Alle Standardfunktionen verfügbar',
            'fleet_management_companies': 'Flottenmanagement-Unternehmen',
            'multi_location_operations': 'Multi-Standort-Betriebe',
            'consulting_firms': 'Beratungsunternehmen',
            'company_selection_dialog': 'Unternehmensauswahl-Dialog',
            'full_company_management': 'Vollständige Unternehmensverwaltung',
            'data_isolation': 'Datentrennung zwischen Unternehmen',
            
            # Help dialog content
            'help_title': 'Ride Guardian Desktop - Hilfe',
            'version_comparison': 'Versionsvergleich',
            'feature': 'Funktion',
            'single_company': 'Einzelunternehmen',
            'multi_company': 'Mehrfachunternehmen',
            'complexity': 'Komplexität',
            'simple': 'Einfach',
            'advanced': 'Erweitert',
            'company_management': 'Unternehmensverwaltung',
            'automatic': 'Automatisch',
            'full_control': 'Vollständige Kontrolle',
            'data_separation': 'Datentrennung',
            'single_dataset': 'Ein Datensatz',
            'isolated_per_company': 'Getrennt pro Unternehmen',
            'switching_companies': 'Unternehmen wechseln',
            'not_available': 'Nicht verfügbar',
            'available': 'Verfügbar',
            'getting_started': 'Erste Schritte',
            'help_getting_started': 'Wählen Sie die Version, die am besten zu Ihren Anforderungen passt. Einzelunternehmen-Modus für einfache Bedienung, Mehrfachunternehmen-Modus für erweiterte Funktionen.',
            'need_help': 'Benötigen Sie Hilfe?',
            'help_contact_info': 'Weitere Unterstützung finden Sie in der Dokumentation oder kontaktieren Sie den Support.',
        }
    
    def tr(self, text: str) -> str:
        """Translate text to German"""
        if self.current_language == 'de':
            return self.translations.get(text, text)
        return text
    
    def load_qt_translations(self, app):
        """Load Qt translation files"""
        try:
            # Load application-specific translations
            app_translator = QTranslator()
            translation_file = os.path.join(
                os.path.dirname(__file__), '..', 'translations', 'ride_guardian_de.qm'
            )
            
            if os.path.exists(translation_file):
                if app_translator.load(translation_file):
                    app.installTranslator(app_translator)
                    self.translators.append(app_translator)
                    print("German application translations loaded successfully")
                else:
                    print("Failed to load German application translations")
            else:
                print(f"Translation file not found: {translation_file}")
            
            # Load Qt system translations
            qt_translator = QTranslator()
            qt_path = os.path.join(
                os.path.dirname(__file__), '..', 'venv', 'lib', 
                'python3.13', 'site-packages', 'PyQt6', 'Qt6', 'translations'
            )
            
            qt_files = ['qtbase_de.qm', 'qt_de.qm']
            
            for qt_file in qt_files:
                qt_file_path = os.path.join(qt_path, qt_file)
                if os.path.exists(qt_file_path):
                    if qt_translator.load(qt_file_path):
                        app.installTranslator(qt_translator)
                        self.translators.append(qt_translator)
                        print(f"Qt system translations loaded: {qt_file}")
                        break
            
        except Exception as e:
            print(f"Error loading translations: {e}")
    
    def get_fahrtenbuch_headers(self) -> list:
        """Get Fahrtenbuch table headers in German"""
        return [
            'Datum\nFahrtbeginn',
            'Uhrzeit\nFahrtbeginn', 
            'Standort des Fahrzeugs bei\nAuftragsübermittlung',
            'Ist\nReserve',
            'Abholort',
            'Zielort',
            'gefahrene\nKilometer',
            'Datum\nFahrtende',
            'Uhrzeit\nFahrtende',
            'Fahrtende',
            'Kennzeichen'
        ]
    
    def get_stundenzettel_headers(self) -> list:
        """Get Stundenzettel table headers in German"""
        return [
            'Schicht\nID',
            'Tätigkeit',
            'Datum/Uhrzeit\nSchichtbeginn',
            'Datum/Uhrzeit\nSchichtende',
            'Gesamte Arbeitszeit\n(Std.)',
            'Pause\n(Min.)',
            'Reale Arbeitszeit\n(Std.)',
            'Frühschicht\n(Std.)',
            'Nachtschicht\n(Std.)'
        ]
    
    def get_company_info_labels(self) -> dict:
        """Get company information labels in German"""
        return {
            'company_location': 'Betriebssitz des Unternehmens:',
            'vehicle': 'Fahrzeug',
            'license_plate': 'Kennzeichen',
            'driver': 'Fahrer',
            'personnel_number': 'Personalnummer'
        }
    
    def format_boolean_german(self, value: bool) -> str:
        """Format boolean values in German"""
        return 'Ja' if value else 'Nein'
    
    def format_date_german(self, date_str: str) -> str:
        """Format date in German format (DD.MM.YYYY)"""
        try:
            from datetime import datetime
            if isinstance(date_str, str):
                # Try parsing ISO format first
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.strftime('%d.%m.%Y')
                except:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y']:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            return dt.strftime('%d.%m.%Y')
                        except:
                            continue
            return date_str
        except:
            return date_str
    
    def format_time_german(self, time_str: str) -> str:
        """Format time in German format (HH:MM)"""
        try:
            from datetime import datetime
            if isinstance(time_str, str):
                # Try parsing ISO format first
                try:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    return dt.strftime('%H:%M')
                except:
                    # Try other common formats
                    for fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p']:
                        try:
                            dt = datetime.strptime(time_str, fmt)
                            return dt.strftime('%H:%M')
                        except:
                            continue
            return time_str
        except:
            return time_str

# Global translation manager instance
translation_manager = TranslationManager()

def tr(text: str) -> str:
    """Global translation function"""
    return translation_manager.tr(text)