"""
LLM-basierter Query Parser
Konvertiert natürliche Sprache in strukturierte OData-Queries + Berechnungslogik
ERWEITERT: Intent "next_orders" + Ressourcen-Context
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
        
        # NEU: Ressourcen-Positions-Mapping
        self.resource_positions = {
            "AGILOX": "AGILOX-PARK-02",
            "JUNGHEINRICH": "JUNGHEINRICH-PARK",
            "MAGAZINO": "MAGAZINO-PARK-01",
            "SAFELOG": "SAFELOG-PARK",
            "SCHUBMASTSTAPLER_LINKS": "SCHUBMAST-PARK-LINKS",
            "SCHUBMASTSTAPLER_RECHTS": "SCHUBMAST-PARK-RECHTS",
            "STAPLER_WA": "STAPLER-PARK-WA",
            "STAPLER_WE": "STAPLER-PARK-WE",
        }
        
    def parse_query(self, user_input: str, resource_id: str = "SUPERVISOR") -> Dict[str, Any]:
        """
        Hauptmethode: Parst User-Input zu strukturiertem JSON
        
        Args:
            user_input: Natürliche Sprache vom User
            resource_id: Aktuelle Ressource des Users (NEU)
        
        Returns:
            Dictionary mit odata_params, calculation, etc.
        """
        
        # Kontext-Anreicherung für Detailabfragen
        last_context = self._get_last_context()
        enriched_input = self._enrich_with_context(user_input, last_context)

        # System Prompt mit Schema-Info und Beispielen
        system_prompt = self._build_system_prompt(resource_id, last_context)
        
        # Conversation History für Context
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Letzte 2-3 Fragen als Context
        for hist in self.conversation_history[-3:]:
            messages.append({"role": "user", "content": hist["user_input"]})
            messages.append({"role": "assistant", "content": json.dumps(hist["parsed_output"], ensure_ascii=False)})
        
        # Aktuelle Frage
        messages.append({"role": "user", "content": enriched_input})
        
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
            validated_output = self._validate_and_enhance(parsed_output, resource_id)
            
            # History speichern
            self.conversation_history.append({
                "user_input": user_input,
                "parsed_output": validated_output,
                "resource_id": resource_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return validated_output
            
        except Exception as e:
            print(f"LLM Parser Error: {e}")
            return self._get_fallback_response(user_input, str(e))
    
    def _get_last_context(self) -> Optional[Dict[str, Any]]:
        """Holt den letzten Kontext aus der Conversation History"""
        if self.conversation_history:
            return self.conversation_history[-1]
        return None
    
    def _enrich_with_context(self, user_input: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Reichert User-Input mit Kontext-Informationen an
        Ermöglicht Detailabfragen zu vorherigen Aufträgen
        """
        if not context:
            return user_input
        
        enriched = user_input
        parsed = context.get("parsed_output", {})
        
        # Check: War letzte Anfrage "next_orders"?
        if parsed.get("intent") == "next_orders":
            # Extrahiere Auftragsdaten falls vorhanden
            # Diese Daten kommen aus der demo_app.py conversation_contexts
            enriched += "\n\n[KONTEXT aus letzter Anfrage]"
            enriched += "\nLetzte Anfrage war nach nächsten Fahraufträgen."
        
        # Check: Fragt User nach Details zu einem Auftrag?
        import re
        
        # Pattern 1: "Auftrag 60", "Auftrag ID 60", "Order 60"
        order_id_match = re.search(r'auftrag(?:\s+id)?\s+(\d+)', user_input.lower())
        
        # Pattern 2: "erster Auftrag", "zweiter Auftrag", "dritter Auftrag"
        position_match = re.search(r'(erste[rn]?|zweite[rn]?|dritte[rn]?)\s+auftrag', user_input.lower())
        
        if order_id_match:
            order_id = order_id_match.group(1)
            enriched += f"\n\n[HINWEIS] User fragt nach Details zu Auftrag ID: {order_id}"
            enriched += f"\nBitte erstelle einen Filter: ID eq '{order_id}'"
            enriched += "\nWähle ALLE relevanten Felder für $select: ID,createdAt,modifiedAt,due,state,type_ID,source,destination,material,quantityAmount,quantityUnit,loadCarrierType_name,assignedResource_ID,group"
        
        elif position_match:
            position_text = position_match.group(1)
            position_mapping = {
                'erste': 1, 'ersten': 1, 'erster': 1,
                'zweite': 2, 'zweiten': 2, 'zweiter': 2,
                'dritte': 3, 'dritten': 3, 'dritter': 3
            }
            position_num = position_mapping.get(position_text, 1)
            
            enriched += f"\n\n[HINWEIS] User fragt nach dem {position_num}. Auftrag aus der letzten Antwort."
            enriched += "\nDies bezieht sich auf die vorherige 'next_orders' Anfrage."
            enriched += f"\nBitte erstelle eine Standard-Query für Auftragsdetails (keine next_orders)."
        
        # Check: Fragt User nach "mehr Infos", "Details", "genauere Informationen"?
        detail_keywords = ['mehr infos', 'details', 'genauere', 'ausführlich', 'vollständig']
        if any(keyword in user_input.lower() for keyword in detail_keywords):
            enriched += "\n\n[HINWEIS] User möchte detaillierte Informationen."
            enriched += "\nSetze detail_level auf 'detailed' und wähle ALLE relevanten Felder."
        
        return enriched


    def _build_system_prompt(self, resource_id: str = "SUPERVISOR", last_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Erstellt den System-Prompt mit Schema-Info und Beispielen
        """
        
        heute = datetime.now().strftime("%Y-%m-%d")
        aktuelle_uhrzeit = datetime.now().strftime("%H:%M")
        date_context = self._get_date_context()
        
        # Ressourcen-Info
        resource_info = f"\n**Aktuelle Ressource:** {resource_id}"
        if resource_id != "SUPERVISOR":
            default_pos = self.resource_positions.get(resource_id, "Unbekannt")
            resource_info += f"\n**Standard-Position:** {default_pos}"
        
        # Liste aller verfügbaren Ressourcen
        resources_list = "\n**Verfügbare Ressourcen:**\n"
        resources_list += "- AGILOX\n- JUNGHEINRICH\n- MAGAZINO\n- SAFELOG\n"
        resources_list += "- SCHUBMASTSTAPLER_LINKS\n- SCHUBMASTSTAPLER_RECHTS\n"
        resources_list += "- STAPLER_WA\n- STAPLER_WE\n"
        resources_list += "\nWenn User eine dieser Ressourcen nennt (z.B. 'beim Jungheinrich', 'bei MAGAZINO'), "
        resources_list += "setze das 'resource' Feld in next_orders_params."

        # Kontext-Info für Follow-up-Fragen
        context_info = ""
        if last_context and last_context.get("parsed_output"):
            last_parsed = last_context["parsed_output"]
            if last_parsed.get("intent") == "next_orders":
                context_info = "\n\n**WICHTIG - Follow-up zu letzter Anfrage:**"
                context_info += "\nDie letzte Anfrage war nach 'nächsten Aufträgen'."
                context_info += "\nWenn User jetzt nach 'erstem Auftrag', 'zweitem Auftrag' oder einer spezifischen Auftrags-ID fragt,"
                context_info += "\ndann erstelle eine NORMALE Query (intent: 'query') mit einem Filter auf die ID."
                context_info += "\nBeispiel: 'Details zum ersten Auftrag' → nutze die Order-ID aus der letzten Antwort"

        prompt = f"""Du bist ein Experten-System für Logistik-Datenbanken.
        {context_info}
        {resources_list} 
Deine Aufgabe: Wandle natürliche Sprach-Anfragen in strukturierte JSON-Queries für ein OData-API um.
{resource_info}

**KRITISCH - Datumsformat:**
API nutzt: "2026-01-19T08:43:23.787Z" (MIT Millisekunden .000Z)
Filter MÜSSEN Millisekunden haben: "createdAt ge 2026-01-19T00:00:00.000Z"

**Heutiges Datum:** {heute}
**Aktuelle Uhrzeit:** {aktuelle_uhrzeit}
{date_context}

**WICHTIG - SCHICHTEN:**
Es gibt zwei Schichten:
- Frühschicht: 06:00 - 14:00 Uhr
- Spätschicht: 14:00 - 22:00 Uhr

Erkenne Schicht-Anfragen:
- "in der Frühschicht" → shift_filter: "früh"
- "in der Spätschicht" → shift_filter: "spät"
- "heute noch" / "aktuelle Schicht" → shift_filter: "current"

**NEU - NÄCHSTE AUFTRÄGE:**
Erkenne Anfragen nach nächsten Fahraufträgen:
- "Zeig mir meine nächsten Aufträge"
- "Was kommt als nächstes?"
- "Nächste Fahraufträge"
- "Welche Aufträge stehen an?"

Wenn solche Anfragen erkannt werden:
- Setze intent: "next_orders"
- Füge position hinzu (Standard-Position der Ressource oder explizit genannt)

**WICHTIG - Beantwortbarkeit:**
- Prüfe ob die Frage mit den verfügbaren Datenbank-Feldern beantwortbar ist
- Wenn NICHT (z.B. Wetter, externe Daten), setze "isAnswerable": false
- Gib dann einen freundlichen Grund an

**Datenbank-Schema (Fahraufträge):**
- ID (string): Eindeutige ID
- createdAt (datetime): Erstellungszeitpunkt - Format "2026-01-19T08:43:23.787Z"
- modifiedAt (datetime): Letzte Änderung
- due (datetime): Fälligkeitsdatum
- state (string): Status (READY, RUNNING, COMPLETED, etc.)
- type_ID (string): Auftragstyp (z.B. WARENEINGANG, UMLAGERUNG)
- group (string): Zugewiesene Gruppe (KANN NULL SEIN!)
- assignedResource_ID (string): Zugewiesene Ressource
- source (string): Startort
- destination (string): Zielort
- material (string): Material-Bezeichnung
- quantityAmount (number): Menge
- quantityUnit (string): Einheit
- loadCarrierType_name (string): Ladungsträger-Typ
- categoryReasonCode (string): Kategorie/Grund

**Output-Format (IMMER als gültiges JSON):**

{{
  "isAnswerable": true oder false,
  "reason": "Erklärung wenn nicht beantwortbar (nur bei false)",
  "intent": "query" | "calculation" | "next_orders",
  "odata_params": {{
    "$filter": "OData-Filter-String (optional)",
    "$select": "Komma-getrennte Felder (optional)",
    "$top": Anzahl (optional, default 100),
    "$orderby": "Feld asc/desc (optional)",
    "$count": true/false (optional)
  }},
  "calculation": {{
    "type": "count" | "sum" | null,
    "grouping_field": "Feldname für Gruppierung (optional)",
    "shift_filter": "früh" | "spät" | "current" | null,
    "detail_level": "basic" | "detailed",
    "time_field": "createdAt" | "modifiedAt" | "due" (optional)
  }},
  "next_orders_params": {{
    "resource": "Spezifische Ressource (optional, nur wenn User eine bestimmte Ressource nennt)",
    "position": "Position der Ressource (optional, sonst Standard-Position)"
  }},
  "response_context": {{
    "user_question": "Original-Frage",
    "friendly_description": "Was wird gemacht"
  }}
}}

**OData Filter Syntax:**
- Vergleiche: eq (gleich), ne (ungleich), gt (größer), ge (größer-gleich), lt (kleiner), le (kleiner-gleich)
- Logik: and, or, not
- Datum: ISO-Format MIT Millisekunden: "2026-01-19T00:00:00.000Z"
- String: 'Wert' (in Anführungszeichen)
- Zeiträume: "createdAt ge 2026-01-19T00:00:00.000Z and createdAt le 2026-01-19T23:59:59.999Z"

**WICHTIG für Zeiträume:**
- Nutze "ge" (>=) für Start
- Nutze "le" (<=) für Ende
- Immer .000Z oder .999Z für Millisekunden

**Beispiele:**

User: "Zeig mir meine nächsten Aufträge"
{{
  "isAnswerable": true,
  "intent": "next_orders",
  "odata_params": {{}},
  "calculation": null,
  "next_orders_params": {{
    "position": null
  }},
  "response_context": {{
    "user_question": "Zeig mir meine nächsten Aufträge",
    "friendly_description": "Nächste Fahraufträge für diese Ressource"
  }}
}}

User: "Was kommt als nächstes bei HR-01-02?"
{{
  "isAnswerable": true,
  "intent": "next_orders",
  "odata_params": {{}},
  "calculation": null,
  "next_orders_params": {{
    "position": "HR-01-02"
  }},
  "response_context": {{
    "user_question": "Was kommt als nächstes bei HR-01-02?",
    "friendly_description": "Nächste Fahraufträge ab Position HR-01-02"
  }}
}}

User: "Wie viele Aufträge gab es heute?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00.000Z and createdAt le {heute}T23:59:59.999Z",
    "$select": "ID,createdAt,state,type_ID"
  }},
  "calculation": {{
    "type": "count",
    "grouping_field": null,
    "detail_level": "basic"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Wie viele Aufträge gab es heute?",
    "friendly_description": "Anzahl der heute erstellten Aufträge"
  }}
}}

