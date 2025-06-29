import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
 
import base64

# Heroku'da ortam değişkeninden anahtar dosyası oluştur
if os.environ.get("FIREBASE_CREDS_BASE64"):
    with open("firebase-key.json", "w") as f:
        f.write(base64.b64decode(os.environ["FIREBASE_CREDS_BASE64"]).decode())
TOKEN = os.environ.get("TELEGRAM_TOKEN") or "7620538088:AAGCKXgtDrzfg2jUnAY4WYp9rgwxNy6oOOE"
PORT = int(os.environ.get("PORT", 8000))

WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL") or "https://peacemissile-bot-app-50391cca531c.herokuapp.com"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Peace Missile Game Bot Online! Oyunu oynamak için aşağıdaki bağlantıya tıkla:\nhttps://peacemissile-game-ui.onrender.com")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
