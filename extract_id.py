"""
Extract specific ID
"""

import json
import sys
from src.odata_client import ODataClient
from config.settings import Config
from dotenv import load_dotenv

load_dotenv()

# ID aus Command Line oder Default
order_id = sys.argv[1] if len(sys.argv) > 1 else "60"

client = ODataClient(
    Config.ODATA_BASE_URL,
    Config.OAUTH_TOKEN_URL,
    Config.OAUTH_CLIENT_ID,
    Config.OAUTH_CLIENT_SECRET
)

query = {
    "odata_params": {
        "$filter": f"ID eq '{order_id}'"
    }
}

result = client.execute_query(query)
orders = result.get("value", [])

if not orders:
    print(f"Keine Daten fuer ID {order_id}")
else:
    print(json.dumps(orders[0], indent=2, ensure_ascii=False))