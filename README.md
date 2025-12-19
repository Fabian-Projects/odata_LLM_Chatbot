# Logistics Chatbot System

Ein intelligentes Chatbot-System für die Analyse von Logistik-Daten. Das System wandelt natürliche Sprach-Anfragen in OData-Queries um und führt Berechnungen auf Transportauftragsdaten durch.

Entwickelt als Projektarbeit im Rahmen des Kurses "Business Analytics 2" an der THWS.

---

## Überblick

Das System besteht aus vier Hauptkomponenten:

1. **LLM Parser** - Wandelt natürliche Sprache in strukturierte OData-Queries
2. **OData Client** - Führt API-Anfragen mit OAuth-Authentifizierung durch
3. **Calculation Engine** - Berechnet Aggregationen und Gruppierungen
4. **Response Generator** - Erstellt natürlichsprachige Antworten

---

## Systemarchitektur

```
User Input (natürliche Sprache)
         |
         v
    LLM Parser (GPT-4)
         |
         v
    Strukturiertes JSON
    {
      "odata_params": {...},
      "calculation": {...}
    }
         |
         v
    OAuth Handler --> Token Abruf
         |
         v
    OData Client --> API Request
         |
         v
    Rohdaten (JSON)
         |
         v
    Calculation Engine --> Berechnungen
         |
         v
    Response Generator --> Natürliche Antwort
         |
         v
    Output (formatierter Text)
```

---

## Voraussetzungen

- Python 3.10 oder höher
- OpenAI API Key (GPT-4 Zugriff)
- Zugriff auf die THWS Logistics OData API
  - OAuth Client ID
  - OAuth Client Secret
  - API Base URL

---

## Installation

### 1. Repository klonen

```bash
git clone <repository-url>
cd logistics-chatbot
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Umgebungsvariablen konfigurieren

Erstelle eine `.env` Datei im Projektverzeichnis:

```bash
cp .env.template .env
```

Füge deine Credentials ein:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# OAuth Configuration
OAUTH_TOKEN_URL=https://your-oauth-endpoint/oauth/token
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# OData API Configuration
ODATA_BASE_URL=https://your-api-endpoint/orders/Orders
```

---

## Verwendung

### Interaktiver Chatbot-Modus

```bash
python3 demo_chatbot.py
```

Beispiel-Session:
```
Du: Wie viele Aufträge gibt es heute?

Bot: Insgesamt: 42 Fahraufträge
```

### Demo-Modus mit Beispielen

```bash
python3 demo_chatbot.py --demo
```

Führt vordefinierte Beispiel-Anfragen aus.

### Einzelne Komponenten testen

```bash
# LLM Parser testen
python3 demo_parser.py --interactive

# OData Client testen
python3 demo_odata.py --interactive

# Komplette Pipeline ohne Response Generator
python3 demo_pipeline.py --interactive
```

---

## Projektstruktur

```
logistics-chatbot/
│
├── src/
│   ├── llm_parser.py          # LLM-basierter Query Parser
│   ├── oauth_handler.py        # OAuth Token Management
│   ├── odata_client.py         # OData API Client
│   ├── calculation_engine.py   # Berechnungs-Orchestrierung
│   └── response_generator.py   # Natural Language Generation
│
├── calculations/
│   ├── base.py                 # Basis-Klasse für Berechnungen
│   ├── count.py                # Count-Berechnungen
│   ├── sum.py                  # Summen & Aggregationen
│   └── registry.py             # Calculation Registry
│
├── config/
│   └── settings.py             # Konfiguration & Environment Variables
│
├── demo_chatbot.py             # Haupt-Demo (komplette Pipeline)
├── demo_parser.py              # LLM Parser Demo
├── demo_odata.py               # OData Client Demo
├── demo_pipeline.py            # Pipeline Demo (ohne Response Generator)
│
├── requirements.txt            # Python Dependencies
├── .env.template               # Template für Environment Variables
├── .gitignore                  # Git Ignore Rules
└── README.md                   # Diese Datei
```

---

## Funktionsweise

### 1. LLM Parser

