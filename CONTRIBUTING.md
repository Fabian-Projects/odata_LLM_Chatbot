# Contributing zu FlexGuide4

Danke für dein Interesse am FlexGuide4 Projekt! Diese Guidelines helfen dir beim erfolgreichen Beitragen.

---

## Quick Start für Entwickler

### Setup

```bash
# 1. Repository klonen
git clone <repository-url>
cd Flexus_Code

# 2. Branch erstellen
git checkout -b feature/dein-feature

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. .env konfigurieren
cp env.template .env
# Credentials eintragen
```

---

## Code-Standards

### Python Style

- **PEP 8** konform
- **Type Hints** für alle Funktionen
- **Docstrings** für alle öffentlichen Methoden
- **Aussagekräftige Namen** (keine Abkürzungen)

**Beispiel:**

```python
def calculate_order_count(
    data: List[Dict[str, Any]], 
    grouping_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Zählt Aufträge mit optionaler Gruppierung.
    
    Args:
        data: Liste mit Auftrags-Dictionaries
        grouping_field: Feld für Gruppierung (optional)
        
    Returns:
        Dictionary mit Zählergebnissen
    """
    # Implementation
    pass
```

### Commit Messages

Klar und beschreibend:

```bash
 "Add shift filter for order queries"
 "Fix OAuth token refresh timeout"
 "Update README with new examples"

 "fix bug"
 "update stuff"
 "wip"
```

---

## Architektur verstehen

### Komponenten-Übersicht

```
src/
├── llm_parser.py          # NL → JSON (GPT-4)
├── odata_client.py        # API Communication
├── oauth_handler.py       # Token Management
├── calculation_engine.py  # Berechnungs-Orchestrierung
└── response_generator.py  # JSON → NL
```

### Data Flow

```
User Input → LLM Parser → OData Client → Calculation Engine → Response Generator → Output
```

---

# Neue Features hinzufügen

### 1. Neue Berechnung

**Datei:** `calculations/my_calculation.py`

```python
from .base import BaseCalculation
from typing import Dict, Any, List

class MyCalculation(BaseCalculation):
    def calculate(
        self, 
        data: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deine Berechnung."""
        result = {}  # Implementation
        return {
            "result": result,
            "type": "my_type"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return config.get("type") == "my_type"
```

**Registrieren in** `calculations/registry.py`:

```python
def _register_default_calculations(self):
    # ...
    self.register("my_type", MyCalculation())
```

### 2. Neue Intent im Parser

**In** `src/llm_parser.py` → `_build_system_prompt()`:

```python
# Beispiel im System Prompt hinzufügen
User: "Deine neue Frage"
{{
  "intent": "dein_intent",
  "odata_params": {{ ... }},
  "calculation": {{ ... }}
}}
```

**In** `demo_app.py` → `bot_reply()`:

```python
if parsed.get("intent") == "dein_intent":
    # Implementation
    return response
```

---

## Testing vor Pull Request

### Manuelle Tests

```bash
# Web-Interface starten
python demo_app.py
```

**Test-Fragen durchgehen:**
1. Welche Fahraufträge stehen als nächstes an?
2. Wie viele Aufträge heute?
3. Details zu Auftrag 60
4. Was sind meine nächsten Aufträge?

### Code-Qualität

```bash
# Syntax Check
python -m py_compile src/*.py

# Type Check (optional)
mypy src/
```

---

## Pull Request Workflow

### 1. Änderungen committen

```bash
git add .
git commit -m "Beschreibende Message"
git push origin feature/dein-feature
```

### 2. Pull Request erstellen

**Beschreibung sollte enthalten:**
- Was wurde geändert?
- Warum wurde es geändert?
- Wie testen? (Beispiel-Fragen)

**Beispiel:**

```markdown
## Änderungen
- Neuer Intent "material_summary" hinzugefügt
- Gruppierung nach Material-Typ

## Testing
Fragen: 
- "Wie viele Aufträge pro Material?"
- "Welche Materialien wurden heute transportiert?"
```

### 3. Code Review

- Feedback konstruktiv umsetzen
- Tests aktualisieren falls nötig
- Dokumentation ergänzen

---

## Review Checklist

**Vor dem Merge:**

- [ ] Code folgt PEP 8
- [ ] Type Hints vorhanden
- [ ] Docstrings vollständig
- [ ] Manuelle Tests bestanden
- [ ] Keine `.env` oder Secrets committed
- [ ] README aktualisiert (falls nötig)
- [ ] Keine Breaking Changes ohne Diskussion

---

## Fragen?

- Team kontaktieren
- README konsultieren