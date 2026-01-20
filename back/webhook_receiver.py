from __future__ import annotations

import os
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(override=True)

from flask import Flask, request, jsonify

app = Flask(__name__)

EXPECTED_AUTH = os.environ.get("WEBHOOK_AUTH")

@app.route("/webhook", methods=["POST"])
def webhook():
    auth = request.headers.get("Authorization")
    if EXPECTED_AUTH and auth != EXPECTED_AUTH:
        return jsonify({"error": "unauthorized"}), 401

    # Try to parse JSON, fall back to raw body
    try:
        payload = request.get_json(force=True)
    except Exception:
        payload = request.data.decode("utf-8")

    # Log to stdout (visible when running the server)
    print("[webhook_receiver] received webhook:", payload)

    # Respond with received data for easy testing
    return jsonify({"ok": True, "received": payload}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    app.run(host="0.0.0.0", port=port)
