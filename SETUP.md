# FlexGuide4 - Setup Guide

Schnellanleitung für die Installation und Einrichtung von FlexGuide4.

---

## Systemanforderungen

- **Python:** 3.10 oder höher
- **Git:** Für Repository-Verwaltung
- **Internet:** Stabile Verbindung
- **Browser:** Für Web-Interface

---

## Installation

### 1. Python Version prüfen

```bash
python3 --version
```

Erwartete Ausgabe: `Python 3.10.x` oder höher

### 2. Repository klonen

```bash
git clone <repository-url>
cd Flexus_Code
```

### 3. Virtual Environment (empfohlen)

```bash
# Erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 4. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 5. Environment konfigurieren

```bash
# Template kopieren
cp env.template .env

# Bearbeiten
nano .env
```

Erforderliche Werte eintragen:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o

# OAuth
OAUTH_TOKEN_URL=https://your-oauth-endpoint.com/oauth/token
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# OData API
ODATA_BASE_URL=https://your-api-endpoint.com/orders/Orders
```

### 6. Installation testen

```bash
python3 -c "from config.settings import Config; Config.validate()"
```

Erwartete Ausgabe: `Konfiguration vollständig`

---

## FlexGuide4 starten

### Web-Interface

```bash
python demo_app.py
```

Browser öffnen: `http://localhost:5000`

---

## API Credentials

### OpenAI API Key

1. Account auf [platform.openai.com](https://platform.openai.com) erstellen
2. API Key generieren
3. In `.env` unter `OPENAI_API_KEY` eintragen

**Kosten:** Ca. 0.01-0.05 EUR pro Anfrage

### THWS OAuth Credentials

Werden vom Projektbetreuer bereitgestellt:
- Client ID
- Client Secret  
- Token URL
- API Base URL

---

## Schnelltest

Nach dem Start des Web-Interface diese Fragen testen:

**Als Supervisor:**
- "Welche Fahraufträge stehen als nächstes an?"
- "Wie viele Aufträge heute?"

**Als Ressource (z.B. MAGAZINO):**
- "Was sind meine nächsten Aufträge?"
- "Zeige mir Auftrag 89"

---

## Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `No module named 'openai'` | `pip install -r requirements.txt` |
| `Config validation failed` | `.env` Datei prüfen |
| `Token refresh failed` | OAuth Credentials vom Betreuer anfordern |
| Port 5000 belegt | Port in `demo_app.py` ändern |

---

## Projekt-Struktur

```
Flexus_Code/
├── demo_app.py              # Web-Interface (Hauptanwendung)
├── src/                     # Kern-Komponenten
├── calculations/            # Berechnungs-Module
├── config/                  # Konfiguration
├── logo/                    # FlexGuide4 Logo
├── requirements.txt         # Dependencies
├── env.template             # Template für .env
└── .env                     # Deine Credentials (lokal)
```

---

## Nächste Schritte

1. [README.md](README.md) - System-Übersicht
2. [CONTRIBUTING.md](CONTRIBUTING.md) - Entwickler-Guide
3. Web-Interface testen mit Beispiel-Fragen

---

## Updates

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

**Support:** Projektteam kontaktieren