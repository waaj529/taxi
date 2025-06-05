"""
API Cache Indicator Component
Shows visual feedback for Google Maps API cache hits/misses
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QGridLayout, QProgressBar, QTextEdit, QSplitter, QHeaderView,
    QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from typing import Dict, List
from core.google_maps import GoogleMapsIntegration
from core.translation_manager import tr, TranslationManager


class CacheOptimizationThread(QThread):
    """Thread für Cache-Optimierung im Hintergrund"""
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, int)
    
    def __init__(self, operation_type):
        super().__init__()
        self.operation_type = operation_type
    
    def run(self):
        try:
            self.status_update.emit("Initialisiere Google Maps Integration...")
            self.progress.emit(10)
            
            gm = GoogleMapsIntegration()
            
            if self.operation_type == "optimize":
                self.status_update.emit("Optimiere Cache...")
                self.progress.emit(50)
                deleted_entries = gm.optimize_cache()
                self.progress.emit(100)
                self.finished_signal.emit(True, f"Cache optimiert: {deleted_entries} alte Einträge entfernt", deleted_entries)
            
            elif self.operation_type == "clear":
                self.status_update.emit("Lösche Cache...")
                self.progress.emit(50)
                gm.clear_cache()
                self.progress.emit(100)
                self.finished_signal.emit(True, "Cache vollständig geleert", 0)
                
        except Exception as e:
            self.finished_signal.emit(False, f"Fehler bei Cache-Operation: {str(e)}", 0)

class APICacheIndicator(QWidget):
    """Visual indicator for API cache status"""
    
    # Signal emitted when cache statistics change
    cache_stats_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_hits = 0
        self.cache_misses = 0
        self.recent_requests: List[Dict] = []
        self.init_ui()
        
        # Timer to clear old indicators
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.clear_old_indicators)
        self.clear_timer.start(5000)  # Clear indicators older than 5 seconds
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Cache status label
        self.status_label = QLabel(tr("API Cache") + ":")
        layout.addWidget(self.status_label)
        
        # Hit indicator
        self.hit_indicator = self.create_indicator("#28a745", tr("Cache Hit"))
        layout.addWidget(self.hit_indicator)
        
        # Miss indicator
        self.miss_indicator = self.create_indicator("#dc3545", tr("API Request"))
        layout.addWidget(self.miss_indicator)
        
        # Stats label
        self.stats_label = QLabel()
        self.update_stats_display()
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
    def create_indicator(self, color: str, tooltip: str) -> QFrame:
        """Create a colored indicator dot"""
        indicator = QFrame()
        indicator.setFixedSize(12, 12)
        indicator.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 6px;
                opacity: 0.3;
            }}
        """)
        indicator.setToolTip(tooltip)
        indicator.hide()
        return indicator
        
    def record_cache_hit(self, location: str = ""):
        """Record a cache hit"""
        self.cache_hits += 1
        self.recent_requests.append({
            'type': 'hit',
            'time': datetime.now(),
            'location': location
        })
        self.flash_indicator(self.hit_indicator)
        self.update_stats_display()
        
    def record_cache_miss(self, location: str = ""):
        """Record a cache miss (API request)"""
        self.cache_misses += 1
        self.recent_requests.append({
            'type': 'miss',
            'time': datetime.now(),
            'location': location
        })
        self.flash_indicator(self.miss_indicator)
        self.update_stats_display()
        
    def flash_indicator(self, indicator: QFrame):
        """Flash an indicator briefly"""
        indicator.show()
        indicator.setStyleSheet(indicator.styleSheet().replace("opacity: 0.3", "opacity: 1.0"))
        
        # Fade out after 1 second
        QTimer.singleShot(1000, lambda: self.fade_indicator(indicator))
        
    def fade_indicator(self, indicator: QFrame):
        """Fade out an indicator"""
        if indicator.isVisible():
            indicator.setStyleSheet(indicator.styleSheet().replace("opacity: 1.0", "opacity: 0.3"))
            QTimer.singleShot(1000, lambda: indicator.hide())
            
    def update_stats_display(self):
        """Update the statistics display"""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            hit_rate = (self.cache_hits / total) * 100
            self.stats_label.setText(
                f"{tr('Hits')}: {self.cache_hits} | "
                f"{tr('Requests')}: {self.cache_misses} | "
                f"{tr('Hit Rate')}: {hit_rate:.1f}%"
            )
        else:
            self.stats_label.setText(tr("No API calls yet"))
            
        # Emit signal with statistics
        self.cache_stats_updated.emit({
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate if total > 0 else 0,
            'recent_requests': self.recent_requests[-10:]  # Last 10 requests
        })
        
    def clear_old_indicators(self):
        """Clear requests older than 1 minute"""
        current_time = datetime.now()
        self.recent_requests = [
            req for req in self.recent_requests
            if (current_time - req['time']).seconds < 60
        ]
        
    def reset_stats(self):
        """Reset all statistics"""
        self.cache_hits = 0
        self.cache_misses = 0
        self.recent_requests.clear()
        self.update_stats_display()
        
    def get_stats(self) -> Dict:
        """Get current cache statistics"""
        total = self.cache_hits + self.cache_misses
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total': total,
            'hit_rate': (self.cache_hits / total * 100) if total > 0 else 0,
            'recent_requests': self.recent_requests
        }


