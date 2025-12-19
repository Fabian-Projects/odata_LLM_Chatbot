"""
Sum Calculation
Summiert numerische Felder mit optionaler Gruppierung
"""

from typing import Dict, Any, List
from .base import BaseCalculation


class SumCalculation(BaseCalculation):
    """
    Summiert numerische Werte
    
    Beispiele:
    - Gesamtmenge Material
    - Summe nach Gruppe
    """
    
    def calculate(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt Summen-Berechnung durch
        
        Args:
            data: Liste mit Records
            config: {
                "type": "sum",
                "aggregation_field": "quantityAmount",  # Welches Feld summieren
                "grouping_field": "group" oder None
            }
        
        Returns:
            Ohne Gruppierung:
            {
                "total": 1250.5,
                "field": "quantityAmount",
                "type": "sum",
                "unit": "FT"  # Falls vorhanden
            }
            
            Mit Gruppierung:
            {
                "groups": {
                    "Andis_Stapler": 450.0,
                    "Marias_Team": 800.5
                },
                "total": 1250.5,
                "field": "quantityAmount",
                "type": "sum",
                "grouped_by": "group"
            }
        """
        
        aggregation_field = config.get("aggregation_field", "quantityAmount")
        grouping_field = config.get("grouping_field")
        
        if grouping_field:
            # Gruppierte Summe
            return self._sum_grouped(data, aggregation_field, grouping_field)
        else:
            # Einfache Summe
            return self._sum_simple(data, aggregation_field)
    
    def _sum_simple(self, data: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
        """Einfache Summe ohne Gruppierung"""
        
        values = self._extract_numeric_values(data, field)
        total = sum(values)
        
        # Versuche Unit zu ermitteln (z.B. quantityUnit)
        unit = None
        unit_field = f"{field.replace('Amount', 'Unit')}"
        
        for record in data:
            if unit_field in record and record[unit_field]:
                unit = record[unit_field]
                break
        
        result = {
            "total": round(total, 2),
            "field": field,
            "type": "sum",
            "record_count": len(values)
        }
        
        if unit:
            result["unit"] = unit
        
        return result
    
    def _sum_grouped(self, data: List[Dict[str, Any]], field: str, grouping_field: str) -> Dict[str, Any]:
        """Summe mit Gruppierung"""
        
        grouped_data = self._group_data(data, grouping_field)
        
        # Summe pro Gruppe
        group_sums = {}
        total = 0
        
        for group, records in grouped_data.items():
            values = self._extract_numeric_values(records, field)
            group_sum = sum(values)
            group_sums[group] = round(group_sum, 2)
            total += group_sum
        
        # Sortiere nach Summe (absteigend)
        sorted_groups = dict(
            sorted(group_sums.items(), key=lambda x: x[1], reverse=True)
        )
        
        return {
            "groups": sorted_groups,
            "total": round(total, 2),
            "field": field,
            "type": "sum",
            "grouped_by": grouping_field,
            "group_count": len(sorted_groups)
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validiert Config
        
        Returns:
            True wenn type == "sum"
        """
        return config.get("type") == "sum"


class AggregationCalculation(BaseCalculation):
    """
    Allgemeine Aggregations-Berechnung
    Unterstützt: sum, avg, min, max
    """
    
    def calculate(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt Aggregation durch
        
        Args:
            config: {
                "type": "aggregation",
                "aggregation": "sum" | "avg" | "min" | "max",
                "aggregation_field": "quantityAmount",
                "grouping_field": "group" oder None
            }
        
        Returns:
            Je nach aggregation verschiedene Outputs
        """
        
        aggregation_type = config.get("aggregation", "sum")
        aggregation_field = config.get("aggregation_field", "quantityAmount")
        grouping_field = config.get("grouping_field")
        
        if grouping_field:
            return self._aggregate_grouped(data, aggregation_field, grouping_field, aggregation_type)
        else:
            return self._aggregate_simple(data, aggregation_field, aggregation_type)
    
    def _aggregate_simple(self, data: List[Dict[str, Any]], field: str, agg_type: str) -> Dict[str, Any]:
        """Einfache Aggregation"""
        
        values = self._extract_numeric_values(data, field)
        
        if not values:
            return {
                "result": None,
                "field": field,
                "type": agg_type,
                "record_count": 0
            }
        
        if agg_type == "sum":
            result = sum(values)
        elif agg_type == "avg":
            result = sum(values) / len(values)
        elif agg_type == "min":
            result = min(values)
        elif agg_type == "max":
            result = max(values)
        else:
            result = sum(values)  # Default
        
        return {
            "result": round(result, 2),
            "field": field,
            "type": agg_type,
            "record_count": len(values)
        }
    
    def _aggregate_grouped(self, data: List[Dict[str, Any]], field: str, grouping_field: str, agg_type: str) -> Dict[str, Any]:
        """Aggregation mit Gruppierung"""
        
        grouped_data = self._group_data(data, grouping_field)
        
        group_results = {}
        
        for group, records in grouped_data.items():
            values = self._extract_numeric_values(records, field)
            
            if not values:
                group_results[group] = None
                continue
            
            if agg_type == "sum":
                result = sum(values)
            elif agg_type == "avg":
                result = sum(values) / len(values)
            elif agg_type == "min":
                result = min(values)
            elif agg_type == "max":
                result = max(values)
            else:
                result = sum(values)
            
            group_results[group] = round(result, 2)
        
        # Sortiere nach Wert
        sorted_groups = dict(
            sorted(group_results.items(), key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
        )
        
        return {
            "groups": sorted_groups,
            "field": field,
            "type": agg_type,
            "grouped_by": grouping_field
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validiert Config"""
        return config.get("aggregation") in ["sum", "avg", "min", "max"]