Eingabe: Natürliche Sprache
```
"Wie viele Aufträge gibt es pro Gruppe heute?"
```

Ausgabe: Strukturiertes JSON
```json
{
  "odata_params": {
    "$filter": "createdAt ge 2025-12-19T00:00:00Z and createdAt lt 2025-12-20T00:00:00Z",
    "$select": "ID,group",
    "$top": 100
  },
  "calculation": {
    "type": "count",
    "grouping_field": "group"
  }
}
```

### 2. OData Client

- Holt OAuth Token (automatische Erneuerung)
- Baut OData-konforme URL
- Führt HTTP Request aus
- Gibt Rohdaten zurück

### 3. Calculation Engine

Unterstützte Berechnungen:
- **Count** - Zählen mit/ohne Gruppierung
- **Sum** - Summen mit/ohne Gruppierung
- **Aggregation** - avg, min, max

Erweiterbar durch Registry-Pattern.

### 4. Response Generator

Wandelt Berechnungsergebnisse in lesbare deutsche Antworten um:

```
Insgesamt: 42 Fahraufträge

Aufgeteilt nach Gruppe:
  Andis_Stapler: 15 (35.7%)
  Marias_Team: 27 (64.3%)

Meiste Aufträge: Marias_Team mit 27 Aufträgen
```

---

## Unterstützte Anfragen

### Einfache Abfragen
- "Zeige mir Auftrag mit ID 3"
- "Welche Aufträge wurden heute erstellt?"

### Berechnungen
- "Wie viele Aufträge gibt es heute?"
- "Wie viele Aufträge pro Status?"
- "Wie viele Aufträge nach Gruppe?"
- "Gesamtmenge aller Aufträge"

### Zeitbasierte Queries
- "Aufträge von heute"
- "Aufträge von gestern"
- "Aufträge dieser Woche"

### Gruppierungen

Gruppierung ist nach jedem Feld möglich:
- Nach Status: `state`
- Nach Gruppe: `group`
- Nach Auftragstyp: `type_ID`
- Nach Ressource: `assignedResource_ID`
- etc.

---

## Erweiterungen

### Neue Berechnungen hinzufügen

1. Erstelle neue Klasse in `calculations/`:

```python
from .base import BaseCalculation

class MyCalculation(BaseCalculation):
    def calculate(self, data, config):
        # Implementierung
        return result
    
    def validate_config(self, config):
        return config.get("type") == "my_type"
```

2. Registriere in `calculations/registry.py`:

```python
def _register_default_calculations(self):
    # ...
    self.register("my_type", MyCalculation())
```

---

## Konfiguration

### OpenAI Model

Standard: `gpt-4o` (empfohlen für Preis/Leistung)

Alternativen:
- `gpt-4-turbo-preview` - Älteres Modell
- `gpt-4o-mini` - Günstiger, etwas weniger präzise

In `.env` anpassen:
```env
OPENAI_MODEL=gpt-4o
```

### OData Query Limits

In `config/settings.py`:
```python
DEFAULT_TOP_LIMIT = 100
MAX_TOP_LIMIT = 1000
```

---

## Sicherheit

- API-Keys werden über Environment Variables verwaltet
- `.env` Datei ist in `.gitignore` enthalten
- OAuth Token wird automatisch erneuert
- Keine Credentials im Code

**WICHTIG:** Niemals `.env` in Git committen!

---

## Fehlerbehandlung

Das System fängt Fehler auf allen Ebenen ab:

- **LLM Parser** - Fallback bei Parse-Fehlern
- **OAuth Handler** - Retry bei Token-Problemen
- **OData Client** - HTTP Error Handling
- **Calculation Engine** - Gibt Rohdaten bei Fehler zurück

Bei Problemen: Demo-Scripts mit `--interactive` starten für detaillierte Fehlerausgaben.

---

## Lizenz

Projektarbeit THWS - Business Analytics 2

---

## Autoren

Entwickelt von Studierenden der THWS im Rahmen der Logistics Systems Vorlesung.

---

## Kontakt

Bei Fragen oder Problemen: Issue im GitHub Repository erstellen.