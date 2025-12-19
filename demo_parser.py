"""
Demo Script für LLM Query Parser
Testet verschiedene Anfrage-Typen
"""

import json
import sys
import os

# Pfad-Fix für Imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm_parser import LLMQueryParser
from config.settings import Config


def print_section(title: str):
    """Section-Header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def pretty_print_result(user_query: str, result: dict):
    """Formatiert Ergebnis"""
    print(f"User: {user_query}")
    print(f"\nParsed Output:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n" + "-"*60)


def main():
    """Hauptfunktion für Demo"""
    
    print_section("LLM Query Parser Demo")
    
    # Config prüfen
    if not Config.validate():
        print("\nBitte .env Datei mit OPENAI_API_KEY erstellen!")
        print("Vorlage: .env.template")
        return
    
    # Parser initialisieren
    print("Initialisiere LLM Parser...")
    parser = LLMQueryParser(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL
    )
    print("Parser bereit!\n")
    
    # Test-Queries
    test_queries = [
        # Einfache Abfragen
        "Zeige mir Auftrag mit ID 3",
        "Was hatte ID 3 geladen?",
        
        # Zeitbasierte Queries
        "Wie viele Aufträge gab es heute?",
        "Zeige mir alle Aufträge von gestern",
        
        # Berechnungen
        "Wie viele Aufträge pro Gruppe heute?",
        "Durchschnittliche Anzahl Aufträge pro Ressource diese Woche",
        
        # Komplexere Queries
        "Welche Aufträge sind von HR-01-08 nach HR-02-02 gefahren?",
        "Zeige mir alle UMLAGERUNG Aufträge mit Status READY",
        
        # Gruppierungen
        "Wie viele Aufträge nach Auftragstyp?",
        "Auslastung nach Gruppe für heute"
    ]
    
    # Interaktiver Modus?
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print_section("Interaktiver Modus")
        print("Gib deine Fragen ein (oder 'exit' zum Beenden)\n")
        
        while True:
            try:
                user_input = input("Du: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nTschuess!")
                    break
                
                if not user_input:
                    continue
                
                result = parser.parse_query(user_input)
                pretty_print_result(user_input, result)
                
            except KeyboardInterrupt:
                print("\n\nAbgebrochen!")
                break
            except Exception as e:
                print(f"\nFehler: {e}\n")
    
    else:
        # Test-Modus mit vorgefertigten Queries
        print_section("Test-Modus (Vorgefertigte Queries)")
        print(f"Teste {len(test_queries)} Beispiel-Anfragen...\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[{i}/{len(test_queries)}]")
            
            try:
                result = parser.parse_query(query)
                pretty_print_result(query, result)
                
            except Exception as e:
                print(f"Fehler bei Query '{query}': {e}\n")
        
        print_section("Test abgeschlossen")
        print("\nTipp: Starte mit --interactive für eigene Fragen:")
        print("   python3 demo_parser.py --interactive\n")


if __name__ == "__main__":
    main()