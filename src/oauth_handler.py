"""
OAuth Token Handler für OData API
Verwaltet Token-Abruf und -Erneuerung
"""

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from typing import Optional


class OAuthTokenHandler:
    """Verwaltet OAuth Token für OData API"""
    
    def __init__(self, token_url: str, client_id: str, client_secret: str):
        """
        Args:
            token_url: OAuth Token Endpoint
            client_id: Client ID
            client_secret: Client Secret
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Gibt gültigen Access Token zurück
        
        Args:
            force_refresh: Erzwingt neuen Token auch wenn aktueller noch gültig
            
        Returns:
            Access Token String
            
        Raises:
            Exception: Wenn Token-Abruf fehlschlägt
        """
        if force_refresh or not self._is_token_valid():
            self._refresh_token()
        
        return self._token
    
    def _is_token_valid(self) -> bool:
        """
        Prüft ob Token noch gültig ist
        
        Returns:
            True wenn Token vorhanden und noch gültig
        """
        if not self._token or not self._token_expires_at:
            return False
        
        # Token 5 Minuten vor Ablauf als ungültig betrachten
        buffer = timedelta(minutes=5)
        return datetime.now() < (self._token_expires_at - buffer)
    
    def _refresh_token(self):
        """
        Holt neuen Token von OAuth Server
        
        Raises:
            Exception: Bei Fehler im Token-Abruf
        """
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            response.raise_for_status()
            
            token_data = response.json()
            self._token = token_data.get("access_token")
            
            if not self._token:
                raise Exception("Kein access_token in Response")
            
            # Berechne Ablaufzeit (meist 'expires_in' in Sekunden)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"Token erfolgreich abgerufen (gueltig bis {self._token_expires_at.strftime('%Y-%m-%d %H:%M:%S')})")
            
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Token-Abruf: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response Status: {e.response.status_code}")
                print(f"Response Body: {e.response.text}")
            raise Exception(f"Token-Abruf fehlgeschlagen: {e}")
    
    def clear_token(self):
        """Löscht gespeicherten Token (für Logout/Reset)"""
        self._token = None
        self._token_expires_at = None