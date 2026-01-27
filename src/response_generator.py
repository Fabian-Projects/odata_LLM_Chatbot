"""
Response Generator
Wandelt Berechnungsergebnisse in natürliche Sprache um
ERWEITERT: Mehr Details, bessere Conversation Memory
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
        raw_data = full_result.get("raw_data", [])

        # DEBUG - HIER EINFÜGEN:
        print(f"DEBUG _format_count:")
        print(f"  total: {total}")
        print(f"  raw_data length: {len(raw_data)}")
        print(f"  raw_data first 3: {raw_data[:3]}")
        print(f"  full_result keys: {full_result.keys()}")
        
        # Einfaches Count - VERBESSERT
        if not groups:
            if total == 0:
                return "Keine Fahraufträge gefunden."
            
            elif total == 1:
                # Zeige Details zum einen Auftrag
                order = raw_data[0] if raw_data else {}
                response = f"1 Fahrauftrag gefunden:\n\n"
                response += self._format_single_order(order)
                return response
            
            elif total <= 5:
                # Zeige alle Aufträge mit Details
                response = f"{total} Fahraufträge gefunden:\n\n"
                for i, order in enumerate(raw_data[:total], 1):
                    response += f"[{i}] {self._format_order_summary(order)}\n"
                return response
            
            else:
                # Viele Aufträge - zeige nur Gesamtzahl
                response = f"Insgesamt: {total} Fahraufträge"
                
                if detail_level == "detailed":
                    response += "\n\n"
                    response += self._add_detailed_context(full_result, raw_data)
                
                return response
        
        # Gruppiertes Count - VERBESSERT
        response = f"Insgesamt: {total} Fahrauftrag{'e' if total != 1 else ''}\n"
        response += f"\nAufgeteilt nach {self._translate_field(grouped_by)}:\n"
        
        for group, count in groups.items():
            percentage = (count / total * 100) if total > 0 else 0
            response += f"  {group}: {count} ({percentage:.1f}%)\n"
        
        # Top-Gruppe hervorheben
        if groups:
            top_group = max(groups.items(), key=lambda x: x[1])
            response += f"\nMeiste Aufträge: {top_group[0]} mit {top_group[1]} Aufträgen"
        
        # Bei detailed: Füge erweiterten Kontext hinzu
        if detail_level == "detailed":
            response += self._add_detailed_context(full_result, raw_data)
        
        return response
    
    def _format_single_order(self, order: Dict[str, Any]) -> str:
        """Formatiert einen einzelnen Auftrag mit allen Details"""
        
        lines = []
        
        # ID
        if order.get("ID"):
            lines.append(f"ID: {order['ID']}")
        
        # Route
        if order.get("source") and order.get("destination"):
            lines.append(f"Route: {order['source']} → {order['destination']}")
        
        # Status
        if order.get("state"):
            lines.append(f"Status: {order['state']}")
        
        # Typ
        if order.get("type_ID"):
            lines.append(f"Typ: {order['type_ID']}")
        
        # Ressource
        if order.get("assignedResource_ID"):
            lines.append(f"Ressource: {order['assignedResource_ID']}")
        
        # Material + Menge
        if order.get("material"):
            material_str = f"Material: {order['material']}"
            if order.get("quantityAmount"):
                material_str += f" ({order['quantityAmount']}"
                if order.get("quantityUnit"):
                    material_str += f" {order['quantityUnit']}"
                material_str += ")"
            lines.append(material_str)
        
        # Erstellt am
        if order.get("createdAt"):
            created = self._format_datetime(order["createdAt"])
            lines.append(f"Erstellt: {created}")
        
        # Fällig am
        if order.get("due"):
            due = self._format_datetime(order["due"])
            lines.append(f"Fällig: {due}")
        
        return "\n".join(lines)
    
    def _format_order_summary(self, order: Dict[str, Any]) -> str:
        """Formatiert eine kompakte Auftrags-Zusammenfassung (eine Zeile)"""
        
        parts = []
        
        if order.get("ID"):
            parts.append(f"ID {order['ID']}")
        
        if order.get("source") and order.get("destination"):
            parts.append(f"{order['source']} → {order['destination']}")
        
        if order.get("state"):
            parts.append(f"[{order['state']}]")
        
        if order.get("type_ID"):
            parts.append(f"({order['type_ID']})")
        
        return " | ".join(parts) if parts else "Keine Details verfügbar"
    
    def _add_detailed_context(self, result: Dict[str, Any], raw_data: List[Dict[str, Any]]) -> str:
        """Fügt ERWEITERTE detaillierte Kontext-Informationen hinzu"""
        
        response = "\n\n--- Detaillierte Analyse ---\n"
        
        # 1. Auftragstypen
        type_dist = {}
        for order in raw_data:
            order_type = order.get("type_ID", "Unbekannt")
            type_dist[order_type] = type_dist.get(order_type, 0) + 1
        
        if type_dist:
            response += "\nAuftragstypen:\n"
            for order_type, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
                response += f"  {order_type}: {count}\n"
        
        # 2. Offene Aufträge (nicht DONE/COMPLETED/INACTIVE)
        open_states = ["READY", "RUNNING", "ASSIGNED", "RESERVED", "PENDING"]
        open_orders = [o for o in raw_data if o.get("state") in open_states]
        
        if open_orders:
            response += f"\nOffene Aufträge ({len(open_orders)}):\n"
            for order in open_orders[:5]:  # Max 5 zeigen
                response += f"  • ID {order.get('ID')}: {order.get('source', '?')} → {order.get('destination', '?')} [{order.get('state')}]\n"
            
            if len(open_orders) > 5:
                response += f"  ... und {len(open_orders) - 5} weitere offene\n"
        
        # 3. Überfällige Aufträge (due in der Vergangenheit, nicht DONE)
        now = datetime.now()
        overdue_orders = []
        
        for order in raw_data:
            if order.get("due") and order.get("state") not in ["DONE", "COMPLETED"]:
                try:
                    due_dt = datetime.fromisoformat(order["due"].replace('Z', '+00:00'))
                    if due_dt < now:
                        overdue_orders.append(order)
                except:
                    pass
        
        if overdue_orders:
            response += f"\n⚠️ Überfällige Aufträge ({len(overdue_orders)}):\n"
            for order in overdue_orders[:5]:
                due_str = self._format_datetime(order.get("due", ""))
                response += f"  • ID {order.get('ID')}: {order.get('source', '?')} → {order.get('destination', '?')} (fällig: {due_str})\n"
            
            if len(overdue_orders) > 5:
                response += f"  ... und {len(overdue_orders) - 5} weitere überfällig\n"
        
        # 4. Top Routen
        routes = {}
        for order in raw_data:
            if order.get("source") and order.get("destination"):
                route = f"{order['source']} → {order['destination']}"
                routes[route] = routes.get(route, 0) + 1
        
        if routes:
            top_routes = sorted(routes.items(), key=lambda x: x[1], reverse=True)[:3]
            response += "\nHäufigste Routen:\n"
            for route, count in top_routes:
                response += f"  {route}: {count}x\n"
        
        # 5. Ressourcen-Verteilung
        resource_dist = {}
        for order in raw_data:
            resource = order.get("assignedResource_ID", "Nicht zugewiesen")
            if resource:
                resource_dist[resource] = resource_dist.get(resource, 0) + 1
        
        if resource_dist and len(resource_dist) > 1:  # Nur wenn mehrere Ressourcen
            response += "\nRessourcen-Verteilung:\n"
            for resource, count in sorted(resource_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
                response += f"  {resource}: {count}\n"
        
        return response
    
    def _format_datetime(self, dt_string: str) -> str:
        """Formatiert Datetime-String zu lesbarem Format"""
        
        if not dt_string:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return dt_string
    
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
            return "Keine Aufträge gefunden."
        
        if count == 1:
            # Einzelner Datensatz - zeige Details
            order = raw_data[0]
            response = "Auftrag gefunden:\n\n"
            response += self._format_single_order(order)
            return response
        
        # Mehrere Datensätze - zeige Übersicht
        response = f"{count} Aufträge gefunden:\n\n"
        
        # Zeige erste 5
        for i, order in enumerate(raw_data[:5], 1):
            response += f"[{i}] {self._format_order_summary(order)}\n"
        
        if count > 5:
            response += f"\n... und {count - 5} weitere"
        
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
            "modifiedAt": "Geändert am",
            "due": "Fällig am",
            "loadCarrierType_name": "Ladungsträger",
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