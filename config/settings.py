"""
Konfiguration für das Logistics Chatbot System
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Zentrale Konfiguration"""
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
    
    # OAuth
    OAUTH_TOKEN_URL = os.getenv("OAUTH_TOKEN_URL", "")
    OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")
    
    # OData API
    ODATA_BASE_URL = os.getenv("ODATA_BASE_URL", "")
    
    # Query Defaults
    DEFAULT_TOP_LIMIT = 100
    MAX_TOP_LIMIT = 1000
    
    # Conversation
    MAX_HISTORY_LENGTH = 3
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Prüft ob alle essentiellen Configs gesetzt sind"""
        required = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("OAUTH_TOKEN_URL", cls.OAUTH_TOKEN_URL),
            ("OAUTH_CLIENT_ID", cls.OAUTH_CLIENT_ID),
            ("OAUTH_CLIENT_SECRET", cls.OAUTH_CLIENT_SECRET),
            ("ODATA_BASE_URL", cls.ODATA_BASE_URL),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            print(f"Fehlende Konfiguration: {', '.join(missing)}")
            return False
        
        print("Konfiguration vollständig")
        return True


def get_config() -> Config:
    """Gibt Config-Instanz zurück"""
    return Config()