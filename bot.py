import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN") or "7620538088:AAGCKXgtDrzfg2jUnAY4WYp9rgwxNy6oOOE"
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL") or "https://peacemissile-bot-app-50391cca531c.herokuapp.com/"
PORT = int(os.environ.get("PORT", 8000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Peace Missile Game Bot Online!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/{TOKEN}"

    # YENİ: run_webhook çağrısı
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()
