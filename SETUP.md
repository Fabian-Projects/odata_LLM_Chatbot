# Setup Guide

Detaillierte Anleitung für die Einrichtung des Logistics Chatbot Systems.

---

## Systemanforderungen

- macOS, Linux oder Windows
- Python 3.10 oder höher
- Git
- Internet-Verbindung
- Terminal/Command Line Zugang

---

## Schritt-für-Schritt Installation

### 1. Python Version prüfen

```bash
python3 --version
```

Sollte ausgeben: `Python 3.10.x` oder höher

Falls Python nicht installiert ist:
- macOS: `brew install python`
- Linux: `sudo apt install python3`
- Windows: Download von python.org

### 2. Repository klonen

```bash
git clone <repository-url>
cd logistics-chatbot
```

### 3. Virtual Environment erstellen (empfohlen)

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 4. Dependencies installieren

```bash
pip install -r requirements.txt
```

Dies installiert:
- openai - GPT API
- requests - HTTP Requests
- python-dotenv - Environment Variables
- pandas - Datenverarbeitung
- flask - Web Framework (für später)

### 5. Environment Variables konfigurieren

```bash
# Template kopieren
cp .env.template .env

# Mit Editor öffnen
nano .env
# oder
vim .env
# oder
code .env
```

Erforderliche Werte eintragen:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxx...
OPENAI_MODEL=gpt-4o

# OAuth
OAUTH_TOKEN_URL=https://studierende-xxx.authentication.eu20.hana.ondemand.com/oauth/token
OAUTH_CLIENT_ID=xxx
OAUTH_CLIENT_SECRET=xxx

# OData
ODATA_BASE_URL=https://thws-projekt-xxx.cfapps.eu20-001.hana.ondemand.com/api_core/orders/Orders
```

### 6. Konfiguration testen

```bash
python3 -c "from config.settings import Config; Config.validate()"
```

Sollte ausgeben: `Konfiguration vollständig`

Falls Fehler: Prüfe .env Datei auf fehlende Werte

---

## API Keys beschaffen

### OpenAI API Key

1. Gehe zu https://platform.openai.com
2. Registriere einen Account
3. Navigiere zu API Keys
4. Erstelle neuen Key
5. Kopiere Key in .env

Kosten: ca. 0.01-0.05 EUR pro Anfrage (abhängig vom Modell)

### THWS OAuth Credentials

Werden vom Projektbetreuer bereitgestellt:
- Client ID
- Client Secret
- Token URL
- API Base URL

---

## Erste Schritte

### Test 1: LLM Parser

```bash
python3 demo_parser.py --interactive
```

Gib ein: "Wie viele Aufträge gibt es heute?"

Erwartete Ausgabe:
```json
{
  "odata_params": {
    "$filter": "createdAt ge 2025-12-19T...",
    ...
  }
}
```

### Test 2: OData Client

```bash
python3 demo_odata.py
```

Sollte Verbindung herstellen und Test-Query ausführen.

### Test 3: Kompletter Chatbot

```bash
python3 demo_chatbot.py
```

Stelle Fragen in natürlicher Sprache.

---

## Troubleshooting

### Problem: "No module named 'openai'"

Lösung:
```bash
pip install -r requirements.txt
```

### Problem: "Config validation failed"

Prüfe ob alle Werte in .env gesetzt sind:
```bash
cat .env
```

### Problem: "Token refresh failed"

Mögliche Ursachen:
- Client ID falsch
- Client Secret falsch
- Token URL nicht erreichbar
- Keine Internet-Verbindung

Lösung: Credentials vom Betreuer erneut anfordern

### Problem: "HTTP 401 Unauthorized"

Token ist abgelaufen oder ungültig.

Lösung:
```bash
# Python-Script neu starten
# Token wird automatisch erneuert
```

### Problem: "Connection Timeout"

API nicht erreichbar.

Lösung:
- Internet-Verbindung prüfen
- VPN verbunden? (falls erforderlich)
- Firewall prüfen

---

## Projekt-Struktur verstehen

Nach dem Setup sollte die Struktur so aussehen:

```
logistics-chatbot/
├── venv/                  # Virtual Environment (nicht in Git)
├── src/                   # Quellcode
├── calculations/          # Berechnungs-Module
├── config/                # Konfiguration
├── demo_*.py              # Demo-Scripts
├── .env                   # Deine Credentials (nicht in Git)
├── .env.template          # Template
├── requirements.txt       # Dependencies
└── README.md              # Haupt-Dokumentation
```

---

## Nächste Schritte

Nach erfolgreicher Installation:

1. README.md lesen
2. Demo-Scripts durchprobieren
3. Eigene Anfragen testen
4. CONTRIBUTING.md lesen (für Entwickler)

---

## Updates installieren

```bash
# Repository aktualisieren
git pull origin main

# Dependencies aktualisieren
pip install -r requirements.txt --upgrade
```

---

## Deinstallation

```bash
# Virtual Environment deaktivieren
deactivate

# Projekt-Ordner löschen
cd ..
rm -rf logistics-chatbot
```

---

Bei weiteren Fragen: Issue im GitHub Repository erstellen.