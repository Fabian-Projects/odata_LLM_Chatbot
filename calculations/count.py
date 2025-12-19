"""
Count Calculation
Zählt Records mit optionaler Gruppierung
"""

from typing import Dict, Any, List
from .base import BaseCalculation


class CountCalculation(BaseCalculation):
    """
    Zählt Anzahl Records
    
    Unterstützt:
    - Einfaches Zählen (keine Gruppierung)
    - Gruppiertes Zählen (nach beliebigem Feld)
    """
    
    def calculate(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt Count-Berechnung durch
        
        Args:
            data: Liste mit Records
            config: {
                "type": "count",
                "grouping_field": "group" oder None
            }
        
        Returns:
            Ohne Gruppierung:
            {
                "total": 42,
                "type": "count"
            }
            
            Mit Gruppierung:
            {
                "groups": {
                    "Andis_Stapler": 15,
                    "Marias_Team": 27
                },
                "total": 42,
                "type": "count",
                "grouped_by": "group"
            }
        """
        
        grouping_field = config.get("grouping_field")
        
        if grouping_field:
            # Gruppiertes Zählen
            return self._count_grouped(data, grouping_field)
        else:
            # Einfaches Zählen
            return self._count_simple(data)
    
    def _count_simple(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Einfaches Zählen ohne Gruppierung"""
        return {
            "total": len(data),
            "type": "count"
        }
    
    def _count_grouped(self, data: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
        """Zählen mit Gruppierung"""
        
        grouped_data = self._group_data(data, field)
        
        # Zähle pro Gruppe
        group_counts = {
            group: len(records) 
            for group, records in grouped_data.items()
        }
        
        # Sortiere nach Anzahl (absteigend)
        sorted_groups = dict(
            sorted(group_counts.items(), key=lambda x: x[1], reverse=True)
        )
        
        return {
            "groups": sorted_groups,
            "total": len(data),
            "type": "count",
            "grouped_by": field,
            "group_count": len(sorted_groups)
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validiert Config
        
        Returns:
            True wenn type == "count"
        """
        return config.get("type") == "count"


class CountPercentageCalculation(BaseCalculation):
    """
    Erweiterte Count-Berechnung mit Prozentangaben
    Nützlich für Auswertungen
    """
    
    def calculate(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Count mit Prozentangaben
        
        Returns:
            {
                "groups": {
                    "Andis_Stapler": {
                        "count": 15,
                        "percentage": 35.7
                    },
                    "Marias_Team": {
                        "count": 27,
                        "percentage": 64.3
                    }
                },
                "total": 42,
                "type": "count_percentage"
            }
        """
        
        grouping_field = config.get("grouping_field")
        
        if not grouping_field:
            # Ohne Gruppierung macht Prozent keinen Sinn
            return {
                "total": len(data),
                "type": "count_percentage"
            }
        
        grouped_data = self._group_data(data, grouping_field)
        total = len(data)
        
        # Count und Prozent pro Gruppe
        group_stats = {}
        
        for group, records in grouped_data.items():
            count = len(records)
            percentage = (count / total * 100) if total > 0 else 0
            
            group_stats[group] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        # Sortiere nach Count
        sorted_groups = dict(
            sorted(group_stats.items(), key=lambda x: x[1]["count"], reverse=True)
        )
        
        return {
            "groups": sorted_groups,
            "total": total,
            "type": "count_percentage",
            "grouped_by": grouping_field
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validiert Config"""
        return config.get("type") == "count_percentage"