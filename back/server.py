from __future__ import annotations

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from chat.chat import SimpleFallbackBot, create_api_chat, API_AVAILABLE, GEMINI_API_KEY

app = Flask(__name__)
CORS(app)

# In-memory storage for uploaded file texts (simple approach)
# Almacenamiento en memoria para los textos de archivos subidos (enfoque simple)
FILE_TEXTS: list[str] = []

system_instruction = (
    # "Eres un asistente de tareas cotidianas. Responde de forma útil y amigable."
    "You are an everyday task assistant. Respond in a helpful and friendly manner."
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
    # if not data or "message" not in data:
    if not data or "message" not in data:
        # return jsonify({"error": "Se requiere 'message' en el cuerpo JSON"}), 400
        return jsonify({"error": "Required 'message' in JSON body"}), 400

    message = data["message"]
    try:
        # Incorporate recent file texts into the prompt so the bot responds based on them
        # Incorporar textos de archivos recientes en el prompt para que el bot responda basándose en ellos
        # Limit the amount of text to avoid huge prompts
        # Limitar la cantidad de texto para evitar prompts enormes
        recent_files_text = "\n\n".join(FILE_TEXTS[-5:]) if FILE_TEXTS else ""
        combined = message
        if recent_files_text:
            # combined = f"{message}\n\nContexto de archivos:\n{recent_files_text}"
            combined = f"{message}\n\nFile Context:\n{recent_files_text}"

        response = BOT.send_message(combined)
        return jsonify({"reply": response.get("text", "")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload-file", methods=["POST"])
def upload_file():
    # await multipart/form-data with 'file'
    # esperar multipart/form-data con 'file'
    if 'file' not in request.files:
        # return jsonify({"error": "No se encontró el archivo en el campo 'file'"}), 400
        return jsonify({"error": "File not found in 'file' field"}), 400

    f = request.files['file']
    if f.filename == '':
        # return jsonify({"error": "Nombre de archivo vacío"}), 400
        return jsonify({"error": "Empty filename"}), 400

    filename = f.filename
    #  text from file
    # texto desde el archivo
    try:
        text = extract_text_from_file(f, filename)
    except Exception as e:
        # return jsonify({"error": f"No se pudo extraer texto: {e}"}), 500
        return jsonify({"error": f"Could not extract text: {e}"}), 500

    # save in memory  (small project/demo). In production use persistent storage/DB
    # guardar en memoria (proyecto/demo pequeño). En producción usar almacenamiento persistente/DB
    FILE_TEXTS.append(f"== {filename} ==\n" + text)
    return jsonify({"ok": True, "filename": filename})


def extract_text_from_file(file_storage, filename: str) -> str:
    # """Intentar extraer texto de .txt, .pdf, .docx. Lee el stream del file_storage."""
    """Try to extract text from .txt, .pdf, .docx. Reads the file_storage stream."""
    lower = filename.lower()
    # Reset file pointer
    # Reiniciar puntero de archivo
    file_storage.stream.seek(0)
    if lower.endswith('.txt'):
        # Leer como texto
        # Read as text
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
            # PyPDF2 puede aceptar un objeto tipo archivo
            reader = PdfReader(file_storage.stream)
            texts = []
            for page in reader.pages:
                try:
                    texts.append(page.extract_text() or '')
                except Exception:
                    continue
            return '\n'.join(texts)
        except Exception as e:
            # raise RuntimeError(f'error extrayendo pdf: {e}')
            raise RuntimeError(f'error extracting pdf: {e}')

    if lower.endswith('.docx'):
        try:
            import docx

            # python-docx expects a path or file-like object; it supports file-like
            # python-docx espera una ruta o un objeto tipo archivo; soporta tipo archivo
            doc = docx.Document(file_storage.stream)
            texts = [p.text for p in doc.paragraphs]
            return '\n'.join(texts)
        except Exception as e:
            # raise RuntimeError(f'error extrayendo docx: {e}')
            raise RuntimeError(f'error extracting docx: {e}')

    
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