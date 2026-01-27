# FlexGuide4 - Intelligenter Logistik-Chatbot

> Ein KI-gestütztes Chatbot-System zur natürlichsprachlichen Analyse von Transportauftragsdaten.

**Entwickelt von THWS Student*Innen** im Rahmen des Kurses Business Analytics 2

---

## Was ist FlexGuide4?

FlexGuide4 wandelt natürliche Fragen in Deutsch in präzise Datenbank-Abfragen um und liefert sofort verständliche Antworten über Logistik-Aufträge.

**Beispiel:**
```
User: "Welche Fahraufträge stehen beim Jungheinrich als nächstes an?"
FlexGuide4: "Verfügbare Aufträge für JUNGHEINRICH (3 Stück):
1. Auftrag ID 60: MAGAZINO-PARK-01 → LEERGUT-02
2. Auftrag ID 89: HR-01-02 → MONTAGE-A1-01
3. Auftrag ID 45: STAPLER-PARK → UEBERGABE-03"
```

---

## Hauptfunktionen

### Ressourcen-basierter Zugriff
- **Supervisor-Modus**: Übersicht über alle Ressourcen (AGILOX, JUNGHEINRICH, MAGAZINO, etc.)
- **Ressourcen-Modus**: Individuelle Ansicht pro Fahrzeug/Stapler mit automatischer Filterung

### Intelligente Abfragen
- **Nächste Aufträge**: "Was kommt als nächstes?"
- **Statistiken**: "Wie viele Aufträge heute?" mit Gruppierung nach Status/Typ
- **Zeitfilter**: Heute, gestern, letzte Woche
- **Schichtfilter**: Früh-/Spätschicht-spezifische Auswertungen
- **Detail-Abfragen**: "Zeige mir Auftrag 89" oder "Details zum ersten Auftrag"

### Kontext-Bewusstsein
- Merkt sich vorherige Fragen
- Versteht Follow-up-Anfragen wie "Details zum ersten Auftrag"
- Session-basiertes Memory pro User

---

## Systemarchitektur

```
┌─────────────────┐
│  Natürliche     │  "Welche Aufträge stehen an?"
│  Sprache (DE)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Parser     │  GPT-4 → Strukturiertes JSON
│  (GPT-4)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OData Client   │  OAuth2 → API Request
│  + OAuth        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Calculation    │  Aggregationen & Gruppierungen
│  Engine         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │  Formatierte deutsche Antwort
│  Generator      │
└─────────────────┘
```

**4 Hauptkomponenten:**
1. **LLM Parser** - Natürliche Sprache → JSON
2. **OData Client** - API-Kommunikation mit OAuth2
3. **Calculation Engine** - Berechnungen & Aggregationen
4. **Response Generator** - JSON → Natürliche Antwort

---

## Quick Start

### Voraussetzungen
- Python 3.10+
- OpenAI API Key (GPT-4)
- Zugriff auf THWS Logistik-API

### Installation

```bash
# 1. Repository klonen
git clone <repository-url>
cd Flexus_Code

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Environment konfigurieren
cp env.template .env
# .env mit deinen Credentials befüllen

# 4. Web-Interface starten
python demo_app.py
```

Öffne Browser: `http://localhost:5000`

### `.env` Konfiguration

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# OAuth
OAUTH_TOKEN_URL=https://api.example.com/oauth/token
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# OData API
ODATA_BASE_URL=https://api.example.com/orders/Orders
```

---

## Verwendungsbeispiele

### Als Supervisor

```
"Welche Fahraufträge stehen als nächstes an?"
→ Übersicht aller Ressourcen mit nächstem Auftrag

"Was steht beim MAGAZINO an?"
→ Nächste Aufträge nur für MAGAZINO

"Wie viele Aufträge nach Status heute?"
→ Gruppierte Statistik
```

### Als Ressource (z.B. JUNGHEINRICH)

```
"Was sind meine nächsten Aufträge?"
→ Nächste Aufträge für JUNGHEINRICH

"Wie viele Aufträge hatte ich heute in der Frühschicht?"
→ Schicht-spezifische Statistik

