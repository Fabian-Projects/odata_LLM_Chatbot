"""
OData Client für Logistics API
Führt OData-Queries aus und gibt Rohdaten zurück
"""

import requests
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
            base_url: OData API Base URL
            token_url: OAuth Token Endpoint
            client_id: OAuth Client ID
            client_secret: OAuth Client Secret
        """
        self.base_url = base_url.rstrip('/')
        self.token_handler = OAuthTokenHandler(token_url, client_id, client_secret)
        self.request_count = 0
        self.last_response = None
    
    def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt OData-Query aus basierend auf Parser-Output
        
        Args:
            parsed_query: JSON vom LLM Parser mit odata_params
            
        Returns:
            Dict mit Rohdaten von API
            
        Example:
            Input: {
                "odata_params": {
                    "$filter": "createdAt ge 2025-12-17T00:00:00Z",
                    "$select": "ID,group",
                    "$top": 100
                }
            }
            
            Output: {
                "value": [...],  # Array mit Daten
                "count": 42,     # Optional, wenn $count=true
                "metadata": {...}
            }
        """
        
        # OData Parameters extrahieren
        odata_params = parsed_query.get("odata_params", {})
        
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
                    "failed": True
                }
            }
    
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