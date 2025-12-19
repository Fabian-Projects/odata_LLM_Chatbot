"""
Calculation Registry
Verwaltet alle verfügbaren Berechnungen
"""

from typing import Dict, Any, List, Optional
from .base import BaseCalculation
from .count import CountCalculation, CountPercentageCalculation
from .sum import SumCalculation, AggregationCalculation


class CalculationRegistry:
    """
    Registry für alle Calculation-Module
    Ermöglicht einfaches Hinzufügen neuer Berechnungen
    """
    
    def __init__(self):
        self.calculations: Dict[str, BaseCalculation] = {}
        self._register_default_calculations()
    
    def _register_default_calculations(self):
        """Registriert Standard-Berechnungen"""
        self.register("count", CountCalculation())
        self.register("count_percentage", CountPercentageCalculation())
        self.register("sum", SumCalculation())
        self.register("aggregation", AggregationCalculation())
    
    def register(self, name: str, calculation: BaseCalculation):
        """
        Registriert neue Berechnung
        
        Args:
            name: Name/Typ der Berechnung
            calculation: Calculation-Instanz
        """
        self.calculations[name] = calculation
        print(f"Calculation registriert: {name}")
    
    def get(self, name: str) -> Optional[BaseCalculation]:
        """
        Holt Berechnung nach Name
        
        Args:
            name: Name der Berechnung
            
        Returns:
            Calculation oder None
        """
        return self.calculations.get(name)
    
    def list_available(self) -> List[str]:
        """
        Listet alle verfügbaren Berechnungen
        
        Returns:
            Liste mit Namen
        """
        return list(self.calculations.keys())
    
    def execute(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt Berechnung aus basierend auf Config
        
        Args:
            data: Rohdaten vom OData Client
            config: Calculation Config vom Parser
                   {
                       "type": "count",
                       "grouping_field": "group",
                       ...
                   }
        
        Returns:
            Berechnungsergebnis
            
        Raises:
            ValueError: Wenn Calculation-Type nicht existiert
        """
        
        calc_type = config.get("type")
        
        if not calc_type:
            raise ValueError("Kein 'type' in calculation config")
        
        # Spezialfall: aggregation nutzt das aggregation-Feld
        if "aggregation" in config and config["aggregation"] in ["sum", "avg", "min", "max"]:
            calc_type = "aggregation"
        
        calculation = self.get(calc_type)
        
        if not calculation:
            raise ValueError(f"Unbekannte Berechnung: {calc_type}. Verfügbar: {self.list_available()}")
        
        # Validiere Config
        if not calculation.validate_config(config):
            raise ValueError(f"Ungültige Config für {calc_type}")
        
        # Führe Berechnung aus
        try:
            result = calculation.calculate(data, config)
            
            # Füge Metadaten hinzu
            result["calculation_type"] = calc_type
            result["record_count_input"] = len(data)
            
            return result
            
        except Exception as e:
            print(f"Fehler bei Berechnung {calc_type}: {e}")
            raise


# Globale Registry-Instanz
_registry = CalculationRegistry()


def get_registry() -> CalculationRegistry:
    """
    Gibt globale Registry-Instanz zurück
    
    Returns:
        CalculationRegistry
    """
    return _registry


def execute_calculation(data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience Function: Führt Berechnung aus
    
    Args:
        data: Rohdaten
        config: Calculation Config
        
    Returns:
        Berechnungsergebnis
    """
    return _registry.execute(data, config)