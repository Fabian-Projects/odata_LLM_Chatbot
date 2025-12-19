"""
LLM-basierter Query Parser
Konvertiert natürliche Sprache in strukturierte OData-Queries + Berechnungslogik
"""

import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
from datetime import datetime, timedelta


class LLMQueryParser:
    """
    Wandelt natürliche Sprach-Anfragen in strukturierte JSON-Queries um.
    Nutzt GPT-4 für intelligentes Parsing.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Args:
            api_key: OpenAI API Key
            model: GPT Model (default: gpt-4-turbo-preview)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        
    def parse_query(self, user_input: str) -> Dict[str, Any]:
        """
        Hauptmethode: Parst User-Input zu strukturiertem JSON
        
        Args:
            user_input: Natürliche Sprache vom User
            
        Returns:
            Dictionary mit odata_params, calculation, etc.
        """
        
        # System Prompt mit Schema-Info und Beispielen
        system_prompt = self._build_system_prompt()
        
        # Conversation History für Context
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Letzte 2-3 Fragen als Context
        for hist in self.conversation_history[-3:]:
            messages.append({"role": "user", "content": hist["user_input"]})
            messages.append({"role": "assistant", "content": json.dumps(hist["parsed_output"], ensure_ascii=False)})
        
        # Aktuelle Frage
        messages.append({"role": "user", "content": user_input})
        
        # GPT API Call
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Niedrig für konsistente Outputs
                response_format={"type": "json_object"}  # Erzwingt JSON
            )
            
            parsed_output = json.loads(response.choices[0].message.content)
            
            # Validierung
            validated_output = self._validate_and_enhance(parsed_output)
            
            # History speichern
            self.conversation_history.append({
                "user_input": user_input,
                "parsed_output": validated_output,
                "timestamp": datetime.now().isoformat()
            })
            
            return validated_output
            
        except Exception as e:
            print(f"❌ LLM Parser Error: {e}")
            return self._get_fallback_response(user_input, str(e))
    
    def _build_system_prompt(self) -> str:
        """
        Erstellt den System-Prompt mit Schema-Info und Beispielen
        """
        
        heute = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""Du bist ein Experten-System für Logistik-Datenbanken. 
Deine Aufgabe: Wandle natürliche Sprach-Anfragen in strukturierte JSON-Queries für ein OData-API um.

**Heutiges Datum:** {heute}

**Datenbank-Schema (Fahraufträge):**
- ID (string): Eindeutige ID
- createdAt (datetime): Erstellungszeitpunkt
- modifiedAt (datetime): Letzte Änderung
- due (datetime): Fälligkeitsdatum
- state (string): Status (READY, IN_PROGRESS, COMPLETED, etc.)
- type_ID (string): Auftragstyp (z.B. UMLAGERUNG)
- group (string): Zugewiesene Gruppe
- assignedResource_ID (string): Zugewiesene Ressource (kann null sein)
- source (string): Startort
- destination (string): Zielort
- material (string): Material-Bezeichnung
- quantityAmount (number): Menge
- quantityUnit (string): Einheit
- loadCarrierType_name (string): Ladungsträger-Typ
- categoryReasonCode (string): Kategorie/Grund

**Output-Format (IMMER als gültiges JSON):**

{{
  "intent": "query" oder "calculation",
  "odata_params": {{
    "$filter": "OData-Filter-String (optional)",
    "$select": "Komma-getrennte Felder (optional)",
    "$top": Anzahl (optional, default 100),
    "$orderby": "Feld asc/desc (optional)",
    "$count": true/false (optional)
  }},
  "calculation": {{
    "type": "count" | "average_time" | "utilization" | "sum" | null,
    "grouping_field": "Feldname für Gruppierung (optional)",
    "time_field": "createdAt" | "modifiedAt" | "due" (optional),
    "aggregation": "sum" | "avg" | "min" | "max" (optional)
  }},
  "response_context": {{
    "user_question": "Original-Frage",
    "friendly_description": "Was wird gemacht"
  }}
}}

**OData Filter Syntax:**
- Vergleiche: eq (gleich), ne (ungleich), gt (größer), ge (größer-gleich), lt (kleiner), le (kleiner-gleich)
- Logik: and, or, not
- Datum: ISO-Format "2025-12-17T00:00:00Z"
- String: 'Wert' (in Anführungszeichen)
- Zeiträume: "createdAt ge 2025-12-17T00:00:00Z and createdAt lt 2025-12-18T00:00:00Z"

**Beispiele:**

User: "Wie viele Aufträge gab es heute?"
{{
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00Z and createdAt lt {heute}T23:59:59Z",
    "$select": "ID"
  }},
  "calculation": {{
    "type": "count",
    "grouping_field": null,
    "time_field": "createdAt"
  }},
  "response_context": {{
    "user_question": "Wie viele Aufträge gab es heute?",
    "friendly_description": "Anzahl der heute erstellten Aufträge"
  }}
}}

User: "Zeige mir ID 3"
{{
  "intent": "query",
  "odata_params": {{
    "$filter": "ID eq '3'",
    "$select": "ID,material,quantityAmount,quantityUnit,source,destination,createdAt,state"
  }},
  "calculation": null,
  "response_context": {{
    "user_question": "Zeige mir ID 3",
    "friendly_description": "Details zum Fahrauftrag mit ID 3"
  }}
}}

User: "Wie viele Aufträge pro Gruppe heute?"
{{
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00Z and createdAt lt {heute}T23:59:59Z",
    "$select": "ID,group"
  }},
  "calculation": {{
    "type": "count",
    "grouping_field": "group",
    "time_field": "createdAt"
  }},
  "response_context": {{
    "user_question": "Wie viele Aufträge pro Gruppe heute?",
    "friendly_description": "Anzahl Aufträge gruppiert nach Gruppe für heute"
  }}
}}

User: "Welche Aufträge sind von HR-01-08 nach HR-02-02 gefahren?"
{{
  "intent": "query",
  "odata_params": {{
    "$filter": "source eq 'HR-01-08' and destination eq 'HR-02-02'",
    "$select": "ID,source,destination,material,quantityAmount,state,createdAt",
    "$orderby": "createdAt desc"
  }},
  "calculation": null,
  "response_context": {{
    "user_question": "Welche Aufträge sind von HR-01-08 nach HR-02-02 gefahren?",
    "friendly_description": "Fahraufträge von HR-01-08 nach HR-02-02"
  }}
}}

**WICHTIG:**
- Antworte NUR mit gültigem JSON, keine Erklärungen drumherum
- Bei Datumsangaben: "heute" = {heute}, "gestern" = Tag davor, etc.
- Bei unklaren Anfragen: Gib beste Vermutung zurück, setze intent auf "query"
- $select: Nur relevante Felder, nicht alles
- $filter: Nutze korrekte OData-Syntax
"""
        
        return prompt
    
    def _validate_and_enhance(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validiert und ergänzt das geparste JSON
        """
        
        # Defaults setzen
        if "intent" not in parsed:
            parsed["intent"] = "query"
        
        if "odata_params" not in parsed:
            parsed["odata_params"] = {}
        
        # Top-Limit sicherstellen
        if "$top" not in parsed["odata_params"]:
            parsed["odata_params"]["$top"] = 100
        
        # Calculation null-Check
        if "calculation" not in parsed or parsed["calculation"] == {}:
            parsed["calculation"] = None
        
        # Response Context sicherstellen
        if "response_context" not in parsed:
            parsed["response_context"] = {
                "user_question": "Unbekannte Anfrage",
                "friendly_description": "Datenabfrage"
            }
        
        return parsed
    
    def _get_fallback_response(self, user_input: str, error: str) -> Dict[str, Any]:
        """
        Fallback bei Parse-Fehlern
        """
        return {
            "intent": "error",
            "odata_params": {},
            "calculation": None,
            "response_context": {
                "user_question": user_input,
                "friendly_description": f"Fehler beim Parsen: {error}",
                "error": True
            }
        }
    
    def clear_history(self):
        """Löscht Conversation History"""
        self.conversation_history = []
    
    def get_last_query(self) -> Optional[Dict[str, Any]]:
        """Gibt letzte geparste Query zurück"""
        if self.conversation_history:
            return self.conversation_history[-1]
        return None


# ===== HELPER FUNCTIONS =====

def build_time_filter(timeframe: str) -> str:
    """
    Helper: Erstellt OData-Filter für Zeiträume
    
    Args:
        timeframe: "heute", "gestern", "diese_woche", "letzter_monat", etc.
        
    Returns:
        OData-Filter-String
    """
    now = datetime.now()
    
    if timeframe == "heute":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59)
        
    elif timeframe == "gestern":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0)
        end = yesterday.replace(hour=23, minute=59, second=59)
        
    elif timeframe == "diese_woche":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0)
        end = now
        
    elif timeframe == "letzter_monat":
        first_of_month = now.replace(day=1)
        end = first_of_month - timedelta(days=1)
        start = end.replace(day=1, hour=0, minute=0, second=0)
        end = end.replace(hour=23, minute=59, second=59)
        
    else:
        # Default: heute
        start = now.replace(hour=0, minute=0, second=0)
        end = now
    
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return f"createdAt ge {start_str} and createdAt lt {end_str}"