"Zeige mir Details zum ersten Auftrag"
→ Vollständige Auftragsinformationen
```

### Detail-Abfragen

```
"Kannst du mir mehr Infos zu Auftrag 60 geben?"
→ Zeigt: ID, Status, Typ, Quelle, Ziel, Material, Menge, Fälligkeit, etc.
```

---

## Projektstruktur

```
Flexus_Code/
│
├── demo_app.py              # Web-Interface (Flask)
│
├── src/                     # Kern-Komponenten
│   ├── llm_parser.py        # GPT-4 Parser
│   ├── odata_client.py      # API Client
│   ├── oauth_handler.py     # Token Management
│   ├── calculation_engine.py # Berechnungs-Logik
│   └── response_generator.py # NLG
│
├── calculations/            # Berechnungs-Module
│   ├── count.py            # Zählen & Gruppieren
│   ├── sum.py              # Summen & Aggregationen
│   └── registry.py         # Modul-Registry
│
├── config/
│   └── settings.py         # Environment Config
│
├── logo/
│   └── logo-flexus.png     # FlexGuide4 Logo
│
└── requirements.txt        # Python Dependencies
```

---

## Features im Detail

### Ressourcen-Management

**9 Ressourcen-Typen:**
- SUPERVISOR (Zugriff auf alle)
- AGILOX
- JUNGHEINRICH
- MAGAZINO
- SAFELOG
- SCHUBMASTSTAPLER_LINKS
- SCHUBMASTSTAPLER_RECHTS
- STAPLER_WA
- STAPLER_WE

### Unterstützte Abfragen

| Kategorie | Beispiel |
|-----------|----------|
| **Nächste Aufträge** | "Was kommt als nächstes?" |
| **Statistiken** | "Wie viele Aufträge heute?" |
| **Zeitfilter** | "Aufträge von gestern" |
| **Schichtfilter** | "Aufträge der Frühschicht" |
| **Gruppierung** | "Aufträge nach Status" |
| **Status** | "Wie viele READY Aufträge?" |
| **Details** | "Zeige Auftrag 89" |
| **Quelle/Ziel** | "Aufträge von MAGAZINO-PARK-01" |

### Schicht-Erkennung

- **Frühschicht**: 06:00 - 14:00 Uhr
- **Spätschicht**: 14:00 - 22:00 Uhr
- **Automatisch**: "Heute noch" → aktuelle Schicht

---

## Technologie-Stack

- **Python 3.10+**
- **OpenAI GPT-4** - Natural Language Understanding
- **Flask** - Web Framework
- **OData v4** - API Standard
- **OAuth 2.0** - Authentifizierung

---

## Sicherheit

- API-Keys nur über Environment Variables
- `.env` nicht in Git (siehe `.gitignore`)
- OAuth Token Auto-Refresh
- Session-basierte User-Isolation
- Keine Credentials im Code

**WICHTIG:** Niemals `.env` committen!

---

## Testing

### Top 10 Test-Fragen

**Als Supervisor:**
1. Welche Fahraufträge stehen als nächstes an?
2. Was steht beim Jungheinrich an?
3. Wie viele Aufträge gab es heute?
4. Wie viele Aufträge nach Status heute?
5. Kannst du mir mehr Infos zu Auftrag 60 geben?

**Als Ressource (z.B. MAGAZINO):**
6. Was sind meine nächsten Aufträge?
7. Wie viele Aufträge hatte ich heute in der Frühschicht?
8. Zeige mir Details zum ersten Auftrag
9. Wie viele meiner Aufträge sind READY?
10. Welche Aufträge gehen von MAGAZINO-PARK-01 los?

---

## Contributing

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details zum Entwicklungs-Workflow.

---

## Team

**THWS Business Analytics Studenten:**
- Maike Knauer
- Johanna Kießling
- Dalilah Baumann
- Fabian Niebelschütz

**Institution:** Technische Hochschule Würzburg-Schweinfurt (THWS)  
**Kurs:** Business Analytics 2  
**Semester:** WS 2024/25

---

## Lizenz

Projektarbeit THWS - Nur für akademische Zwecke

---

## Support

Bei Fragen oder Problemen:
- Projektteam kontaktieren