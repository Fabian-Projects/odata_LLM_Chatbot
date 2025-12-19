# Contributing Guide

Richtlinien für die Zusammenarbeit am Logistics Chatbot Projekt.

---

## Setup für Entwickler

### 1. Repository forken und klonen

```bash
git clone <your-fork-url>
cd logistics-chatbot
```

### 2. Branch für Feature erstellen

```bash
git checkout -b feature/dein-feature-name
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. .env Datei konfigurieren

```bash
cp .env.template .env
# Füge deine Credentials ein
```

---

## Code-Stil

### Python

- PEP 8 Style Guide befolgen
- Docstrings für alle Funktionen und Klassen
- Type Hints verwenden wo möglich
- Aussagekräftige Variablen- und Funktionsnamen

Beispiel:

```python
def calculate_sum(data: List[Dict[str, Any]], field: str) -> float:
    """
    Berechnet Summe über ein numerisches Feld
    
    Args:
        data: Liste mit Datensätzen
        field: Feldname für Summierung
        
    Returns:
        Summe als Float
    """
    values = [float(record.get(field, 0)) for record in data]
    return sum(values)
```

### Kommentare

- Nur wo nötig - Code sollte selbsterklärend sein
- Deutsche Kommentare für Projektspezifisches
- Englisch für allgemeinen Code

### Commits

Klare, beschreibende Commit-Messages:

```bash
git commit -m "Add sum calculation for quantity fields"
git commit -m "Fix OAuth token refresh bug"
git commit -m "Update README with new examples"
```

---

## Testing

### Manuelle Tests

Vor jedem Commit:

```bash
# LLM Parser testen
python3 demo_parser.py --interactive

# OData Client testen
python3 demo_odata.py --interactive

# Komplette Pipeline testen
python3 demo_chatbot.py
```

### Test-Anfragen

Stelle sicher, dass diese funktionieren:

- "Wie viele Aufträge gibt es heute?"
- "Wie viele Aufträge pro Status?"
- "Zeige mir Auftrag mit ID 1"
- "Gesamtmenge aller Aufträge"

---

## Neue Features hinzufügen

### Neue Berechnung hinzufügen

1. Erstelle neue Datei in `calculations/`:

```python
# calculations/my_calculation.py

from .base import BaseCalculation
from typing import Dict, Any, List

class MyCalculation(BaseCalculation):
    
    def calculate(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deine Berechnung implementieren
        """
        # Implementation
        return {
            "result": result,
            "type": "my_type"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return config.get("type") == "my_type"
```

2. In `calculations/__init__.py` importieren:

```python
from .my_calculation import MyCalculation
```

3. In `calculations/registry.py` registrieren:

```python
def _register_default_calculations(self):
    # ...
    self.register("my_type", MyCalculation())
```

4. Testen:

```bash
python3 demo_pipeline.py --interactive
```

---

## Pull Request Process

### 1. Code fertigstellen

- Alle Tests durchlaufen lassen
- Code formatieren
- Kommentare überprüfen

### 2. Commit und Push

```bash
git add .
git commit -m "Aussagekräftige Message"
git push origin feature/dein-feature-name
```

### 3. Pull Request erstellen

- Beschreibe was geändert wurde
- Füge Beispiele hinzu wenn relevant
- Verlinke Issues falls vorhanden

### 4. Review abwarten

- Feedback umsetzen
- Diskussionen konstruktiv führen

---

## Code Review Checklist

Beim Review von Pull Requests prüfen:

- [ ] Code folgt Style Guidelines
- [ ] Docstrings vorhanden
- [ ] Manuelle Tests durchgeführt
- [ ] Keine Credentials im Code
- [ ] .env nicht committed
- [ ] README aktualisiert falls nötig
- [ ] Keine breaking changes ohne Diskussion

---

## Projektstruktur verstehen

### src/ - Hauptkomponenten

- `llm_parser.py` - NL zu JSON
- `odata_client.py` - API Kommunikation
- `oauth_handler.py` - Token Management
- `calculation_engine.py` - Orchestrierung
- `response_generator.py` - Text-Generierung

### calculations/ - Berechnungslogik

- `base.py` - Abstrakte Basis
- `count.py` - Zähl-Operationen
- `sum.py` - Summen & Aggregationen
- `registry.py` - Verwaltung

### config/ - Konfiguration

- `settings.py` - Environment Variables

---

## Debugging

### Verbose Output aktivieren

In den Demo-Scripts ist Output bereits aktiviert.

### Python Debugger

```python
import pdb; pdb.set_trace()
```

### Logging aktivieren

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Häufige Probleme

### "Module not found"

```bash
# Stelle sicher, dass du im Projektverzeichnis bist
pwd

# Dependencies neu installieren
pip install -r requirements.txt
```

### "Config validation failed"

Prüfe `.env` Datei:

```bash
cat .env
```

Alle Werte müssen gesetzt sein.

### "Token refresh failed"

OAuth Credentials prüfen:
- Client ID korrekt?
- Client Secret korrekt?
- Token URL erreichbar?

---

## Fragen?

- Issue im GitHub Repository erstellen
- Projektgruppe kontaktieren
- README und Dokumentation konsultieren

---

Danke für deine Mitarbeit!