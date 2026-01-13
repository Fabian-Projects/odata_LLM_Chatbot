"""
Komplette Pipeline mit Response Generator
LLM Parser -> OData Client -> Calculation Engine -> Response Generator
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm_parser import LLMQueryParser
from src.odata_client import ODataClient
from src.calculation_engine import CalculationEngine
from src.response_generator import ResponseGenerator
from config.settings import Config


def print_section(title: str):
    """Section Header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def run_complete_pipeline(user_query: str):
    """
    Führt komplette Pipeline aus
    
    Args:
        user_query: Natürliche Sprach-Anfrage
    """
    
    # Komponenten initialisieren
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    generator = ResponseGenerator(language="de")
    
    print(f"Frage: {user_query}\n")
    
    # 1. Parse
    print("[1/4] Parse Query...")
    parsed = parser.parse_query(user_query)
    
    # 2. OData Query
    print("[2/4] Hole Daten von API...")
    odata_result = client.execute_query(parsed)
    print(f"      {odata_result['count']} Records abgerufen")
    
    # 3. Calculation
    print("[3/4] Fuehre Berechnung aus...")
    calc_result = engine.process(odata_result, parsed.get('calculation'))
    
    # 4. Generate Response
    print("[4/4] Generiere Antwort...\n")
    response = generator.generate(calc_result, parsed.get('response_context'))
    
    # Ausgabe
    print("-" * 60)
    print(response)
    print("-" * 60)


def interactive_mode():
    """Interaktiver Chat-Modus mit Error Handling"""
    
    print_section("Logistics Chatbot - Interaktiver Modus")
    
    # Komponenten initialisieren
    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    generator = ResponseGenerator(language="de")
    
    print("Stelle Fragen zu den Fahrauftraegen")
    print("('exit' zum Beenden)\n")
    
    while True:
        try:
            user_input = input("Du: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nTschuess!")
                break
            
            if not user_input:
                continue
            
            print()
            
            # 1. Parse mit Error Check
            parsed = parser.parse_query(user_input)
            
            # 2. Prüfe ob beantwortbar
            if not parsed.get("isAnswerable", True):
                reason = parsed.get("reason", "Diese Frage kann ich nicht beantworten.")
                print(f"\nBot: {reason}")
                print("Ich kann dir nur Informationen über Fahraufträge geben.\n")
                print("-" * 60)
                continue
            
            # 3. Normale Pipeline
            odata_result = client.execute_query(parsed)
            calc_result = engine.process(odata_result, parsed.get('calculation'))
            response = generator.generate(calc_result, parsed.get('response_context'))
            
            print(f"\nBot: {response}\n")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\nAbgebrochen!")
            break
        except Exception as e:
            print(f"\nBot: Entschuldigung, da ist etwas schiefgelaufen.")
            print(f"Fehler: {e}\n")
            print("-" * 60)


def demo_mode():
    """Demo mit Beispiel-Fragen"""
    
    print_section("Logistics Chatbot - Demo Modus")
    
    test_queries = [
        "Wie viele Auftraege gibt es heute?",
        "Wie viele Auftraege pro Status?",
        "Zeige mir Auftrag mit ID 1",
        "Wie viele Auftraege nach Gruppe?",
    ]
    
    print(f"Fuehre {len(test_queries)} Beispiel-Anfragen aus...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}]")
        print("=" * 60)
        run_complete_pipeline(query)
        
        if i < len(test_queries):
            input("\nWeiter mit Enter...")
    
    print_section("Demo abgeschlossen")


def main():
    """Hauptfunktion"""
    
    # Config validieren
    if not Config.validate():
        print("\nBitte .env Datei mit allen Credentials erstellen!")
        return
    
    # Modus wählen
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_mode()
        elif sys.argv[1] == "--demo":
            demo_mode()
        else:
            print("Unbekannte Option. Nutze:")
            print("  --interactive : Interaktiver Chat")
            print("  --demo        : Demo mit Beispielen")
    else:
        # Standard: Interactive
        interactive_mode()


if __name__ == "__main__":
    main()