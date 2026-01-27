from flask import Flask, request, jsonify, session, send_from_directory
from src.llm_parser import LLMQueryParser
from src.odata_client import ODataClient
from src.calculation_engine import CalculationEngine
from src.response_generator import ResponseGenerator
from config.settings import Config
import os

from dotenv import load_dotenv
load_dotenv()

parser = client = engine = generator = None

AVAILABLE_RESOURCES = [
    "SUPERVISOR",
    "AGILOX",
    "JUNGHEINRICH",
    "MAGAZINO",
    "SAFELOG",
    "SCHUBMASTSTAPLER_LINKS",
    "SCHUBMASTSTAPLER_RECHTS",
    "STAPLER_WA",
    "STAPLER_WE"
]

RESOURCE_POSITIONS = {
    "AGILOX": "AGILOX-PARK-02",
    "JUNGHEINRICH": "JUNGHEINRICH-PARK",
    "MAGAZINO": "MAGAZINO-PARK-01",
    "SAFELOG": "SAFELOG-PARK",
    "SCHUBMASTSTAPLER_LINKS": "SCHUBMAST-PARK-LINKS",
    "SCHUBMASTSTAPLER_RECHTS": "SCHUBMAST-PARK-RECHTS",
    "STAPLER_WA": "STAPLER-PARK-WA",
    "STAPLER_WE": "STAPLER-PARK-WE",
    "SUPERVISOR": None
}