User: "Zeige mir Auftrag 89"
{{
  "isAnswerable": true,
  "intent": "query",
  "odata_params": {{
    "$filter": "ID eq '89'",
    "$select": "ID,createdAt,state,type_ID,source,destination,material,quantityAmount"
  }},
  "calculation": null,
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Zeige mir Auftrag 89",
    "friendly_description": "Details zu Auftrag 89"
  }}
}}

User: "Wie viele Aufträge nach Status heute?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00.000Z and createdAt le {heute}T23:59:59.999Z",
    "$select": "ID,state,createdAt"
  }},
  "calculation": {{
    "type": "count",
    "grouping_field": "state",
    "detail_level": "basic"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Wie viele Aufträge nach Status heute?",
    "friendly_description": "Aufträge gruppiert nach Status"
  }}
}}

User: "Kannst du mir genauere Informationen geben?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00.000Z and createdAt le {heute}T23:59:59.999Z",
    "$select": "ID,state,type_ID,createdAt,assignedResource_ID"
  }},
  "calculation": {{
    "type": "count",
    "grouping_field": "state",
    "detail_level": "detailed"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Kannst du mir genauere Informationen geben?",
    "friendly_description": "Detaillierte Auftrags-Statistiken"
  }}
}}

User: "Wie viele Aufträge gab es letzte Woche?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge LETZTE_WOCHE_START and createdAt le LETZTE_WOCHE_ENDE",
    "$select": "ID,createdAt,state"
  }},
  "calculation": {{
    "type": "count",
    "grouping_field": null,
    "shift_filter": null,
    "detail_level": "basic"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Wie viele Aufträge gab es letzte Woche?",
    "friendly_description": "Aufträge der letzten Woche"
  }}
}}

