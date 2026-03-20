import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")  # optional security token

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    return response.ok

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Bot is running ✅"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # Optional: verify secret token
    if WEBHOOK_SECRET:
        token = request.args.get("token") or request.headers.get("X-Secret-Token")
        if token != WEBHOOK_SECRET:
            return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    # TradingView sends plain text or JSON — handle both
    if not data:
        raw = request.data.decode("utf-8").strip()
        message = f"🚨 <b>TradingView Alert</b>\n\n{raw}"
    else:
        # Build a nicely formatted message from JSON fields
        ticker   = data.get("ticker", "N/A")
        price    = data.get("price", "N/A")
        action   = data.get("action", "").upper()
        interval = data.get("interval", "")
        message_text = data.get("message", "")

        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚡"

        message = (
            f"{emoji} <b>TradingView Alert</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📊 <b>Ticker:</b> {ticker}\n"
            f"💰 <b>Price:</b> {price}\n"
        )
        if action:
            message += f"📌 <b>Action:</b> {action}\n"
        if interval:
            message += f"⏱ <b>Interval:</b> {interval}\n"
        if message_text:
            message += f"📝 <b>Note:</b> {message_text}\n"

    success = send_telegram_message(message)

    if success:
        return jsonify({"status": "Message sent ✅"}), 200
    else:
        return jsonify({"status": "Failed to send message ❌"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