def init_pipeline():
    global parser, client, engine, generator
    if parser is not None:
        return

    if not Config.validate():
        raise RuntimeError(
            "Config ungültig. Bitte .env prüfen: OPENAI_API_KEY, OPENAI_MODEL, "
            "ODATA_BASE_URL, OAUTH_TOKEN_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET"
        )

    parser = LLMQueryParser(Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
    client = ODataClient(
        Config.ODATA_BASE_URL,
        Config.OAUTH_TOKEN_URL,
        Config.OAUTH_CLIENT_ID,
        Config.OAUTH_CLIENT_SECRET
    )
    engine = CalculationEngine()
    generator = ResponseGenerator(language="de")

conversation_contexts = {}


def bot_reply(user_message: str, session_id: str = "default", resource_id: str = "SUPERVISOR") -> str:
    init_pipeline()
    
    last_context = conversation_contexts.get(session_id)
    
    if last_context:
        enriched_input = f"{user_message}\n\nKontext der letzten Anfrage:\n{last_context}"
    else:
        enriched_input = user_message
    
    parsed = parser.parse_query(enriched_input, resource_id=resource_id)
    
    if parsed.get("intent") == "error":
        return parsed.get("response_context", {}).get("friendly_description", "Parsing-Fehler")
    
    if not parsed.get("isAnswerable", True):
        reason = parsed.get("reason", "Diese Frage kann ich nicht beantworten.")
        return f"{reason}\n\nIch kann dir nur Informationen über Fahraufträge geben."
    
    if parsed.get("intent") == "next_orders":
        try:
            next_orders_params = parsed.get("next_orders_params", {})
            specific_resource = next_orders_params.get("resource")
            position = next_orders_params.get("position")
            
            # Wenn Supervisor fragt nach spezifischer Ressource
            if resource_id == "SUPERVISOR" and specific_resource:
                target_resources = [specific_resource] if specific_resource in AVAILABLE_RESOURCES else []
            # Wenn Supervisor allgemein fragt (alle Ressourcen)
            elif resource_id == "SUPERVISOR" and not specific_resource:
                target_resources = [r for r in AVAILABLE_RESOURCES if r != "SUPERVISOR"]
            # Normale Ressource fragt
            else:
                target_resources = [resource_id]
            
            if not target_resources:
                return "Keine gültige Ressource gefunden."
            
            # Sammle Aufträge für alle Ziel-Ressourcen
            all_orders_by_resource = {}
            
            for res in target_resources:
                res_position = position if position else RESOURCE_POSITIONS.get(res)
                
                if not res_position:
                    continue
                
                try:
                    result = client.assign_best_orders(res, res_position)
                    orders = result.get("orders", [])
                    if orders:
                        all_orders_by_resource[res] = orders
                except Exception as e:
                    print(f"Fehler bei Ressource {res}: {e}")
                    continue
            
            if not all_orders_by_resource:
                return "Keine Aufträge gefunden."
            
            # Formatiere Response
            if len(target_resources) == 1:
                res = target_resources[0]
                orders = all_orders_by_resource.get(res, [])
                
                if not orders:
                    response = f"Keine Aufträge gefunden für {res}."
                elif len(orders) == 1:
                    order = orders[0]
                    response = f"Nächster Auftrag für {res}:\n\n"
                    response += f"Auftrag ID {order['id']}: {order['from']} → {order['to']}"
                else:
                    response = f"Verfügbare Aufträge für {res} ({len(orders)} Stück):\n\n"
                    for i, order in enumerate(orders[:10], 1):
                        response += f"{i}. Auftrag ID {order['id']}: {order['from']} → {order['to']}\n"
                    
                    if len(orders) > 10:
                        response += f"\n... und {len(orders) - 10} weitere"
                
                # Speichere die Auftrags-IDs im Kontext
                order_ids = [str(order['id']) for order in orders[:10]]
                conversation_contexts[session_id] = {
                    "type": "next_orders",
                    "question": user_message,
                    "resource": res,
                    "order_ids": order_ids,
                    "orders_data": orders[:10]
                }
            else:
                # Mehrere Ressourcen (Supervisor-Übersicht)
                response = "Die nächsten Fahraufträge pro Ressource sind:\n\n"
                
                all_order_ids = []
                all_orders_data = []
                
                for res, orders in all_orders_by_resource.items():
                    response += f"{res}:\n"
                    if orders:
                        top_order = orders[0]
                        response += f"→ Auftrag ID {top_order['id']}: {top_order['from']} → {top_order['to']}\n"
                        all_order_ids.append(str(top_order['id']))
                        all_orders_data.append(top_order)
                    else:
                        response += "→ Keine Aufträge\n"
                    response += "\n"
                
                conversation_contexts[session_id] = {
                    "type": "next_orders_overview",
                    "question": user_message,
                    "resources": list(all_orders_by_resource.keys()),
                    "order_ids": all_order_ids,
                    "orders_data": all_orders_data
                }
            
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Fehler beim Abrufen der nächsten Aufträge: {str(e)}"
    
    # Standard OData Query
    try:
        odata_result = client.execute_query(parsed, resource_id=resource_id)
        calc_result = engine.process(odata_result, parsed.get("calculation"))
        response = generator.generate(calc_result, parsed.get("response_context"))
        
        # Speichere Kontext mit Auftragsdaten falls vorhanden
        context_data = {
            "type": "standard_query",
            "question": user_message,
            "resource": resource_id,
            "filter": parsed.get('odata_params', {}).get('$filter', 'keine'),
            "result_summary": calc_result.get('summary', 'N/A')
        }
        
        # Falls Einzelauftrag abgefragt wurde, speichere Details
        if odata_result.get("data") and len(odata_result["data"]) > 0:
            context_data["orders_data"] = odata_result["data"]
            context_data["order_ids"] = [str(o.get('id', '')) for o in odata_result["data"] if 'id' in o]
        
        conversation_contexts[session_id] = context_data
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Fehler bei der Abfrage: {str(e)}"



app = Flask(__name__)
app.secret_key = 'flexguide-demo-secret-key-2025'

@app.route('/logo')
def serve_logo():
    logo_path = '/Users/fabi/Documents/BBA/7_Semester/Projekt_Business_Analytics_2/Flexus_Projektarbeit_Klenk/Flexus_Code/logo'
    return send_from_directory(logo_path, 'logo-flexus.png')

@app.get("/")
def home():
    return """
    <!doctype html>
    <html lang="de">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>FlexGuide4 - Logistics Chatbot</title>
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          background: #ffffff;
          color: #2c3e50;
          overflow: hidden;
          height: 100vh;
        }

        .fixed-header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: 52px;
          background: #ffffff;
          border-bottom: 1px solid #e5e7eb;
          display: flex;
          align-items: center;
          padding: 0 24px;
          z-index: 1000;
        }

        .logo {
          height: 36px;
          width: auto;
        }

        .brand {
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          font-size: 24px;
          font-weight: 600;
          letter-spacing: -0.5px;
        }

        .brand-flex {
          color: #003e87;
        }

        .brand-number {
          color: #003e87;
        }

        .brand-guide {
          color: #DC6F2D;
        }

        .main-container {
          margin-top: 52px;
          height: calc(100vh - 52px);
          display: flex;
          flex-direction: column;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .message {
          max-width: 800px;
          width: 100%;
          margin: 0 auto;
          line-height: 1.6;
          white-space: pre-wrap;
          font-size: 15px;
          display: flex;
        }

        .message.user {
          justify-content: flex-end;
        }

        .message.bot {
          justify-content: flex-start;
        }

        .message-content {
          max-width: 70%;
          padding: 12px 16px;
          border-radius: 12px;
        }

        .message.user .message-content {
          background: linear-gradient(to right, #0064d9 0.188rem, #ebf8ff 0.188rem);
          color: #1f2937;
          font-weight: 500;
        }

        .message.bot .message-content {
          background: transparent;
          color: #374151;
          padding-left: 0;
        }

        .input-section {
          border-top: 1px solid #e5e7eb;
          background: #ffffff;
          padding: 16px 24px 24px;
        }

        .input-wrapper {
          max-width: 800px;
          margin: 0 auto;
          position: relative;
        }

        .text-input {
          width: 100%;
          padding: 16px 16px 50px 16px;
          border: 1px solid #d1d5db;
          border-radius: 12px;
          font-size: 15px;
          font-family: inherit;
          background: #ffffff;
          color: #1f2937;
          transition: all 0.15s;
          resize: none;
          min-height: 120px;
        }

        .text-input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .text-input::placeholder {
          color: #9ca3af;
        }

        .input-controls {
          position: absolute;
          bottom: 12px;
          right: 12px;
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .resource-dropdown {
          position: relative;
        }

        .dropdown-trigger {
          background: none;
          border: none;
          padding: 6px 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 14px;
          color: #6b7280;
          transition: color 0.15s;
        }

        .dropdown-trigger:hover {
          color: #374151;
        }

        .dropdown-arrow {
          width: 0;
          height: 0;
          border-left: 4px solid transparent;
          border-right: 4px solid transparent;
          border-top: 5px solid currentColor;
          transition: transform 0.2s;
        }

        .dropdown-trigger.active .dropdown-arrow {
          transform: rotate(180deg);
        }

        .dropdown-menu {
          position: absolute;
          bottom: 100%;
          right: 0;
          margin-bottom: 8px;
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
          min-width: 240px;
          max-height: 320px;
          overflow-y: auto;
          display: none;
          z-index: 100;
        }

        .dropdown-menu.show {
          display: block;
        }

        .dropdown-item {
          padding: 10px 16px;
          cursor: pointer;
          font-size: 14px;
          color: #374151;
          transition: background 0.1s;
        }

        .dropdown-item:hover {
          background: #f3f4f6;
        }

        .dropdown-item.selected {
          background: #eff6ff;
          color: #3b82f6;
          font-weight: 500;
        }

        .send-button {
          padding: 8px 16px;
          background: #3b82f6;
          color: #ffffff;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }

        .send-button:hover:not(:disabled) {
          background: #2563eb;
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .footer-note {
          text-align: center;
          padding: 12px 24px;
          font-size: 13px;
          color: #6b7280;
          background: #ffffff;
        }

        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: #f9fafb;
        }

        ::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }

        @media (max-width: 768px) {
          .brand {
            font-size: 18px;
          }

          .input-row {
            flex-wrap: wrap;
          }

          .dropdown-trigger {
            font-size: 13px;
            padding: 8px 12px;
          }
        }
      </style>
    </head>
    <body>
      <div class="fixed-header">
        <img src="/logo" alt="Flexus Logo" class="logo">
        <div class="brand">
          <span class="brand-flex">Flex</span><span class="brand-guide">Guide</span><span class="brand-number">4</span>
        </div>
      </div>

      <div class="main-container">
        <div class="messages-container" id="messages"></div>

        <div class="input-section">
          <div class="input-wrapper">
            <textarea 
              id="input" 
              class="text-input" 
              placeholder="Stell eine Frage über Fahraufträge..."
              rows="1"
            ></textarea>
            
            <div class="input-controls">
              <div class="resource-dropdown">
                <button class="dropdown-trigger" id="dropdownTrigger">
                  <span id="selectedResource">Supervisor</span>
                  <div class="dropdown-arrow"></div>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                  <div class="dropdown-item selected" data-value="SUPERVISOR">Supervisor (alle Aufträge)</div>
                  <div class="dropdown-item" data-value="AGILOX">AGILOX</div>
                  <div class="dropdown-item" data-value="JUNGHEINRICH">JUNGHEINRICH</div>
                  <div class="dropdown-item" data-value="MAGAZINO">MAGAZINO</div>
                  <div class="dropdown-item" data-value="SAFELOG">SAFELOG</div>
                  <div class="dropdown-item" data-value="SCHUBMASTSTAPLER_LINKS">SCHUBMASTSTAPLER LINKS</div>
                  <div class="dropdown-item" data-value="SCHUBMASTSTAPLER_RECHTS">SCHUBMASTSTAPLER RECHTS</div>
                  <div class="dropdown-item" data-value="STAPLER_WA">STAPLER WA</div>
                  <div class="dropdown-item" data-value="STAPLER_WE">STAPLER WE</div>
                </div>
              </div>
              <button class="send-button" id="sendBtn">Senden</button>
            </div>
          </div>
        </div>

        <div class="footer-note">
          Dies ist eine ChatBot Demo von THWS Student*Innen
        </div>
      </div>

      <script>
        const messagesContainer = document.getElementById('messages');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        const dropdownTrigger = document.getElementById('dropdownTrigger');
        const dropdownMenu = document.getElementById('dropdownMenu');
        const selectedResourceSpan = document.getElementById('selectedResource');

        let currentResource = 'SUPERVISOR';
        let currentResourceLabel = 'Supervisor';

        // Dropdown Toggle
        dropdownTrigger.addEventListener('click', (e) => {
          e.stopPropagation();
          dropdownMenu.classList.toggle('show');
          dropdownTrigger.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
          dropdownMenu.classList.remove('show');
          dropdownTrigger.classList.remove('active');
        });

        // Dropdown item selection
        dropdownMenu.addEventListener('click', (e) => {
          if (e.target.classList.contains('dropdown-item')) {
            const value = e.target.dataset.value;
            const label = e.target.textContent;

            document.querySelectorAll('.dropdown-item').forEach(item => {
              item.classList.remove('selected');
            });
            e.target.classList.add('selected');

            currentResource = value;
            currentResourceLabel = label;
            selectedResourceSpan.textContent = label;

            localStorage.setItem('selectedResource', value);
            localStorage.setItem('selectedResourceLabel', label);

            addMessage(`Ressource gewechselt zu: ${label}`, 'bot');
          }
        });

        // Load saved resource
        const savedResource = localStorage.getItem('selectedResource');
        const savedLabel = localStorage.getItem('selectedResourceLabel');
        if (savedResource) {
          currentResource = savedResource;
          currentResourceLabel = savedLabel || 'Supervisor';
          selectedResourceSpan.textContent = currentResourceLabel;
          
          document.querySelectorAll('.dropdown-item').forEach(item => {
            if (item.dataset.value === savedResource) {
              item.classList.add('selected');
            } else {
              item.classList.remove('selected');
            }
          });
        }

        function addMessage(text, sender) {
          const messageDiv = document.createElement('div');
          messageDiv.className = `message ${sender}`;
          
          const contentDiv = document.createElement('div');
          contentDiv.className = 'message-content';
          contentDiv.textContent = text;
          
          messageDiv.appendChild(contentDiv);
          messagesContainer.appendChild(messageDiv);
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        async function sendMessage() {
          const text = input.value.trim();
          if (!text) return;

          input.value = '';
          addMessage(text, 'user');

          sendBtn.disabled = true;
          sendBtn.textContent = 'Denke...';

          try {
            const res = await fetch('/api/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message: text,
                resource: currentResource
              })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Request failed');

            addMessage(data.reply, 'bot');
          } catch (e) {
            addMessage(`Fehler: ${e.message}`, 'bot');
          } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Senden';
            input.focus();
          }
        }

        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        });

        // Auto-resize textarea
        input.addEventListener('input', function() {
          this.style.height = 'auto';
          this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });

        input.focus();
        addMessage(`Willkommen bei FlexGuide4! Du bist angemeldet als: ${currentResourceLabel}`, 'bot');
      </script>
    </body>
    </html>
    """


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    resource = (data.get("resource") or "SUPERVISOR").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400
    
    if resource not in AVAILABLE_RESOURCES:
        return jsonify({"error": f"Invalid resource: {resource}"}), 400

    # Session ID aus Flask Session oder generiere neue
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']

    try:
        reply = bot_reply(message, session_id=session_id, resource_id=resource)
        
        print(f"Session ID: {session_id}")
        print(f"Response Length: {len(reply)}")
        print(f"Full Response:\n{reply}")
        print("="*50)

        return jsonify({"reply": reply})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)