User: "Wie viele Aufträge gab es heute in der Frühschicht?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00.000Z and createdAt le {heute}T23:59:59.999Z",
    "$select": "ID,createdAt,state"
  }},
  "calculation": {{
    "type": "count",
    "shift_filter": "früh",
    "detail_level": "basic"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Wie viele Aufträge gab es heute in der Frühschicht?",
    "friendly_description": "Aufträge der Frühschicht"
  }}
}}

User: "Wie viele Aufträge haben wir heute noch?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "createdAt ge {heute}T00:00:00.000Z and state ne 'COMPLETED'",
    "$select": "ID,createdAt,state"
  }},
  "calculation": {{
    "type": "count",
    "shift_filter": "current",
    "detail_level": "basic"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Wie viele Aufträge haben wir heute noch?",
    "friendly_description": "Offene Aufträge der aktuellen Schicht"
  }}
}}

User: "Kannst du mir mehr Infos zu Auftrag 60 geben?"
{{
  "isAnswerable": true,
  "intent": "query",
  "odata_params": {{
    "$filter": "ID eq '60'",
    "$select": "ID,createdAt,modifiedAt,due,state,type_ID,source,destination,material,quantityAmount,quantityUnit,loadCarrierType_name,assignedResource_ID,group"
  }},
  "calculation": null,
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Kannst du mir mehr Infos zu Auftrag 60 geben?",
    "friendly_description": "Detaillierte Informationen zu Auftrag ID 60"
  }}
}}

