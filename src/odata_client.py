"""
OData Client für Logistics API
Führt OData-Queries aus und gibt Rohdaten zurück
ERWEITERT: Ressourcen-Filter + assignBestOrders
"""

import requests
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode
from datetime import datetime
import json

from .oauth_handler import OAuthTokenHandler


class ODataClient:
    """
    OData Client für API-Abfragen
    Nutzt OAuth für Authentifizierung
    """
    
    def __init__(
        self, 
        base_url: str,
        token_url: str,
        client_id: str,
        client_secret: str
    ):
        """
        Args:
            base_url: OData API Base URL (z.B. .../api_core/orders/Orders)
            token_url: OAuth Token Endpoint
            client_id: OAuth Client ID
            client_secret: OAuth Client Secret
        """
        self.base_url = base_url.rstrip('/')
        self.token_handler = OAuthTokenHandler(token_url, client_id, client_secret)
        self.request_count = 0
        self.last_response = None
    
    def execute_query(self, parsed_query: Dict[str, Any], resource_id: str = "SUPERVISOR") -> Dict[str, Any]:
        """
        Führt OData-Query aus basierend auf Parser-Output
        ERWEITERT: Filtert automatisch nach Ressource (außer für Supervisor)
        
        Args:
            parsed_query: JSON vom LLM Parser mit odata_params
            resource_id: Ressourcen-ID für Filterung
            
        Returns:
            Dict mit Rohdaten von API
        """
        
        # OData Parameters extrahieren
        odata_params = parsed_query.get("odata_params", {}).copy()
        
        # Ressourcen-Filter hinzufügen (außer für Supervisor)
        if resource_id != "SUPERVISOR":
            existing_filter = odata_params.get("$filter", "")
            resource_filter = f"assignedResource_ID eq '{resource_id}'"
            
            if existing_filter:
                # Kombiniere mit bestehendem Filter
                odata_params["$filter"] = f"({existing_filter}) and ({resource_filter})"
            else:
                odata_params["$filter"] = resource_filter
        
        # Query ausführen
        try:
            response_data = self._execute_request(odata_params)
            
            # Metadaten hinzufügen
            result = {
                "value": response_data.get("value", []),
                "count": len(response_data.get("value", [])),
                "query_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "odata_params": odata_params,
                    "resource_id": resource_id,
                    "request_count": self.request_count
                }
            }
            
            # Wenn $count Parameter gesetzt war
            if odata_params.get("$count") == "true" or odata_params.get("$count") is True:
                result["total_count"] = response_data.get("@odata.count", result["count"])
            
            return result
            
        except Exception as e:
            print(f"Fehler bei OData Query: {e}")
            return {
                "value": [],
                "count": 0,
                "error": str(e),
                "query_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "odata_params": odata_params,
                    "resource_id": resource_id,
                    "failed": True
                }
            }
    
    def assign_best_orders(self, resource_id: str, current_position: str) -> Dict[str, Any]:
        """
        Ruft assignBestOrdersTest API auf um nächste Aufträge zu ermitteln
        
        Args:
            resource_id: Ressourcen-ID (z.B. "SCHUBMASTSTAPLER_LINKS")
            current_position: Aktuelle Position (z.B. "SCHUBMAST-PARK-LINKS" oder UUID)
            
        Returns:
            Dict mit geparsten Aufträgen:
            {
                "orders": [
                    {"id": "90", "from": "HR-01-02", "to": "HR-01-EIN"},
                    ...
                ],
                "logs": [...],
                "raw_response": {...}
            }
        """
        
        # Token holen
        try:
            token = self.token_handler.get_token()
        except Exception as e:
            raise Exception(f"Token-Abruf fehlgeschlagen: {e}")
        
        # URL für assignBestOrdersTest
        # base_url ist z.B. ".../api_core/orders/Orders"
        # Wir brauchen ".../api_core/orders/assignBestOrdersTest"
        base_parts = self.base_url.rsplit('/', 1)[0]  # Entferne "/Orders" am Ende
        url = f"{base_parts}/assignBestOrdersTest"
        
        # Request Body
        body = {
            "resourceId": resource_id,
            "currentPosition": {
                "poiIdOrName": current_position
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"\nassignBestOrders Request:")
        print(f"URL: {url}")
        print(f"Body: {json.dumps(body, indent=2)}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )
            
            self.request_count += 1
            self.last_response = response
            
            print(f"Status: {response.status_code}")
            
            response.raise_for_status()
            
            raw_data = response.json()
            
            # Parse die Logs um Aufträge zu extrahieren
            parsed_orders = self._parse_order_logs(raw_data.get("logs", []))
            
            return {
                "orders": parsed_orders,
                "logs": raw_data.get("logs", []),
                "raw_response": raw_data,
                "resource_id": resource_id,
                "position": current_position
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data}"
            except:
                error_msg += f": {response.text[:200]}"
            
            raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request fehlgeschlagen: {e}")
    
    def _parse_order_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Parst Order-Informationen aus den Logs
        
        Pattern: "ID (von -> nach)" oder "Order 'ID': 'von' → 'nach'"
        
        Args:
            logs: Liste von Log-Einträgen
            
        Returns:
            Liste von Order-Dicts mit id, from, to
        """
        orders = []
        
        # Pattern für beide Formate
        # Format 1: "90 (HR-01-02 -> HR-01-EIN)"
        # Format 2: "Order '90': 'HR-01-02' → 'HR-01-EIN'"
        pattern1 = r"(\d+)\s*\(([A-Z0-9\-]+)\s*->\s*([A-Z0-9\-]+)\)"
        pattern2 = r"Order\s+'(\d+)':\s+'([A-Z0-9\-]+)'\s+→\s+'([A-Z0-9\-]+)'"
        
        for log in logs:
            message = log.get("message", "")
            
            # Versuche Pattern 2 (einzelner Auftrag)
            match2 = re.search(pattern2, message)
            if match2:
                orders.append({
                    "id": match2.group(1),
                    "from": match2.group(2),
                    "to": match2.group(3)
                })
                continue
            
            # Versuche Pattern 1 (kann mehrere enthalten, kommasepariert)
            matches1 = re.finditer(pattern1, message)
            for match in matches1:
                orders.append({
                    "id": match.group(1),
                    "from": match.group(2),
                    "to": match.group(3)
                })
        
        return orders
    
    def _execute_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt HTTP Request aus
        
        Args:
            params: OData Query Parameters
            
        Returns:
            Response JSON
        """
        
        # Token holen
        try:
            token = self.token_handler.get_token()
        except Exception as e:
            raise Exception(f"Token-Abruf fehlgeschlagen: {e}")
        
        # Headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # URL mit Query Parameters
        query_string = self._build_query_string(params)
        url = f"{self.base_url}?{query_string}" if query_string else self.base_url
        
        print(f"\nOData Request:")
        print(f"URL: {url}")
        print(f"Params: {json.dumps(params, indent=2)}")
        
        # Request ausführen
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            self.request_count += 1
            self.last_response = response
            
            print(f"Status: {response.status_code}")
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data}"
            except:
                error_msg += f": {response.text[:200]}"
            
            raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request fehlgeschlagen: {e}")
    
    def _build_query_string(self, params: Dict[str, Any]) -> str:
        """
        Baut OData Query String
        
        Args:
            params: Dict mit OData Parametern
            
        Returns:
            URL-encoded Query String
        """
        
        # Leere/None Werte entfernen
        clean_params = {
            k: v for k, v in params.items() 
            if v is not None and v != ""
        }
        
        # Boolean zu String
        for key, value in clean_params.items():
            if isinstance(value, bool):
                clean_params[key] = "true" if value else "false"
        
        # URL-encode
        if clean_params:
            return urlencode(clean_params, quote_via=requests.utils.quote)
        
        return ""
    
    def test_connection(self) -> bool:
        """
        Testet Verbindung zur API
        
        Returns:
            True wenn erfolgreich
        """
        try:
            print("Teste OData Verbindung...")
            
            # Minimale Query
            test_params = {"$top": 1, "$select": "ID"}
            result = self._execute_request(test_params)
            
            print(f"Verbindung erfolgreich! {len(result.get('value', []))} Records gefunden.")
            return True
            
        except Exception as e:
            print(f"Verbindungstest fehlgeschlagen: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Client-Statistiken zurück
        
        Returns:
            Dict mit Stats
        """
        return {
            "request_count": self.request_count,
            "token_valid": self.token_handler._is_token_valid(),
            "base_url": self.base_url
        }
    
    def save_response_to_file(self, data: Dict[str, Any], prefix: str = "odata") -> str:
        """
        Speichert Response in JSON-Datei
        
        Args:
            data: Daten zum Speichern
            prefix: Dateiname-Prefix
            
        Returns:
            Dateiname
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{prefix}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Gespeichert: {filename}")
        return filename


# Helper Functions

def build_filter_expression(field: str, operator: str, value: Any) -> str:
    """
    Helper: Baut OData Filter-Ausdruck
    
    Args:
        field: Feldname
        operator: eq, ne, gt, ge, lt, le
        value: Wert (String wird automatisch quoted)
        
    Returns:
        OData Filter String
        
    Example:
        build_filter_expression("state", "eq", "READY")
        -> "state eq 'READY'"
    """
    if isinstance(value, str):
        return f"{field} {operator} '{value}'"
    else:
        return f"{field} {operator} {value}"


def combine_filters(filters: List[str], logic: str = "and") -> str:
    """
    Helper: Kombiniert mehrere Filter
    
    Args:
        filters: Liste von Filter-Ausdrücken
        logic: "and" oder "or"
        
    Returns:
        Kombinierter Filter String
        
    Example:
        combine_filters([
            "state eq 'READY'",
            "group eq 'Andis_Stapler'"
        ])
        -> "state eq 'READY' and group eq 'Andis_Stapler'"
    """
    return f" {logic} ".join(filters)