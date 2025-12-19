"""
Calculation Engine
Orchestriert Berechnungen auf OData-Daten
"""

from typing import Dict, Any, List, Optional
from calculations.registry import get_registry


class CalculationEngine:
    """
    Haupt-Engine für Berechnungen
    Nimmt Rohdaten + Config und gibt Ergebnisse zurück
    """
    
    def __init__(self):
        self.registry = get_registry()
    
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
                                   ...
                               }
        
        Returns:
            Dict mit Ergebnis
            
            Ohne Berechnung:
            {
                "raw_data": [...],
                "count": 42,
                "has_calculation": False
            }
            
            Mit Berechnung:
            {
                "calculation_result": {
                    "groups": {...},
                    "total": 42,
                    ...
                },
                "raw_data_count": 42,
                "has_calculation": True,
                "calculation_type": "count"
            }
        """
        
        # Daten extrahieren
        raw_data = odata_result.get("value", [])
        
        # Keine Berechnung? Gib Rohdaten zurück
        if not calculation_config or calculation_config.get("type") is None:
            return {
                "raw_data": raw_data,
                "count": len(raw_data),
                "has_calculation": False,
                "query_metadata": odata_result.get("query_metadata")
            }
        
        # Führe Berechnung aus
        try:
            calculation_result = self.registry.execute(raw_data, calculation_config)
            
            return {
                "calculation_result": calculation_result,
                "raw_data_count": len(raw_data),
                "has_calculation": True,
                "calculation_type": calculation_config.get("type"),
                "query_metadata": odata_result.get("query_metadata")
            }
            
        except Exception as e:
            print(f"Fehler in Calculation Engine: {e}")
            
            # Fallback: Gib Rohdaten zurück
            return {
                "raw_data": raw_data,
                "count": len(raw_data),
                "has_calculation": False,
                "calculation_error": str(e),
                "query_metadata": odata_result.get("query_metadata")
            }
    
    def list_available_calculations(self) -> List[str]:
        """
        Listet verfügbare Berechnungen
        
        Returns:
            Liste mit Calculation-Types
        """
        return self.registry.list_available()