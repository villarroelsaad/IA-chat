"""
chat.py

Chat bot de consola que intenta usar la librería de Google/GenAI si está
configurada; si no, ejecuta un modo de respaldo simple (sin llamada a la API)
para poder probar localmente.

Uso: python chat.py
Escribe 'exit' o 'quit' para salir, 'help' para ver comandos.
"""
from __future__ import annotations

import os
from typing import List, Dict

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

API_AVAILABLE = False
client = None
chat = None

# Cargar .env si python-dotenv está disponible
if load_dotenv is not None:
    load_dotenv(override=True)

# Leer variables de entorno (pueden ser inyectadas por docker-compose)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Intentar importar google.genai (Gemini-like). Si falla, usamos fallback.
try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    API_AVAILABLE = True
except Exception:
    API_AVAILABLE = False


class SimpleFallbackBot:
    """Un bot muy simple que responde con reglas básicas.

    - Responde preguntas sobre perros/patas de ejemplo
    - Devuelve eco si no reconoce la intención
    """

    def __init__(self, system_instruction: str | None = None):
        self.system_instruction = system_instruction or ""
        self.history: List[Dict[str, str]] = []

    def send_message(self, message: str) -> Dict[str, str]:
        self.history.append({"role": "user", "text": message})
        text = message.lower().strip()
        resp = "Lo siento, no entiendo. ¿Puedes reformular?"
        # Reglas muy simples de ejemplo
        if "dog" in text or "perro" in text or "perros" in text:
            resp = "¡Qué bien! Los perros son geniales. ¿Cuántos tienes?"
        if "paws" in text or "patas" in text:
            # Intentar detectar número en la entrada
            import re

            nums = re.findall(r"\d+", text)
            if nums:
                n = int(nums[0])
                resp = f"Si tienes {n} perros, hay {n*4} patas en total (suponiendo 4 patas por perro)."
            else:
                resp = "¿Cuántos perros tienes? Puedo calcular las patas si me das un número."

        # Añadir al historial de respuestas
        self.history.append({"role": "assistant", "text": resp})
        return {"text": resp}

    def get_history(self):
        return self.history


def create_api_chat(system_instruction: str | None = None, model: str | None = None):
    """Crear cliente de chat usando google.genai si está disponible.

    Devuelve un objeto con métodos send_message(text)->{text:...} y get_history()->list
    """
    global client, chat

    if not API_AVAILABLE:
        raise RuntimeError("La librería google.genai no está disponible")

    # Inicializar cliente y conversación
    client = genai.Client()
    cfg = types.GenerateContentConfig(system_instruction=system_instruction or "", temperature=0.8)
    chat = client.chats.create(model=model or GEMINI_MODEL, config=cfg)

    class ApiWrapper:
        def send_message(self, message: str) -> Dict[str, str]:
            res = chat.send_message(message)
            return {"text": res.text}

        def get_history(self):
            return chat.get_history()

    return ApiWrapper()


def print_help():
    print("Comandos disponibles:")
    print("  help       Mostrar esta ayuda")
    print("  exit/quit  Salir del chat")
    print("Escribe cualquier mensaje para recibir una respuesta.")


def main():
    system_instruction = "Eres un asistente para tareas cotidianas. Responde de forma útil y amigable." 
    model = GEMINI_MODEL

    # Usar la variable leída desde el entorno (docker-compose puede inyectarla)
    if API_AVAILABLE and GEMINI_API_KEY:
        try:
            bot = create_api_chat(system_instruction=system_instruction, model=model)
            print("Usando cliente API (google.genai).\nEscribe 'help' para ver comandos.")
        except Exception as e:
            print(f"No se pudo inicializar la API: {e}\nUsando modo fallback local.")
            bot = SimpleFallbackBot(system_instruction=system_instruction)
    else:
        print("Modo fallback: no se detectó la librería de API o la clave.\nUsando bot local simple. Escribe 'help' para ver comandos.")
        bot = SimpleFallbackBot(system_instruction=system_instruction)

    # Bucle de conversación
    try:
        while True:
            prompt = input("Tú: ")
            if not prompt:
                continue
            cmd = prompt.strip().lower()
            if cmd in ("exit", "quit"):
                print("Adiós!")
                break
            if cmd == "help":
                print_help()
                continue

            res = bot.send_message(prompt)
            print(f"Bot: {res.get('text','')}")

    except (KeyboardInterrupt, EOFError):
        print("\nSaliendo...")


if __name__ == "__main__":
    main()