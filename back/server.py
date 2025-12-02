from __future__ import annotations

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from chat.chat import SimpleFallbackBot, create_api_chat, API_AVAILABLE, GEMINI_API_KEY

app = Flask(__name__)
CORS(app)

# In-memory storage for uploaded file texts (simple approach)
FILE_TEXTS: list[str] = []

# Inicializar bot: preferir API si está disponible y configurada
system_instruction = (
    "Eres un asistente de tareas cotidianas. Responde de forma útil y amigable."
)

def get_bot():

    if API_AVAILABLE and GEMINI_API_KEY:
        try:
            return create_api_chat(system_instruction=system_instruction)
        except Exception:
            return SimpleFallbackBot(system_instruction=system_instruction)
    return SimpleFallbackBot(system_instruction=system_instruction)


BOT = get_bot()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json(force=True)
    if not data or "message" not in data:
        return jsonify({"error": "Se requiere 'message' en el cuerpo JSON"}), 400

    message = data["message"]
    try:
        # Incorporar textos de archivos recientes al prompt para que el bot responda según ellos
        # Limitamos la cantidad de texto para evitar prompts enormes
        recent_files_text = "\n\n".join(FILE_TEXTS[-5:]) if FILE_TEXTS else ""
        combined = message
        if recent_files_text:
            combined = f"{message}\n\nContexto de archivos:\n{recent_files_text}"

        response = BOT.send_message(combined)
        return jsonify({"reply": response.get("text", "")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload-file", methods=["POST"])
def upload_file():
    # Espera multipart/form-data con campo 'file'
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en el campo 'file'"}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    filename = f.filename
    # Extraer texto según el tipo de archivo
    try:
        text = extract_text_from_file(f, filename)
    except Exception as e:
        return jsonify({"error": f"No se pudo extraer texto: {e}"}), 500

    # Guardar en memoria (pequeño proyecto/demo). En producción usar almacenamiento persistente/DB
    FILE_TEXTS.append(f"== {filename} ==\n" + text)
    return jsonify({"ok": True, "filename": filename})


def extract_text_from_file(file_storage, filename: str) -> str:
    """Intentar extraer texto de .txt, .pdf, .docx. Lee el stream del file_storage."""
    lower = filename.lower()
    # Reset file pointer
    file_storage.stream.seek(0)
    if lower.endswith('.txt'):
        # Leer como texto
        data = file_storage.stream.read()
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except Exception:
                return data.decode('latin-1', errors='ignore')
        return str(data)

    if lower.endswith('.pdf'):
        try:
            from PyPDF2 import PdfReader

            # PyPDF2 can accept a file-like object
            reader = PdfReader(file_storage.stream)
            texts = []
            for page in reader.pages:
                try:
                    texts.append(page.extract_text() or '')
                except Exception:
                    continue
            return '\n'.join(texts)
        except Exception as e:
            raise RuntimeError(f'error extrayendo pdf: {e}')

    if lower.endswith('.docx'):
        try:
            import docx

            # python-docx expects a path or file-like object; it supports file-like
            doc = docx.Document(file_storage.stream)
            texts = [p.text for p in doc.paragraphs]
            return '\n'.join(texts)
        except Exception as e:
            raise RuntimeError(f'error extrayendo docx: {e}')

    # Fallback: intentar decodificar como texto
    data = file_storage.stream.read()
    if isinstance(data, bytes):
        try:
            return data.decode('utf-8')
        except Exception:
            return data.decode('latin-1', errors='ignore')
    return str(data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
