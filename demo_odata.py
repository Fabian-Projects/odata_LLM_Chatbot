"""
Demo Script für OData Client
Testet Verbindung und Queries
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.odata_client import ODataClient
from src.llm_parser import LLMQueryParser
from config.settings import Config


def print_section(title: str):
    """Section Header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_connection():
    """Test 1: Verbindung testen"""
    print_section("Test 1: Verbindungstest")
    
    client = ODataClient(
        base_url=Config.ODATA_BASE_URL,
        token_url=Config.OAUTH_TOKEN_URL,
        client_id=Config.OAUTH_CLIENT_ID,
        client_secret=Config.OAUTH_CLIENT_SECRET
    )
    
    success = client.test_connection()
    
    if success:
        print("\nVerbindung erfolgreich!")
        return client
    else:
        print("\nVerbindung fehlgeschlagen!")
        return None


def test_simple_query(client: ODataClient):
    """Test 2: Einfache Query"""
    print_section("Test 2: Einfache Query")
    
    # Manuelles Query-Dict
    test_query = {
        "odata_params": {
            "$top": 5,
            "$select": "ID,group,state,createdAt"
        }
    }
    
    print("Query:")
    print(json.dumps(test_query, indent=2))
    
    result = client.execute_query(test_query)
    
    print(f"\nErgebnis:")
    print(f"Anzahl Records: {result['count']}")
    
    if result['count'] > 0:
        print(f"\nErstes Record:")
        print(json.dumps(result['value'][0], indent=2, ensure_ascii=False))


def test_with_filter(client: ODataClient):
    """Test 3: Query mit Filter"""
    print_section("Test 3: Query mit Filter")
    
    test_query = {
        "odata_params": {
            "$filter": "state eq 'READY'",
            "$select": "ID,state,group",
            "$top": 10
        }
    }
    
    print("Query:")
    print(json.dumps(test_query, indent=2))
    
    result = client.execute_query(test_query)
    
    print(f"\nErgebnis:")
    print(f"Anzahl Records: {result['count']}")
    
    if result['count'] > 0:
        print(f"\nRecords:")
        for record in result['value'][:3]:
            print(f"  ID: {record.get('ID')}, State: {record.get('state')}, Group: {record.get('group')}")


def test_llm_to_odata(client: ODataClient):
    """Test 4: LLM Parser + OData Client"""
    print_section("Test 4: LLM Parser -> OData Client")
    
    # Parser initialisieren
    parser = LLMQueryParser(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL
    )
    
    # Natürliche Sprache
    user_query = "Zeige mir die letzten 3 Aufträge"
    
    print(f"User Frage: {user_query}")
    
    # Parser
    parsed = parser.parse_query(user_query)
    print(f"\nGeparst:")
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    
    # OData Query
    result = client.execute_query(parsed)
    print(f"\nOData Ergebnis:")
    print(f"Anzahl Records: {result['count']}")
    
    if result['count'] > 0:
        print(f"\nRecords:")
        for record in result['value']:
            print(f"  ID: {record.get('ID')}, Group: {record.get('group')}, Created: {record.get('createdAt')}")


def interactive_mode(client: ODataClient):
    """Interaktiver Modus"""
    print_section("Interaktiver Modus")
    
    parser = LLMQueryParser(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL
    )
    
    print("Stelle Fragen in natuerlicher Sprache")
    print("(oder 'exit' zum Beenden)\n")
    
    while True:
        try:
            user_input = input("Du: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nTschuess!")
                break
            
            if not user_input:
                continue
            
            # Parse
            parsed = parser.parse_query(user_input)
            
            print(f"\nParsed Query:")
            print(json.dumps(parsed.get('odata_params'), indent=2))
            
            # Execute
            result = client.execute_query(parsed)
            
            print(f"\nErgebnis: {result['count']} Records")
            
            if result['count'] > 0:
                # Zeige erste 5 Records
                for i, record in enumerate(result['value'][:5], 1):
                    print(f"\n[{i}] ID: {record.get('ID')}")
                    print(f"    Group: {record.get('group')}")
                    print(f"    State: {record.get('state')}")
                    print(f"    Created: {record.get('createdAt')}")
                
                if result['count'] > 5:
                    print(f"\n... und {result['count'] - 5} weitere")
            
            print("\n" + "-"*60)
            
        except KeyboardInterrupt:
            print("\n\nAbgebrochen!")
            break
        except Exception as e:
            print(f"\nFehler: {e}\n")


def main():
    """Hauptfunktion"""
    
    print_section("OData Client Demo")
    
    # Config validieren
    if not Config.validate():
        print("\nBitte .env Datei mit allen Credentials erstellen!")
        return
    
    # Verbindung testen
    client = test_connection()
    
    if not client:
        print("\nAbbruch: Keine Verbindung zur API")
        return
    
    # Tests durchführen
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode(client)
    else:
        test_simple_query(client)
        test_with_filter(client)
        test_llm_to_odata(client)
        
        print_section("Tests abgeschlossen")
        print("\nTipp: Starte mit --interactive für eigene Fragen")
        print("   python3 demo_odata.py --interactive\n")


if __name__ == "__main__":
    main()