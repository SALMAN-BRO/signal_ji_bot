import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Works with both TELEGRAM_CHAT_ID and TELEGRAM_CHAT_IDS
raw_ids = os.environ.get("TELEGRAM_CHAT_IDS") or os.environ.get("TELEGRAM_CHAT_ID", "")
CHAT_IDS = [cid.strip() for cid in raw_ids.split(",") if cid.strip()]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    all_ok = True
    for chat_id in CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"Failed to send to {chat_id}: {response.text}")
            all_ok = False
        else:
            print(f"Message sent to {chat_id} ✅")
    return all_ok

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Bot is running ✅"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verify secret token if set
    if WEBHOOK_SECRET:
        token = request.args.get("token") or request.headers.get("X-Secret-Token")
        if token != WEBHOOK_SECRET:
            return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    if not data:
        raw = request.data.decode("utf-8").strip()
        message = f"🚨 <b>TradingView Alert</b>\n\n{raw}"
    else:
        ticker    = data.get("ticker",    "N/A")
        signal    = data.get("signal",    "N/A")
        timeframe = data.get("timeframe", data.get("interval", "N/A"))
        price     = data.get("price",     "N/A")
        action    = data.get("action",    "").upper()

        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚡"

        message = (
            f"{emoji} <b>New Signal Alert</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📊 <b>Ticker</b>      :  {ticker}\n"
            f"📌 <b>Signal</b>      :  {signal}\n"
            f"⏱ <b>Timeframe</b>  :  {timeframe}\n"
            f"💰 <b>Price</b>       :  {price}\n"
        )

    success = send_telegram_message(message)

    if success:
        return jsonify({"status": "Message sent ✅"}), 200
    else:
        return jsonify({"status": "Failed to send message ❌"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
