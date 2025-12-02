"""
chat.py

Console chat bot that attempts to use the Google/GenAI library if configured; if
not, it runs a simple fallback mode (no API call) for local testing.

Usage: python chat.py
Type 'exit' or 'quit' to exit, 'help' to see commands.
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

# Load .env if python-dotenv is available
# Cargar .env si python-dotenv está disponible
if load_dotenv is not None:
    load_dotenv(override=True)

# Read environment variables (can be injected by docker-compose)
# Leer variables de entorno (pueden ser inyectadas por docker-compose)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Try to import google.genai (Gemini-like). If it fails, we use fallback.
# Intentar importar google.genai (tipo Gemini). Si falla, usamos fallback.
try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    API_AVAILABLE = True
except Exception:
    API_AVAILABLE = False


class SimpleFallbackBot:
    """A very simple bot that responds with basic rules.

    - Answers questions about example dogs/paws
    - Returns echo if the intent is not recognized
    """

    def __init__(self, system_instruction: str | None = None):
        self.system_instruction = system_instruction or ""
        self.history: List[Dict[str, str]] = []

    def send_message(self, message: str) -> Dict[str, str]:
        self.history.append({"role": "user", "text": message})
        text = message.lower().strip()
        # resp = "Lo siento, no entiendo. ¿Puedes reformular?"
        resp = "I'm sorry, I don't understand. Can you rephrase?"
        # Simple example rules
        # Reglas muy simples de ejemplo
        if "dog" in text or "perro" in text or "perros" in text:
            # resp = "¡Qué bien! Los perros son geniales. ¿Cuántos tienes?"
            resp = "That's great! Dogs are awesome. How many do you have?"
        if "paws" in text or "patas" in text:
            # Intentar detectar número en la entrada
            # Try to detect a number in the input
            import re

            nums = re.findall(r"\d+", text)
            if nums:
                n = int(nums[0])
                # resp = f"Si tienes {n} perros, hay {n*4} patas en total (suponiendo 4 patas por perro)."
                resp = f"If you have {n} dogs, there are {n*4} paws in total (assuming 4 paws per dog)."
            else:
                # resp = "¿Cuántos perros tienes? Puedo calcular las patas si me das un número."
                resp = "How many dogs do you have? I can calculate the paws if you give me a number."

        # Add to response history
        # Añadir al historial de respuestas
        self.history.append({"role": "assistant", "text": resp})
        return {"text": resp}

    def get_history(self):
        return self.history


def create_api_chat(system_instruction: str | None = None, model: str | None = None):
    """Create chat client using google.genai if available.

    Returns an object with methods send_message(text)->{text:...} and get_history()->list
    """
    global client, chat

    if not API_AVAILABLE:
        # raise RuntimeError("La librería google.genai no está disponible")
        raise RuntimeError("The google.genai library is not available")

    # Initialize client and conversation
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
    # print("Comandos disponibles:")
    print("Available Commands:")
    # print("  help       Mostrar esta ayuda")
    print("  help       Show this help")
    # print("  exit/quit  Salir del chat")
    print("  exit/quit  Exit chat")
    # print("Escribe cualquier mensaje para recibir una respuesta.")
    print("Type any message to receive a reply.")


def main():
    # system_instruction = "Eres un asistente para tareas cotidianas. Responde de forma útil y amigable."
    system_instruction = "You are an assistant for everyday tasks. Respond in a helpful and friendly manner." 
    model = GEMINI_MODEL

    # Use the variable read from the environment (docker-compose can inject it)
    # Usar la variable leída desde el entorno (docker-compose puede inyectarla)
    if API_AVAILABLE and GEMINI_API_KEY:
        try:
            bot = create_api_chat(system_instruction=system_instruction, model=model)
            # print("Usando cliente API (google.genai).\nEscribe 'help' para ver comandos.")
            print("Using API client (google.genai).\nType 'help' to see commands.")
        except Exception as e:
            # print(f"No se pudo inicializar la API: {e}\nUsando modo fallback local.")
            print(f"Could not initialize API: {e}\nUsing local fallback mode.")
            bot = SimpleFallbackBot(system_instruction=system_instruction)
    else:
        # print("Modo fallback: no se detectó la librería de API o la clave.\nUsando bot local simple. Escribe 'help' para ver comandos.")
        print("Fallback mode: API library or key not detected.\nUsing simple local bot. Type 'help' to see commands.")
        bot = SimpleFallbackBot(system_instruction=system_instruction)

    # Conversation loop
    # Bucle de conversación
    try:
        while True:
            # prompt = input("Tú: ")
            prompt = input("You: ")
            if not prompt:
                continue
            cmd = prompt.strip().lower()
            if cmd in ("exit", "quit"):
                # print("Adiós!")
                print("Goodbye!")
                break
            if cmd == "help":
                print_help()
                continue

            res = bot.send_message(prompt)
            # print(f"Bot: {res.get('text','')}")
            print(f"Bot: {res.get('text','')}")

    except (KeyboardInterrupt, EOFError):
        # print("\nSaliendo...")
        print("\nExiting...")


if __name__ == "__main__":
    main()