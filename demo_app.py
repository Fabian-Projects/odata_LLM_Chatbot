from flask import Flask, request, jsonify
from src.llm_parser import LLMQueryParser
from src.odata_client import ODataClient
from src.calculation_engine import CalculationEngine
from src.response_generator import ResponseGenerator
from config.settings import Config

from dotenv import load_dotenv
load_dotenv()  # sorgt dafür, dass Config die .env wirklich sieht

parser = client = engine = generator = None

def init_pipeline():
    global parser, client, engine, generator
    if parser is not None:
        return  # schon initialisiert

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

# Globale Variable für Session-Context (einfache Variante)
conversation_contexts = {}

def bot_reply(user_message: str, session_id: str = "default") -> str:
    """Pipeline mit Kontext-Memory"""
    init_pipeline()
    
    # Kontext laden
    last_context = conversation_contexts.get(session_id)
    
    # Input mit Kontext anreichern
    if last_context:
        enriched_input = f"{user_message}\n\nKontext der letzten Anfrage:\n{last_context}"
    else:
        enriched_input = user_message
    
    # Parse
    parsed = parser.parse_query(enriched_input)
    
    # Checks
    if parsed.get("intent") == "error":
        return parsed.get("response_context", {}).get("friendly_description", "Parsing-Fehler")
    
    if not parsed.get("isAnswerable", True):
        reason = parsed.get("reason", "Diese Frage kann ich nicht beantworten.")
        return f"{reason}\n\nIch kann dir nur Informationen über Fahraufträge geben."
    
    # Pipeline
    odata_result = client.execute_query(parsed)
    calc_result = engine.process(odata_result, parsed.get("calculation"))
    response = generator.generate(calc_result, parsed.get("response_context"))
    
    # Kontext speichern
    conversation_contexts[session_id] = (
        f"Frage: {user_message}\n"
        f"Filter: {parsed.get('odata_params', {}).get('$filter', 'keine')}\n"
        f"Ergebnis: {calc_result.get('summary', 'N/A')}"
    )
    
    return response



app = Flask(__name__)

@app.get("/")
def home():
    return """
    <!doctype html>
    <html lang="de">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>FlexGuide4 Chatbot</title>
      <style>

        :root {
          --accent: #F97306;
          --accent-soft: rgba(249, 115, 6, 0.15);
          --accent-border: rgba(249, 115, 6, 0.4);
        }

        body {
          font-family: system-ui, sans-serif;
          margin: 0;
          background: #0b0f17;
          color: #e7eaf0;
        }

        .wrap {
          max-width: 900px;
          margin: 0 auto;
          padding: 24px;
        }

        .card {
          background: #121a27;
          border: 1px solid #22324a;
          border-radius: 16px;
          padding: 16px;
        }

        .messages {
          height: 65vh;
          overflow: auto;
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 10px;
          border-radius: 12px;
          background: #0f1623;
          border: 1px solid #22324a;
        }

        .msg {
          max-width: 75%;
          padding: 12px 14px;
          border-radius: 14px;
          line-height: 1.35;
          white-space: pre-wrap;
        }

        .user {
          align-self: flex-end;
          background: var(--accent);
          color: white;
        }

        .bot {
          align-self: flex-start;
          background: #1b2638;
          border: 1px solid #2b3c59;
        }

        .row {
          display: flex;
          gap: 10px;
          margin-top: 12px;
        }

        input {
          flex: 1;
          padding: 14px;
          border-radius: 12px;
          border: 1px solid #2b3c59;
          background: #0f1623;
          color: #e7eaf0;
        }

        input:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 2px var(--accent-soft);
        }

        button {
          padding: 14px 18px;
          border-radius: 12px;
          border: 0;
          background: var(--accent);
          color: white;
          cursor: pointer;
        }

        button:hover {
          filter: brightness(1.05);
        }

        button:disabled {
          opacity: .6;
          cursor: not-allowed;
        }

        .title {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        
        h2 {
          margin: 0;
          color: var(--accent);
          font-size: 32px;
          font-weight: 700;
          letter-spacing: 0.3px;
        }

        .badge {
          font-size: 12px;
          padding: 6px 12px;
          border-radius: 999px;
          background: var(--accent-soft);
          border: 1px solid var(--accent-border);
          color: var(--accent);
        }

      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="title">
          <h2>FlexGuide4 Chatbot</h2>
          <div class="badge" id="status">bereit</div>
        </div>

        <div class="card">
          <div class="messages" id="messages"></div>

          <div class="row">
            <input id="input" placeholder="Stell eine Frage…" />
            <button id="send">Senden</button>
          </div>
        </div>
      </div>

      <script>
        const messages = document.getElementById("messages");
        const input = document.getElementById("input");
        const sendBtn = document.getElementById("send");
        const status = document.getElementById("status");

        function add(text, who) {
          const div = document.createElement("div");
          div.className = `msg ${who}`;
          div.textContent = text;
          messages.appendChild(div);
          messages.scrollTop = messages.scrollHeight;
        }

        async function send() {
          const text = input.value.trim();
          if (!text) return;

          input.value = "";
          add(text, "user");

          sendBtn.disabled = true;
          status.textContent = "denke…";

          try {
            const res = await fetch("/api/chat", {
              method: "POST",
              headers: {"Content-Type":"application/json"},
              body: JSON.stringify({ message: text })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Request failed");

            add(data.reply, "bot");
            status.textContent = "bereit";
          } catch (e) {
            add("Fehler: " + e.message, "bot");
            status.textContent = "fehler";
          } finally {
            sendBtn.disabled = false;
            input.focus();
          }
        }

        sendBtn.addEventListener("click", send);
        input.addEventListener("keydown", (e) => {
          if (e.key === "Enter") send();
        });

        input.focus();
        add("Hi! Ich bin der FlexGuide4 Chatbot.", "bot");
      </script>
    </body>
    </html>
    """


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        reply = bot_reply(message)
        return jsonify({"reply": reply})
    except Exception as e:
        # Fürs Debuggen: Fehlertext zurückgeben (später kann man das kürzen)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)