User: "Kannst du mir mehr Infos zum ersten Auftrag geben?"
{{
  "isAnswerable": true,
  "intent": "query",
  "odata_params": {{
    "$filter": "ID eq 'ID_AUS_KONTEXT'",
    "$select": "ID,createdAt,modifiedAt,due,state,type_ID,source,destination,material,quantityAmount,quantityUnit,loadCarrierType_name,assignedResource_ID,group"
  }},
  "calculation": null,
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Kannst du mir mehr Infos zum ersten Auftrag geben?",
    "friendly_description": "Details zum ersten Auftrag aus der vorherigen Liste"
  }}
}}

User: "Welche Fahraufträge stehen beim Jungheinrich als nächstes an?"
{{
  "isAnswerable": true,
  "intent": "next_orders",
  "odata_params": {{}},
  "calculation": null,
  "next_orders_params": {{
    "resource": "JUNGHEINRICH",
    "position": null
  }},
  "response_context": {{
    "user_question": "Welche Fahraufträge stehen beim Jungheinrich als nächstes an?",
    "friendly_description": "Nächste Fahraufträge für JUNGHEINRICH"
  }}
}}

User: "Welche Fahraufträge stehen als nächstes an?" (Als Supervisor)
{{
  "isAnswerable": true,
  "intent": "next_orders",
  "odata_params": {{}},
  "calculation": null,
  "next_orders_params": {{
    "resource": null,
    "position": null
  }},
  "response_context": {{
    "user_question": "Welche Fahraufträge stehen als nächstes an?",
    "friendly_description": "Nächste Fahraufträge für alle Ressourcen (Supervisor-Ansicht)"
  }}
}}