class APICacheStatusWidget(QWidget):
    """Detailed API cache status widget for reports/monitoring"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Create frame with border
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame_layout = QHBoxLayout(frame)
        
        # Icon/Status indicator
        self.status_icon = QLabel("🔄")
        self.status_icon.setStyleSheet("font-size: 20px;")
        frame_layout.addWidget(self.status_icon)
        
        # Status text
        self.status_text = QLabel(tr("API Cache Active"))
        self.status_text.setStyleSheet("font-weight: bold;")
        frame_layout.addWidget(self.status_text)
        
        # Cache indicator
        self.cache_indicator = APICacheIndicator()
        frame_layout.addWidget(self.cache_indicator)
        
        layout.addWidget(frame)
        
    def update_status(self, is_active: bool, message: str = ""):
        """Update the cache status display"""
        if is_active:
            self.status_icon.setText("✅")
            self.status_text.setText(message or tr("API Cache Active"))
            self.status_text.setStyleSheet("font-weight: bold; color: #28a745;")
        else:
            self.status_icon.setText("❌")
            self.status_text.setText(message or tr("API Cache Inactive"))
            self.status_text.setStyleSheet("font-weight: bold; color: #dc3545;")
            
    def get_cache_indicator(self) -> APICacheIndicator:
        """Get the cache indicator component"""
        return self.cache_indicator


class ApiCacheIndicatorWidget(QWidget):
    """
    Verbesserte Cache-Anzeige-Widget mit detaillierten Statistiken und Verwaltungsfunktionen
    Ähnlich dem Excel-System für Google Maps API-Effizienz
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gm = GoogleMapsIntegration()
        self.tm = TranslationManager()
        
        self.init_ui()
        self.refresh_cache_data()
        
        # Auto-Refresh alle 30 Sekunden
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_cache_data)
        self.refresh_timer.start(30000)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📊 Google Maps API Cache Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # Refresh Button
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self.refresh_cache_data)
        header_layout.addWidget(refresh_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Main content in splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Statistics
        stats_panel = self.create_statistics_panel()
        splitter.addWidget(stats_panel)
        
        # Right panel: Cache details
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Cache-Daten werden geladen...")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-top: 1px solid #ddd;")
        layout.addWidget(self.status_label)
    
    def create_statistics_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cache-Effizienz-Gruppe
        efficiency_group = QGroupBox("🎯 Cache-Effizienz")
        efficiency_layout = QGridLayout(efficiency_group)
        
        self.efficiency_labels = {}
        
        # Sitzungsstatistiken
        session_group = QGroupBox("📈 Aktuelle Sitzung")
        session_layout = QGridLayout(session_group)
        
        self.session_labels = {}
        
        # Gesamtstatistiken
        total_group = QGroupBox("📊 Gesamtstatistiken")
        total_layout = QGridLayout(total_group)
        
        self.total_labels = {}
        
        # Kosteneinsparungen
        cost_group = QGroupBox("💰 Kosteneinsparungen")
        cost_layout = QGridLayout(cost_group)
        
        self.cost_labels = {}
        
        layout.addWidget(efficiency_group)
        layout.addWidget(session_group)
        layout.addWidget(total_group)
        layout.addWidget(cost_group)
        
        # Cache-Verwaltungsbuttons
        management_group = QGroupBox("🔧 Cache-Verwaltung")
        management_layout = QVBoxLayout(management_group)
        
        optimize_btn = QPushButton("🗂️ Cache optimieren")
        optimize_btn.clicked.connect(lambda: self.manage_cache("optimize"))
        optimize_btn.setToolTip("Entfernt alte, selten genutzte Cache-Einträge")
        management_layout.addWidget(optimize_btn)
        
        clear_btn = QPushButton("🗑️ Cache leeren")
        clear_btn.clicked.connect(lambda: self.manage_cache("clear"))
        clear_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        clear_btn.setToolTip("Löscht alle Cache-Einträge (Vorsicht!)")
        management_layout.addWidget(clear_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        management_layout.addWidget(self.progress_bar)
        
        self.operation_status = QLabel("")
        self.operation_status.setVisible(False)
        management_layout.addWidget(self.operation_status)
        
        layout.addWidget(management_group)
        layout.addStretch()
        
        return widget
    
    def create_details_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Top Routes Table
        routes_group = QGroupBox("🚗 Top wiederverwendete Routen")
        routes_layout = QVBoxLayout(routes_group)
        
        self.routes_table = QTableWidget()
        self.routes_table.setAlternatingRowColors(True)
        self.routes_table.horizontalHeader().setStretchLastSection(True)
        routes_layout.addWidget(self.routes_table)
        
        layout.addWidget(routes_group)
        
        # Cache Log
        log_group = QGroupBox("📝 Cache-Aktivitätsprotokoll")
        log_layout = QVBoxLayout(log_group)
        
        self.cache_log = QTextEdit()
        self.cache_log.setMaximumHeight(200)
        self.cache_log.setReadOnly(True)
        log_layout.addWidget(self.cache_log)
        
        clear_log_btn = QPushButton("Protokoll löschen")
        clear_log_btn.clicked.connect(self.cache_log.clear)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        return widget
    
    def refresh_cache_data(self):
        """Aktualisiere alle Cache-Daten und Statistiken"""
        try:
            # Detaillierte Statistiken abrufen
            stats = self.gm.get_cache_efficiency_stats()
            
            # Effizienz-Statistiken aktualisieren
            self.update_efficiency_stats(stats)
            
            # Sitzungsstatistiken aktualisieren
            self.update_session_stats(stats)
            
            # Gesamtstatistiken aktualisieren
            self.update_total_stats(stats)
            
            # Kosteneinsparungen aktualisieren
            self.update_cost_stats(stats)
            
            # Top-Routen-Tabelle aktualisieren
            self.update_routes_table(stats['top_wiederverwendete_routen'])
            
            # Protokoll aktualisieren
            current_time = datetime.now().strftime("%H:%M:%S")
            efficiency = stats.get('sitzung_cache_effizienz_prozent', 0)
            self.cache_log.append(f"[{current_time}] Cache aktualisiert - Effizienz: {efficiency}%")
            
            # Status aktualisieren
            total_entries = stats.get('gesamt_zwischengespeicherte_routen', 0)
            total_uses = stats.get('gesamt_cache_verwendungen', 0)
            self.status_label.setText(f"✓ Cache aktiv: {total_entries} Routen gespeichert, {total_uses} Verwendungen")
            
        except Exception as e:
            self.status_label.setText(f"❌ Fehler beim Laden der Cache-Daten: {str(e)}")
            self.cache_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Fehler: {str(e)}")
    
    def update_efficiency_stats(self, stats):
        """Aktualisiere Effizienz-Statistiken"""
        efficiency = stats.get('sitzung_cache_effizienz_prozent', 0)
        
        # Effizienz-Farbe basierend auf Wert
        if efficiency >= 80:
            color = "#28a745"  # Grün
            icon = "🟢"
        elif efficiency >= 50:
            color = "#ffc107"  # Gelb
            icon = "🟡"
        else:
            color = "#dc3545"  # Rot
            icon = "🔴"
        
        # Labels aktualisieren (erstellen falls nicht vorhanden)
        efficiency_group = self.findChild(QGroupBox, "🎯 Cache-Effizienz")
        if efficiency_group:
            layout = efficiency_group.layout()
            
            # Clear existing widgets
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
            
            # Effizienz-Anzeige
            efficiency_label = QLabel(f"{icon} {efficiency}%")
            efficiency_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            layout.addWidget(QLabel("Cache-Effizienz:"), 0, 0)
            layout.addWidget(efficiency_label, 0, 1)
    
    def update_session_stats(self, stats):
        """Aktualisiere Sitzungsstatistiken"""
        session_group = self.findChild(QGroupBox, "📈 Aktuelle Sitzung")
        if session_group:
            layout = session_group.layout()
            
            # Clear existing widgets
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
            
            cache_hits = stats.get('sitzung_cache_treffer', 0)
            api_calls = stats.get('sitzung_api_aufrufe', 0)
            
            layout.addWidget(QLabel("Cache-Treffer:"), 0, 0)
            layout.addWidget(QLabel(str(cache_hits)), 0, 1)
            
            layout.addWidget(QLabel("API-Aufrufe:"), 1, 0)
            layout.addWidget(QLabel(str(api_calls)), 1, 1)
            
            layout.addWidget(QLabel("Gesamt-Anfragen:"), 2, 0)
            layout.addWidget(QLabel(str(cache_hits + api_calls)), 2, 1)
    
    def update_total_stats(self, stats):
        """Aktualisiere Gesamtstatistiken"""
        total_group = self.findChild(QGroupBox, "📊 Gesamtstatistiken")
        if total_group:
            layout = total_group.layout()
            
            # Clear existing widgets
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
            
            total_routes = stats.get('gesamt_zwischengespeicherte_routen', 0)
            total_uses = stats.get('gesamt_cache_verwendungen', 0)
            avg_reuse = stats.get('durchschnittliche_wiederverwendung', 0)
            
            layout.addWidget(QLabel("Gespeicherte Routen:"), 0, 0)
            layout.addWidget(QLabel(str(total_routes)), 0, 1)
            
            layout.addWidget(QLabel("Gesamtverwendungen:"), 1, 0)
            layout.addWidget(QLabel(str(total_uses)), 1, 1)
            
            layout.addWidget(QLabel("Ø Wiederverwendung:"), 2, 0)
            layout.addWidget(QLabel(f"{avg_reuse:.1f}x"), 2, 1)
    
    def update_cost_stats(self, stats):
        """Aktualisiere Kosteneinsparungsstatistiken"""
        cost_group = self.findChild(QGroupBox, "💰 Kosteneinsparungen")
        if cost_group:
            layout = cost_group.layout()
            
            # Clear existing widgets
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
            
            saved_calls = stats.get('geschaetzte_gesparte_api_aufrufe', 0)
            saved_costs = stats.get('geschaetzte_kosteneinsparung_euro', 0)
            
            layout.addWidget(QLabel("Gesparte API-Aufrufe:"), 0, 0)
            layout.addWidget(QLabel(str(saved_calls)), 0, 1)
            
            layout.addWidget(QLabel("Geschätzte Einsparung:"), 1, 0)
            cost_label = QLabel(f"€{saved_costs:.2f}")
            cost_label.setStyleSheet("color: #28a745; font-weight: bold;")
            layout.addWidget(cost_label, 1, 1)
    
    def update_routes_table(self, top_routes):
        """Aktualisiere die Top-Routen-Tabelle"""
        if not top_routes:
            self.routes_table.setRowCount(0)
            return
        
        columns = ["Von", "Nach", "Verwendungen", "Entfernung (km)", "Dauer (min)", "Letzte Nutzung"]
        self.routes_table.setColumnCount(len(columns))
        self.routes_table.setHorizontalHeaderLabels(columns)
        self.routes_table.setRowCount(len(top_routes))
        
        for row, route in enumerate(top_routes):
            self.routes_table.setItem(row, 0, QTableWidgetItem(route.get('origin_address', '')))
            self.routes_table.setItem(row, 1, QTableWidgetItem(route.get('destination_address', '')))
            self.routes_table.setItem(row, 2, QTableWidgetItem(str(route.get('use_count', 0))))
            
            distance = route.get('distance_km', 0)
            self.routes_table.setItem(row, 3, QTableWidgetItem(f"{distance:.2f}" if distance else "N/A"))
            
            duration = route.get('duration_minutes', 0)
            self.routes_table.setItem(row, 4, QTableWidgetItem(f"{duration:.1f}" if duration else "N/A"))
            
            last_used = route.get('last_used', '')
            if last_used:
                try:
                    dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    formatted_date = last_used
            else:
                formatted_date = "N/A"
            self.routes_table.setItem(row, 5, QTableWidgetItem(formatted_date))
        
        self.routes_table.resizeColumnsToContents()
    
    def manage_cache(self, operation):
        """Verwalte Cache-Operationen"""
        if operation == "clear":
            reply = QMessageBox.question(
                self, "Cache leeren",
                "Sind Sie sicher, dass Sie den gesamten Cache leeren möchten?\n\n"
                "Dies führt dazu, dass alle gespeicherten Routen gelöscht werden "
                "und neue Google Maps API-Aufrufe erforderlich sind.\n\n"
                "Diese Aktion kann nicht rückgängig gemacht werden.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        elif operation == "optimize":
            reply = QMessageBox.question(
                self, "Cache optimieren",
                "Cache optimieren?\n\n"
                "Dies entfernt alte, selten genutzte Cache-Einträge "
                "um Speicherplatz zu sparen.\n\n"
                "Häufig verwendete Routen bleiben erhalten.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Starte Cache-Operation im Hintergrund
        self.progress_bar.setVisible(True)
        self.operation_status.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.cache_thread = CacheOptimizationThread(operation)
        self.cache_thread.progress.connect(self.progress_bar.setValue)
        self.cache_thread.status_update.connect(self.operation_status.setText)
        self.cache_thread.finished_signal.connect(self.cache_operation_finished)
        self.cache_thread.start()
    
    def cache_operation_finished(self, success, message, affected_entries):
        """Cache-Operation abgeschlossen"""
        self.progress_bar.setVisible(False)
        self.operation_status.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Cache-Operation", message)
            current_time = datetime.now().strftime("%H:%M:%S")
            self.cache_log.append(f"[{current_time}] {message}")
            
            # Daten aktualisieren
            self.refresh_cache_data()
        else:
            QMessageBox.critical(self, "Fehler", message)
            self.cache_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Fehler: {message}")
    
    def closeEvent(self, event):
        """Widget wird geschlossen"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)