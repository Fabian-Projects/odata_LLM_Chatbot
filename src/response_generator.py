"""
Response Generator
Wandelt Berechnungsergebnisse in natürliche Sprache um
KORRIGIERT für createdAt Feldname
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseGenerator:
    """
    Generiert natürliche Antworten aus Berechnungsergebnissen
    """
    
    def __init__(self, language: str = "de"):
        """
        Args:
            language: Sprache für Antworten (de oder en)
        """
        self.language = language
    
    def generate(
        self, 
        result: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generiert Antwort aus Ergebnis
        
        Args:
            result: Ergebnis von Calculation Engine
            context: Optionaler Context (user_question, etc.)
        
        Returns:
            Formatierte Antwort als String
        """
        
        # Prüfe Detail-Level
        detail_level = result.get("detail_level", "basic")
        
        # Keine Berechnung? Zeige Rohdaten
        if not result.get("has_calculation"):
            return self._format_raw_data(result, context)
        
        # Mit Berechnung
        calc_result = result.get("calculation_result", {})
        calc_type = result.get("calculation_type")
        
        if calc_type == "count":
            return self._format_count(calc_result, result, context, detail_level)
        
        elif calc_type == "count_percentage":
            return self._format_count_percentage(calc_result, context)
        
        elif calc_type == "sum":
            return self._format_sum(calc_result, context)
        
        elif calc_type in ["avg", "min", "max", "aggregation"]:
            return self._format_aggregation(calc_result, context)
        
        else:
            # Fallback
            return self._format_generic(calc_result, context)
    
    def _format_count(
        self, 
        calc_result: Dict[str, Any],
        full_result: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        detail_level: str
    ) -> str:
        """Formatiert Count-Ergebnis"""
        
        total = calc_result.get("total", 0)
        groups = calc_result.get("groups")
        grouped_by = calc_result.get("grouped_by")
        
        # Einfaches Count
        if not groups:
            response = f"Insgesamt: {total} Fahrauftrag{'e' if total != 1 else ''}"
            
            # Bei detailed: Füge Kontext hinzu
            if detail_level == "detailed":
                response += self._add_detailed_context(full_result)
            
            return response
        
        # Gruppiertes Count
        response = f"Insgesamt: {total} Fahrauftrag{'e' if total != 1 else ''}\n"
        response += f"\nAufgeteilt nach {self._translate_field(grouped_by)}:\n"
        
        for group, count in groups.items():
            percentage = (count / total * 100) if total > 0 else 0
            response += f"  {group}: {count} ({percentage:.1f}%)\n"
        
        # Top-Gruppe hervorheben
        if groups:
            top_group = max(groups.items(), key=lambda x: x[1])
            response += f"\nMeiste Auftraege: {top_group[0]} mit {top_group[1]} Auftraegen"
        
        # Bei detailed: Füge Kontext hinzu
        if detail_level == "detailed":
            response += self._add_detailed_context(full_result)
        
        return response
    
    def _format_count_percentage(self, calc_result: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """Formatiert Count mit Prozent"""
        
        total = calc_result.get("total", 0)
        groups = calc_result.get("groups", {})
        grouped_by = calc_result.get("grouped_by")
        
        response = f"Insgesamt: {total} Fahrauftrag{'e' if total != 1 else ''}\n"
        response += f"\nAufgeteilt nach {self._translate_field(grouped_by)}:\n"
        
        for group, stats in groups.items():
            count = stats.get("count", 0)
            percentage = stats.get("percentage", 0)
            response += f"  {group}: {count} ({percentage}%)\n"
        
        return response
    
    def _format_sum(self, calc_result: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """Formatiert Summen-Ergebnis"""
        
        total = calc_result.get("total", 0)
        field = calc_result.get("field", "")
        unit = calc_result.get("unit", "")
        groups = calc_result.get("groups")
        grouped_by = calc_result.get("grouped_by")
        
        unit_str = f" {unit}" if unit else ""
        
        # Einfache Summe
        if not groups:
            return f"Gesamtsumme ({self._translate_field(field)}): {total}{unit_str}"
        
        # Gruppierte Summe
        response = f"Gesamtsumme ({self._translate_field(field)}): {total}{unit_str}\n"
        response += f"\nAufgeteilt nach {self._translate_field(grouped_by)}:\n"
        
        for group, sum_value in groups.items():
            percentage = (sum_value / total * 100) if total > 0 else 0
            response += f"  {group}: {sum_value}{unit_str} ({percentage:.1f}%)\n"
        
        return response
    
    def _format_aggregation(self, calc_result: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """Formatiert Aggregations-Ergebnis"""
        
        agg_type = calc_result.get("type", "aggregation")
        field = calc_result.get("field", "")
        groups = calc_result.get("groups")
        result_value = calc_result.get("result")
        
        agg_label = {
            "avg": "Durchschnitt",
            "min": "Minimum",
            "max": "Maximum",
            "sum": "Summe"
        }.get(agg_type, agg_type)
        
        # Einfaches Ergebnis
        if result_value is not None and not groups:
            return f"{agg_label} ({self._translate_field(field)}): {result_value}"
        
        # Gruppiert
        if groups:
            grouped_by = calc_result.get("grouped_by", "")
            response = f"{agg_label} nach {self._translate_field(grouped_by)}:\n"
            
            for group, value in groups.items():
                if value is not None:
                    response += f"  {group}: {value}\n"
            
            return response
        
        return f"{agg_label}: {result_value}"
    
    def _format_raw_data(self, result: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """Formatiert Rohdaten ohne Berechnung"""
        
        count = result.get("count", 0)
        raw_data = result.get("raw_data", [])
        
        if count == 0:
            return "Keine Auftraege gefunden."
        
        if count == 1:
            # Einzelner Datensatz - zeige Details
            record = raw_data[0]
            response = "Auftrag gefunden:\n\n"
            
            # Wichtige Felder zuerst
            important_fields = ["ID", "state", "type_ID", "source", "destination", 
                              "material", "quantityAmount", "quantityUnit", "createdAt"]
            
            for field in important_fields:
                if field in record and record[field] is not None:
                    label = self._translate_field(field)
                    value = record[field]
                    
                    # Datum formatieren (createdAt!)
                    if field == "createdAt" and isinstance(value, str):
                        try:
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            value = dt.strftime("%d.%m.%Y %H:%M")
                        except:
                            pass
                    
                    response += f"{label}: {value}\n"
            
            return response
        
        # Mehrere Datensätze - zeige Übersicht
        response = f"{count} Auftraege gefunden:\n\n"
        
        # Zeige erste 5
        for i, record in enumerate(raw_data[:5], 1):
            response += f"[{i}] ID: {record.get('ID', 'N/A')}"
            
            if record.get('state'):
                response += f" | Status: {record.get('state')}"
            
            if record.get('type_ID'):
                response += f" | Typ: {record.get('type_ID')}"
            
            response += "\n"
        
        if count > 5:
            response += f"\n... und {count - 5} weitere"
        
        return response
    
    def _add_detailed_context(self, result: Dict[str, Any]) -> str:
        """Fügt detaillierte Kontext-Informationen hinzu"""
        
        response = "\n\n--- Detaillierte Informationen ---\n"
        
        # Status-Verteilung
        status_dist = result.get("status_distribution", {})
        if status_dist:
            response += "\nStatus-Uebersicht:\n"
            for status, count in status_dist.items():
                response += f"  {status}: {count}\n"
        
        return response
    
    def _format_generic(self, calc_result: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """Generische Formatierung als Fallback"""
        
        response = "Ergebnis:\n"
        
        for key, value in calc_result.items():
            if key not in ["calculation_type", "record_count_input"]:
                response += f"{key}: {value}\n"
        
        return response
    
    def _translate_field(self, field: str) -> str:
        """Übersetzt Feldnamen ins Deutsche"""
        
        translations = {
            "ID": "ID",
            "state": "Status",
            "type_ID": "Auftragstyp",
            "group": "Gruppe",
            "assignedResource_ID": "Ressource",
            "source": "Quelle",
            "destination": "Ziel",
            "material": "Material",
            "quantityAmount": "Menge",
            "quantityUnit": "Einheit",
            "createdAt": "Erstellt am",
            "modifiedAt": "Geaendert am",
            "due": "Faellig am",
            "loadCarrierType_name": "Ladungstraeger",
            "categoryReasonCode": "Kategorie",
            "origin": "Ursprung",
            "note": "Notiz"
        }
        
        return translations.get(field, field)


class ResponseFormatter:
    """
    Erweiterte Formatierung mit verschiedenen Output-Formaten
    """
    
    @staticmethod
    def format_as_table(groups: Dict[str, Any], headers: List[str] = None) -> str:
        """
        Formatiert gruppierte Daten als Tabelle
        
        Args:
            groups: Dict mit gruppierten Daten
            headers: Optional, Header-Namen
            
        Returns:
            ASCII-Tabelle als String
        """
        
        if not groups:
            return "Keine Daten"
        
        # Bestimme maximale Breiten
        max_key_len = max(len(str(k)) for k in groups.keys())
        max_val_len = max(len(str(v)) for v in groups.values())
        
        # Header
        header1 = headers[0] if headers and len(headers) > 0 else "Gruppe"
        header2 = headers[1] if headers and len(headers) > 1 else "Wert"
        
        max_key_len = max(max_key_len, len(header1))
        max_val_len = max(max_val_len, len(header2))
        
        # Tabelle bauen
        separator = "+" + "-" * (max_key_len + 2) + "+" + "-" * (max_val_len + 2) + "+"
        
        table = separator + "\n"
        table += f"| {header1:<{max_key_len}} | {header2:<{max_val_len}} |\n"
        table += separator + "\n"
        
        for key, value in groups.items():
            table += f"| {str(key):<{max_key_len}} | {str(value):<{max_val_len}} |\n"
        
        table += separator
        
        return table
    
    @staticmethod
    def format_as_list(items: List[Dict[str, Any]], fields: List[str] = None) -> str:
        """
        Formatiert Liste von Records
        
        Args:
            items: Liste mit Datensätzen
            fields: Optionale Feldauswahl
            
        Returns:
            Formatierte Liste
        """
        
        if not items:
            return "Keine Daten"
        
        response = ""
        
        for i, item in enumerate(items, 1):
            response += f"\n[{i}]\n"
            
            # Felder oder alle Felder
            show_fields = fields if fields else item.keys()
            
            for field in show_fields:
                if field in item and item[field] is not None:
                    response += f"  {field}: {item[field]}\n"
        
        return response