User: "Was steht beim MAGAZINO an?"
{{
  "isAnswerable": true,
  "intent": "next_orders",
  "odata_params": {{}},
  "calculation": null,
  "next_orders_params": {{
    "resource": "MAGAZINO",
    "position": null
  }},
  "response_context": {{
    "user_question": "Was steht beim MAGAZINO an?",
    "friendly_description": "Nächste Fahraufträge für MAGAZINO"
  }}
}}

User: "Zeig mir was beim Jungheinrich kommt"
{{
  "isAnswerable": true,
  "intent": "next_orders",
  "odata_params": {{}},
  "calculation": null,
  "next_orders_params": {{
    "resource": "JUNGHEINRICH",
    "position": null
  }},
  "response_context": {{
    "user_question": "Zeig mir was beim Jungheinrich kommt",
    "friendly_description": "Nächste Fahraufträge für JUNGHEINRICH"
  }}
}}

User: "Welche Aufträge gehen von MAGAZINO-PARK-01 los?"
{{
  "isAnswerable": true,
  "intent": "query",
  "odata_params": {{
    "$filter": "source eq 'MAGAZINO-PARK-01'",
    "$select": "ID,createdAt,state,source,destination,type_ID,assignedResource_ID"
  }},
  "calculation": null,
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Welche Aufträge gehen von MAGAZINO-PARK-01 los?",
    "friendly_description": "Aufträge mit Start-Position MAGAZINO-PARK-01"
  }}
}}

