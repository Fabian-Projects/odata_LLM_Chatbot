"""
Calculation Engine
Orchestriert Berechnungen auf OData-Daten
Erweitert um Schicht- und Bereichsfilterung
"""

from typing import Dict, Any, List, Optional
from calculations.registry import get_registry

# Importiere neue Module (müssen im selben Verzeichnis sein)
try:
    from .shift_manager import ShiftManager
    from .area_filter import AreaFilter
except ImportError:
    # Fallback wenn Module nicht gefunden werden
    print("WARNUNG: shift_manager.py oder area_filter.py nicht gefunden!")
    ShiftManager = None
    AreaFilter = None


class CalculationEngine:
    """
    Haupt-Engine für Berechnungen
    Nimmt Rohdaten + Config und gibt Ergebnisse zurück
    """
    
    def __init__(self):
        self.registry = get_registry()
        
        # Initialisiere neue Manager
        self.shift_manager = ShiftManager() if ShiftManager else None
        self.area_filter = AreaFilter() if AreaFilter else None
    
    def process(
        self, 
        odata_result: Dict[str, Any], 
        calculation_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verarbeitet OData-Ergebnis mit optionaler Berechnung
        
        Args:
            odata_result: Response vom OData Client
                         {
                             "value": [...],
                             "count": 42,
                             "query_metadata": {...}
                         }
            
            calculation_config: Calculation Config vom Parser oder None
                               {
                                   "type": "count",
                                   "grouping_field": "group",
                                   "shift_filter": "früh" (optional),
                                   "area_filter": "Safelog" (optional),
                                   "detail_level": "basic" | "detailed" (optional)
                                   ...
                               }
        
        Returns:
            Dict mit Ergebnis (angereichert mit Schicht- und Bereichsinfo)
        """
        
        # Daten extrahieren
        raw_data = odata_result.get("value", [])
        
        # Reichere Daten mit Schicht-Informationen an
        if self.shift_manager:
            raw_data = self.shift_manager.add_shift_info_to_orders(raw_data)
        
        # Bereichsfilterung anwenden (falls gewünscht)
        if calculation_config and calculation_config.get("area_filter") and self.area_filter:
            area_name = self.area_filter.normalize_area_name(calculation_config["area_filter"])
            if area_name:
                raw_data = self.area_filter.filter_orders_by_area(raw_data, area_name)
        
        # Schichtfilterung anwenden (falls gewünscht)
        if calculation_config and calculation_config.get("shift_filter") and self.shift_manager:
            shift_name = self.shift_manager.normalize_shift_name(calculation_config["shift_filter"])
            if shift_name:
                raw_data = self.shift_manager.filter_orders_by_shift(raw_data, shift_name)
        
        # Zusätzliche Kontext-Informationen sammeln
        context_info = self._collect_context_info(raw_data)
        
        # Keine Berechnung? Gib angereicherte Rohdaten zurück
        if not calculation_config or calculation_config.get("type") is None:
            result = {
                "raw_data": raw_data,
                "count": len(raw_data),
                "has_calculation": False,
                "query_metadata": odata_result.get("query_metadata")
            }
            result.update(context_info)
            return result
        
        # Prüfe ob detaillierte Informationen gewünscht sind
        detail_level = calculation_config.get("detail_level", "basic")
        
        # Führe Berechnung aus
        try:
            calculation_result = self.registry.execute(raw_data, calculation_config)
            
            # Bei "detailed" Level: Füge erweiterte Statistiken hinzu
            if detail_level == "detailed":
                calculation_result = self._enrich_with_details(calculation_result, raw_data)
            
            result = {
                "calculation_result": calculation_result,
                "raw_data": raw_data,
                "raw_data_count": len(raw_data),
                "has_calculation": True,
                "calculation_type": calculation_config.get("type"),
                "query_metadata": odata_result.get("query_metadata"),
                "detail_level": detail_level
            }
            result.update(context_info)
            return result
            
        except Exception as e:
            print(f"Fehler in Calculation Engine: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Gib Rohdaten zurück
            result = {
                "raw_data": raw_data,
                "count": len(raw_data),
                "has_calculation": False,
                "calculation_error": str(e),
                "query_metadata": odata_result.get("query_metadata")
            }
            result.update(context_info)
            return result
    
    def _collect_context_info(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sammelt Kontext-Informationen über die Daten
        
        Args:
            data: Liste von Fahraufträgen
            
        Returns:
            Dict mit Kontext-Informationen
        """
        info = {}
        
        # Schicht-Informationen
        if self.shift_manager:
            info["current_shift"] = self.shift_manager.get_current_shift()
            info["shift_distribution"] = self.shift_manager.get_shift_distribution(data)
        
        # Bereichs-Informationen
        if self.area_filter:
            info["area_distribution"] = self.area_filter.get_area_distribution(data)
        
        # Status-Verteilung (Basis)
        status_dist = {}
        for item in data:
            status = item.get("state", "Unbekannt")
            status_dist[status] = status_dist.get(status, 0) + 1
        info["status_distribution"] = status_dist
        
        return info
    
    def _enrich_with_details(
        self, 
        calc_result: Dict[str, Any], 
        raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reichert Berechnungsergebnis mit detaillierten Statistiken an
        
        Args:
            calc_result: Basis-Berechnungsergebnis
            raw_data: Rohdaten
            
        Returns:
            Angereichertes Ergebnis
        """
        # Kopiere Basis-Ergebnis
        enriched = calc_result.copy()
        
        # Füge detaillierte Statistiken hinzu
        enriched["detailed_stats"] = {
            "total_records": len(raw_data),
            "status_breakdown": self._get_status_breakdown(raw_data),
            "group_breakdown": self._get_group_breakdown(raw_data),
            "top_resources": self._get_top_resources(raw_data, limit=5),
            "sample_orders": [
                {
                    "ID": item.get("ID"),
                    "state": item.get("state"),
                    "group": item.get("group"),
                    "shift": item.get("shift", "Unbekannt")
                }
                for item in raw_data[:3]
            ]
        }
        
        # Füge Schicht-spezifische Analysen hinzu
        if self.shift_manager:
            enriched["detailed_stats"]["shift_analysis"] = self._get_shift_analysis(raw_data)
        
        return enriched
    
    def _get_status_breakdown(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Berechnet detaillierte Status-Verteilung"""
        status_dist = {}
        for item in data:
            status = item.get("state", "Unbekannt")
            status_dist[status] = status_dist.get(status, 0) + 1
        
        total = len(data)
        
        # Kategorisiere Stati
        open_states = ["READY", "IN_PROGRESS", "ASSIGNED", "PENDING", "WAITING"]
        completed_states = ["COMPLETED", "DONE", "FINISHED"]
        
        open_count = sum(status_dist.get(s, 0) for s in open_states)
        completed_count = sum(status_dist.get(s, 0) for s in completed_states)
        other_count = total - open_count - completed_count
        
        return {
            "by_status": status_dist,
            "categorized": {
                "open": open_count,
                "completed": completed_count,
                "other": other_count
            },
            "open_percentage": round((open_count / total * 100) if total > 0 else 0, 1),
            "completed_percentage": round((completed_count / total * 100) if total > 0 else 0, 1)
        }
    
    def _get_group_breakdown(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Berechnet Gruppen-Verteilung"""
        group_dist = {}
        for item in data:
            group = item.get("group", "Unbekannt")
            group_dist[group] = group_dist.get(group, 0) + 1
        
        # Sortiere nach Anzahl
        return dict(sorted(group_dist.items(), key=lambda x: x[1], reverse=True))
    
    def _get_top_resources(self, data: List[Dict[str, Any]], limit: int = 5) -> Dict[str, int]:
        """Gibt Top N Ressourcen zurück"""
        resource_dist = {}
        for item in data:
            resource = item.get("assignedResource_ID")
            if resource and resource != "Keine":
                resource_dist[resource] = resource_dist.get(resource, 0) + 1
        
        # Sortiere und limitiere
        sorted_resources = sorted(resource_dist.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_resources[:limit])
    
    def _get_shift_analysis(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysiert Daten nach Schichten"""
        if not self.shift_manager:
            return {}
        
        shift_dist = self.shift_manager.get_shift_distribution(data)
        
        # Status pro Schicht
        status_by_shift = {}
        for item in data:
            shift = item.get("shift", "Unbekannt")
            status = item.get("state", "Unbekannt")
            
            if shift not in status_by_shift:
                status_by_shift[shift] = {}
            
            status_by_shift[shift][status] = status_by_shift[shift].get(status, 0) + 1
        
        return {
            "distribution": shift_dist,
            "status_by_shift": status_by_shift,
            "current_shift": self.shift_manager.get_current_shift()
        }
    
    def list_available_calculations(self) -> List[str]:
        """
        Listet verfügbare Berechnungen
        
        Returns:
            Liste mit Calculation-Types
        """
        return self.registry.list_available()
