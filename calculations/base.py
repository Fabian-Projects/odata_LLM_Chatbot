"""
Basis-Klasse für alle Berechnungen
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod


class BaseCalculation(ABC):
    """
    Abstrakte Basis-Klasse für Berechnungen
    Alle Calculation-Module erben von dieser Klasse
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def calculate(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt die Berechnung durch
        
        Args:
            data: Liste mit Records von OData API
            config: Calculation Config vom Parser
                   z.B. {
                       "type": "count",
                       "grouping_field": "group",
                       "time_field": "createdAt"
                   }
        
        Returns:
            Dict mit Berechnungsergebnis
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validiert ob Config für diese Berechnung gültig ist
        
        Args:
            config: Calculation Config
            
        Returns:
            True wenn gültig
        """
        pass
    
    def _group_data(self, data: List[Dict[str, Any]], field: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Helper: Gruppiert Daten nach Feld
        
        Args:
            data: Liste mit Records
            field: Feldname für Gruppierung
            
        Returns:
            Dict mit gruppierten Daten
            {
                "Gruppe_A": [{record1}, {record2}],
                "Gruppe_B": [{record3}]
            }
        """
        grouped = {}
        
        for record in data:
            key = record.get(field)
            
            # None-Werte als "Unbekannt" behandeln
            if key is None or key == "":
                key = "Unbekannt"
            
            # String konvertieren für einheitliche Keys
            key = str(key)
            
            if key not in grouped:
                grouped[key] = []
            
            grouped[key].append(record)
        
        return grouped
    
    def _extract_numeric_values(self, data: List[Dict[str, Any]], field: str) -> List[float]:
        """
        Helper: Extrahiert numerische Werte aus Feld
        
        Args:
            data: Liste mit Records
            field: Feldname
            
        Returns:
            Liste mit numerischen Werten (None-Werte gefiltert)
        """
        values = []
        
        for record in data:
            value = record.get(field)
            
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    # Nicht-numerische Werte ignorieren
                    pass
        
        return values