User: "Zeige mir Aufträge zum Ziel LEERGUT-02"
{{
  "isAnswerable": true,
  "intent": "query",
  "odata_params": {{
    "$filter": "destination eq 'LEERGUT-02'",
    "$select": "ID,createdAt,state,source,destination,type_ID,assignedResource_ID"
  }},
  "calculation": null,
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Zeige mir Aufträge zum Ziel LEERGUT-02",
    "friendly_description": "Aufträge mit Ziel LEERGUT-02"
  }}
}}

User: "Wie viele Aufträge von MONTAGE nach HR?"
{{
  "isAnswerable": true,
  "intent": "calculation",
  "odata_params": {{
    "$filter": "contains(source, 'MONTAGE') and contains(destination, 'HR')",
    "$select": "ID,createdAt,state,source,destination"
  }},
  "calculation": {{
    "type": "count",
    "detail_level": "basic"
  }},
  "next_orders_params": null,
  "response_context": {{
    "user_question": "Wie viele Aufträge von MONTAGE nach HR?",
    "friendly_description": "Anzahl Aufträge von MONTAGE nach HR"
  }}
}}

**WICHTIG:**
- Antworte NUR mit gültigem JSON, keine Erklärungen drumherum
- Bei Datumsangaben: "heute" = {heute}, "gestern" = Tag davor, "letzte Woche" = 7 Tage zurück
- IMMER Millisekunden im Datumsformat: .000Z oder .999Z
- $select: IMMER mindestens "ID,createdAt,state,source,destination,type_ID,assignedResource_ID" inkludieren
- Nutze "state" für Gruppierungen (nicht "group", da oft null)
- Bei Nachfragen wie "genauere Informationen": setze detail_level auf "detailed"
- Bei "nächste Aufträge"-Anfragen: intent = "next_orders"
"""
        
        return prompt
    
    def _validate_and_enhance(self, parsed: Dict[str, Any], resource_id: str = "SUPERVISOR") -> Dict[str, Any]:
        """Validiert und ergänzt das geparste JSON"""
        
        # isAnswerable Check
        if "isAnswerable" not in parsed:
            parsed["isAnswerable"] = True
        
        # Wenn nicht beantwortbar, gib das direkt zurück
        if not parsed["isAnswerable"]:
            if "reason" not in parsed:
                parsed["reason"] = "Die Frage kann mit den verfügbaren Daten nicht beantwortet werden."
            return parsed
        
        # Intent Check
        if "intent" not in parsed:
            parsed["intent"] = "query"
        
        # Für "next_orders" Intent
        # NEU: Für "next_orders" Intent
        if parsed["intent"] == "next_orders":
            if "next_orders_params" not in parsed:
                parsed["next_orders_params"] = {}
            
            # Prüfe ob spezifische Ressource genannt wurde
            params = parsed["next_orders_params"]
            
            # Wenn keine Position angegeben, nutze Standard-Position
            if not params.get("position"):
                # Wenn spezifische Ressource im Intent erwähnt
                target_resource = params.get("resource") or resource_id
                
                if target_resource != "SUPERVISOR":
                    params["position"] = self.resource_positions.get(target_resource)
                else:
                    params["position"] = None
        
        # Für normale Queries
        if "odata_params" not in parsed:
            parsed["odata_params"] = {}
        
        # FIX Datumsfilter mit korrektem Format
        if "$filter" in parsed.get("odata_params", {}):
            parsed["odata_params"]["$filter"] = self._fix_date_format(parsed["odata_params"]["$filter"])
        
        if "$top" not in parsed.get("odata_params", {}):
            parsed["odata_params"]["$top"] = 100
        
        if "calculation" not in parsed or parsed["calculation"] == {}:
            parsed["calculation"] = None
        
        # Stelle sicher dass calculation ein Dict ist
        if parsed["calculation"] is not None:
            if "detail_level" not in parsed["calculation"]:
                parsed["calculation"]["detail_level"] = "basic"
            
            # Konvertiere "current" zur aktuellen Schicht
            if parsed["calculation"].get("shift_filter") == "current":
                current_hour = datetime.now().hour
                if 6 <= current_hour < 14:
                    parsed["calculation"]["shift_filter"] = "früh"
                elif 14 <= current_hour < 22:
                    parsed["calculation"]["shift_filter"] = "spät"
                else:
                    parsed["calculation"]["shift_filter"] = None
        
        if "response_context" not in parsed:
            parsed["response_context"] = {
                "user_question": "Unbekannte Anfrage",
                "friendly_description": "Datenabfrage"
            }
        
        return parsed
    
    def _fix_date_format(self, filter_string: str) -> str:
        """
        Stellt sicher dass Datumsfilter Millisekunden haben
        
        Args:
            filter_string: OData Filter String
            
        Returns:
            Korrigierter Filter String
        """
        # Ersetze Datums-Platzhalter
        heute = datetime.now()
        gestern = heute - timedelta(days=1)
        
        # Letzte Woche = Montag vor 7 Tagen bis Sonntag vor 7 Tagen
        heute_wochentag = heute.weekday()  # 0=Montag, 6=Sonntag
        letzte_woche_start = heute - timedelta(days=heute_wochentag + 7)
        letzte_woche_ende = letzte_woche_start + timedelta(days=6, hours=23, minutes=59, seconds=59, milliseconds=999)
        
        # Ersetze Platzhalter
        replacements = {
            "LETZTE_WOCHE_START": letzte_woche_start.strftime("%Y-%m-%dT00:00:00.000Z"),
            "LETZTE_WOCHE_ENDE": letzte_woche_ende.strftime("%Y-%m-%dT23:59:59.999Z"),
        }
        
        for placeholder, value in replacements.items():
            filter_string = filter_string.replace(placeholder, value)
        
        # Füge Millisekunden hinzu wenn sie fehlen
        import re
        
        # Finde alle Datums-Patterns ohne Millisekunden
        pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z'
        
        def add_milliseconds(match):
            return match.group(1) + '.000Z'
        
        filter_string = re.sub(pattern, add_milliseconds, filter_string)
        
        # Stelle sicher dass End-Zeiten .999Z haben
        filter_string = filter_string.replace('23:59:59.000Z', '23:59:59.999Z')
        
        return filter_string
    
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
    
    def _get_date_context(self):
        """Generiert Kontext für relative Datumsangaben"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # Letzte Woche berechnen
        heute_wochentag = today.weekday()
        letzte_woche_start = today - timedelta(days=heute_wochentag + 7)
        letzte_woche_ende = letzte_woche_start + timedelta(days=6)
    
        return f"""
Aktuelles Datum: {today.strftime('%Y-%m-%d')}
Gestern: {yesterday.strftime('%Y-%m-%d')}
Vor einer Woche: {week_ago.strftime('%Y-%m-%d')}
Letzte Woche Start: {letzte_woche_start.strftime('%Y-%m-%d')} (Montag)
Letzte Woche Ende: {letzte_woche_ende.strftime('%Y-%m-%d')} (Sonntag)

Bei "letzte Woche": Nutze Platzhalter LETZTE_WOCHE_START und LETZTE_WOCHE_ENDE
Bei relativen Datumsangaben (heute, gestern): Konvertiere zu ISO-Format mit Millisekunden
Format-Beispiel: {today.strftime('%Y-%m-%d')}T00:00:00.000Z
"""


# ===== HELPER FUNCTIONS (alte Funktionen bleiben erhalten) =====

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
        end = now.replace(hour=23, minute=59, second=59, microsecond=999000)
        
    elif timeframe == "gestern":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999000)
        
    elif timeframe == "diese_woche":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        
    elif timeframe == "letzte_woche":
        # Letzte Woche = Montag bis Sonntag der Vorwoche
        heute_wochentag = now.weekday()
        letzte_woche_start = now - timedelta(days=heute_wochentag + 7)
        start = letzte_woche_start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999000)
        
    elif timeframe == "letzter_monat":
        first_of_month = now.replace(day=1)
        end = first_of_month - timedelta(days=1)
        start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999000)
        
    else:
        # Default: heute
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "000Z"  # Millisekunden
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "999Z"
    
    return f"createdAt ge {start_str} and createdAt le {end_str}"