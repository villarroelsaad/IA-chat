from __future__ import annotations
import os
import threading
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    load_dotenv = None

# Configuración de Webhooks y Bot
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_AUTH = os.environ.get("WEBHOOK_AUTH")

from chat.chat import SimpleFallbackBot, create_api_chat, API_AVAILABLE, GEMINI_API_KEY

app = Flask(__name__)
CORS(app)
# Inicializamos SocketIO para comunicación en tiempo real con el frontend
socketio = SocketIO(app, cors_allowed_origins="*")

FILE_TEXTS: list[str] = []
system_instruction = "You are an everyday task assistant. Respond in a helpful and friendly manner."

def get_bot():
    if API_AVAILABLE and GEMINI_API_KEY:
        try:
            return create_api_chat(system_instruction=system_instruction)
        except Exception:
            return SimpleFallbackBot(system_instruction=system_instruction)
    return SimpleFallbackBot(system_instruction=system_instruction)

BOT = get_bot()

# --- FUNCIONES DE APOYO PARA WEBHOOKS ---

def _notify_webhook(payload: dict) -> None:
    """Envía la petición POST al webhook configurado."""
    if not WEBHOOK_URL:
        return
    try:
        headers = {"Content-Type": "application/json"}
        if WEBHOOK_AUTH:
            headers["Authorization"] = WEBHOOK_AUTH
        resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        app.logger.info(f"Webhook POST to {WEBHOOK_URL} returned {resp.status_code}")
    except Exception as e:
        app.logger.warning(f"Webhook POST failed: {e}")

def notify_webhook_async(payload: dict) -> None:
    """Ejecuta el envío del webhook en un hilo separado para no bloquear."""
    t = threading.Thread(target=_notify_webhook, args=(payload,), daemon=True)
    t.start()

# --- RUTAS DE LA API ---

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json(force=True)
    if not data or "message" not in data:
        return jsonify({"error": "Required 'message' in JSON body"}), 400

    message = data["message"]
    try:
        recent_files_text = "\n\n".join(FILE_TEXTS[-5:]) if FILE_TEXTS else ""
        combined = message
        if recent_files_text:
            combined = f"{message}\n\nFile Context:\n{recent_files_text}"

        response = BOT.send_message(combined)
        return jsonify({"reply": response.get("text", "")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/webhook-receiver", methods=["POST"])
def webhook_receiver():
    """Recibe la notificación del webhook y avisa al frontend por WebSocket."""
    # Verificación de seguridad (Token)
    auth = request.headers.get("Authorization")
    if WEBHOOK_AUTH and auth != WEBHOOK_AUTH:
        return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        data = {"raw": request.data.decode("utf-8")}

    filename = data.get("filename", "unknown")
    
    print(f"--- NOTIFICACIÓN RECIBIDA ---")
    print(f"Archivo procesado: {filename}")

    # EMITIR AL FRONTEND: Aquí es donde el chat recibe el aviso automático
    socketio.emit('file_notification', {
        'message': f" He terminado de procesar tu archivo: {filename}. Ya puedes hacerme preguntas sobre él.",
        'filename': filename,
        'status': 'success'
    })
    
    return jsonify({"status": "received", "ok": True}), 200

@app.route("/upload-file", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "File not found in 'file' field"}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = f.filename
    try:
        text = extract_text_from_file(f, filename)
    except Exception as e:
        return jsonify({"error": f"Could not extract text: {e}"}), 500

    FILE_TEXTS.append(f"== {filename} ==\n" + text)
    
    # Disparar el flujo del webhook hacia nuestra propia ruta /webhook-receiver
    if WEBHOOK_URL:
        payload = {
            "filename": filename,
            "status": "uploaded",
            "text_snippet": (text or "")[:500],
        }
        notify_webhook_async(payload)

    return jsonify({"ok": True, "filename": filename})

# --- LÓGICA DE EXTRACCIÓN (PDF, DOCX, TXT) ---

def extract_text_from_file(file_storage, filename: str) -> str:
    lower = filename.lower()
    file_storage.stream.seek(0)
    
    if lower.endswith('.txt'):
        data = file_storage.stream.read()
        return data.decode('utf-8', errors='ignore') if isinstance(data, bytes) else str(data)

    if lower.endswith('.pdf'):
        from PyPDF2 import PdfReader
        reader = PdfReader(file_storage.stream)
        return '\n'.join([page.extract_text() or '' for page in reader.pages])

    if lower.endswith('.docx'):
        import docx
        doc = docx.Document(file_storage.stream)
        return '\n'.join([p.text for p in doc.paragraphs])

    return file_storage.stream.read().decode('utf-8', errors='ignore')

if __name__ == "__main__":
    # Importante: Usar socketio.run para habilitar WebSockets
    port = int(os.environ.get("PORT", 8000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)