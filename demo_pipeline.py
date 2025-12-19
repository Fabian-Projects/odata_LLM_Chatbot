"""
Komplette Pipeline Demo
LLM Parser -> OData Client -> Calculation Engine
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm_parser import LLMQueryParser
from src.odata_client import ODataClient
from src.calculation_engine import CalculationEngine
from config.settings import Config


def print_section(title: str):
    """Section Header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def print_result(result: dict):
    """Formatierte Ausgabe der Ergebnisse"""
    
    if result.get("has_calculation"):
        # Mit Berechnung
        calc_result = result["calculation_result"]
        calc_type = result["calculation_type"]
        
        print(f"\nBerechnung: {calc_type}")
        print(f"Basis-Daten: {result['raw_data_count']} Records\n")
        
        if "groups" in calc_result:
            # Gruppierte Ergebnisse
            print(f"Gruppiert nach: {calc_result.get('grouped_by')}")
            print(f"Anzahl Gruppen: {calc_result.get('group_count')}\n")
            
            for group, value in calc_result["groups"].items():
                if isinstance(value, dict):
                    # Mit Prozent
                    print(f"  {group}: {value['count']} ({value['percentage']}%)")
                else:
                    # Nur Wert
                    print(f"  {group}: {value}")
            
            if "total" in calc_result:
                print(f"\nGesamt: {calc_result['total']}")
        
        else:
            # Einfaches Ergebnis
            if "total" in calc_result:
                print(f"Gesamt: {calc_result['total']}")
            if "result" in calc_result:
                print(f"Ergebnis: {calc_result['result']}")
    
    else:
        # Ohne Berechnung - zeige Rohdaten
        print(f"\nAnzahl Records: {result['count']}\n")
        
        if result['count'] > 0:
            print("Records:")
            for i, record in enumerate(result.get('raw_data', [])[:5], 1):
                print(f"\n[{i}]")
                for key, value in list(record.items())[:5]:
                    print(f"  {key}: {value}")
            
            if result['count'] > 5:
                print(f"\n... und {result['count'] - 5} weitere")


def test_count_simple():
    """Test 1: Einfaches Zählen"""
    print_section("Test 1: Einfaches Zaehlen")
    
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    
    # User Query
    user_query = "Wie viele Auftraege gibt es heute?"
    print(f"Frage: {user_query}\n")
    
    # 1. Parse
    parsed = parser.parse_query(user_query)
    print("Parsed:")
    print(f"  Filter: {parsed['odata_params'].get('$filter')}")
    print(f"  Calculation: {parsed['calculation']['type']}")
    
    # 2. OData Query
    odata_result = client.execute_query(parsed)
    print(f"\nOData: {odata_result['count']} Records abgerufen")
    
    # 3. Calculation
    final_result = engine.process(odata_result, parsed.get('calculation'))
    
    print("\nErgebnis:")
    print_result(final_result)


def test_count_grouped():
    """Test 2: Gruppiertes Zählen"""
    print_section("Test 2: Gruppiertes Zaehlen")
    
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    
    # User Query
    user_query = "Wie viele Auftraege pro Status heute?"
    print(f"Frage: {user_query}\n")
    
    # Pipeline
    parsed = parser.parse_query(user_query)
    print(f"Gruppierung: {parsed['calculation'].get('grouping_field')}")
    
    odata_result = client.execute_query(parsed)
    final_result = engine.process(odata_result, parsed.get('calculation'))
    
    print("\nErgebnis:")
    print_result(final_result)


def test_sum():
    """Test 3: Summen-Berechnung"""
    print_section("Test 3: Summen-Berechnung")
    
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    
    # User Query
    user_query = "Gesamtmenge aller Auftraege heute"
    print(f"Frage: {user_query}\n")
    
    # Pipeline
    parsed = parser.parse_query(user_query)
    odata_result = client.execute_query(parsed)
    final_result = engine.process(odata_result, parsed.get('calculation'))
    
    print("\nErgebnis:")
    print_result(final_result)


def test_no_calculation():
    """Test 4: Ohne Berechnung (reine Abfrage)"""
    print_section("Test 4: Reine Abfrage ohne Berechnung")
    
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    
    # User Query
    user_query = "Zeige mir Auftrag mit ID 1"
    print(f"Frage: {user_query}\n")
    
    # Pipeline
    parsed = parser.parse_query(user_query)
    odata_result = client.execute_query(parsed)
    final_result = engine.process(odata_result, parsed.get('calculation'))
    
    print("\nErgebnis:")
    print_result(final_result)


def interactive_mode():
    """Interaktiver Modus mit kompletter Pipeline"""
    print_section("Interaktiver Modus - Komplette Pipeline")
    
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    
    print("Stelle Fragen in natuerlicher Sprache")
    print("Die komplette Pipeline wird ausgefuehrt:")
    print("  Parser -> OData -> Calculation -> Ergebnis\n")
    print("('exit' zum Beenden)\n")
    
    while True:
        try:
            user_input = input("Du: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nTschuess!")
                break
            
            if not user_input:
                continue
            
            print("\n" + "-"*60)
            
            # 1. Parse
            parsed = parser.parse_query(user_input)
            
            # 2. OData
            odata_result = client.execute_query(parsed)
            
            # 3. Calculation
            final_result = engine.process(odata_result, parsed.get('calculation'))
            
            # 4. Output
            print_result(final_result)
            
            print("\n" + "-"*60)
            
        except KeyboardInterrupt:
            print("\n\nAbgebrochen!")
            break
        except Exception as e:
            print(f"\nFehler: {e}\n")


def main():
    """Hauptfunktion"""
    
    print_section("Komplette Pipeline Demo")
    
    # Config validieren
    if not Config.validate():
        print("\nBitte .env Datei mit allen Credentials erstellen!")
        return
    
    # Tests oder Interaktiv?
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        print("Fuehre automatische Tests aus...\n")
        
        test_count_simple()
        test_count_grouped()
        test_sum()
        test_no_calculation()
        
        print_section("Tests abgeschlossen")
        print("\nTipp: Starte mit --interactive fuer eigene Fragen")
        print("   python3 demo_pipeline.py --interactive\n")


if __name__ == "__main__":
    main()