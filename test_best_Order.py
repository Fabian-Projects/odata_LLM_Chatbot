import requests
import json

BASE_URL = "https://thws-projekt-flexguide-flexus-flexguide-core.cfapps.eu20-001.hana.ondemand.com"
TOKEN_URL = "https://studierende-90uhml1i.authentication.eu20.hana.ondemand.com/oauth/token"
CLIENT_ID = "sb-thws-projekt-flexguide-flexguide!t140281"
CLIENT_SECRET = "e28189b8-6aa9-45a4-88e2-89c2c1ad9063$kpuf6YNb26rrtr60g7k_VXOVt8adUpiP5uzXQwoSpm4="

def get_token():
    r = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    })
    return r.json()["access_token"]

def test_api(resource_id, position):
    token = get_token()
    
    url = f"{BASE_URL}/api_core/orders/assignBestOrdersTest"
    body = {
        "resourceId": resource_id,
        "currentPosition": {"poiIdOrName": position}
    }
    
    r = requests.post(url, json=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    
    print(f"\nStatus: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    return r.json()

if __name__ == "__main__":
    result = test_api("STAPLER_WA", "STAPLER-PARK-WA")