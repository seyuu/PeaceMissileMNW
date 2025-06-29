import os
import base64
from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, firestore

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, Dispatcher, MessageHandler, filters
from telegram.ext import WebhookHandler

import threading

# -------------------- Firebase Setup --------------------
if os.environ.get("FIREBASE_CREDS_BASE64"):
    with open("firebase-key.json", "w") as f:
        f.write(base64.b64decode(os.environ["FIREBASE_CREDS_BASE64"]).decode())

cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# -------------------- Flask Setup --------------------
app = Flask(__name__)

# -------------------- Telegram Setup --------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN") or "7620538088:AAGCKXgtDrzfg2jUnAY4WYp9rgwxNy6oOOE"
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL") or "https://peacemissile-bot-app-50391cca531c.herokuapp.com"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Peace Missile Game Bot Online! Oyunu oynamak için:\nhttps://peacemissile-game-ui.onrender.com"
    )

application.add_handler(CommandHandler("start", start))

# --------------- Save Score Endpoint ---------------
@app.route("/save_score", methods=["POST"])
def save_score():
    data = request.json
    user_id = str(data.get("user_id"))
    score = int(data.get("score", 0))
    username = data.get("username", "Player")

    user_ref = db.collection("users").document(user_id)
    user = user_ref.get().to_dict()

    total_score = score
    total_pmno_coins = score

    if user:
        total_score += user.get("total_score", 0)
        total_pmno_coins += user.get("total_pmno_coins", 0)

    user_ref.set({
        "username": username,
        "score": max(user.get("score", 0) if user else 0, score),
        "total_score": total_score,
        "total_pmno_coins": total_pmno_coins
    }, merge=True)
    return "OK", 200

# --------------- Root Endpoint ---------------
@app.route("/", methods=["GET"])
def root():
    return "Peace Missile Score API OK", 200

# --------------- Telegram Webhook Endpoint ---------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    """Telegram Webhook endpointi"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK", 200

# --------------- Main Run ---------------
def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Set webhook
    import asyncio
    asyncio.get_event_loop().run_until_complete(application.bot.set_webhook(WEBHOOK_URL))

    # Flask ve Telegram handler aynı processte çalışacak
    threading.Thread(target=run_flask).start()
    application.run_polling(stop_signals=None)  # polling yerine sadece update_queue ile çalışacak
