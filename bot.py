from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
app = Flask(__name__)

# dispatcher ile handler'ları kaydet
dispatcher = Dispatcher(bot, None, workers=0)

def start(update, context):
    update.message.reply_text('Peace Missile Bot aktif!')

dispatcher.add_handler(CommandHandler("start", start))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot Çalışıyor"

if __name__ == "__main__":
    # Set webhook on deploy
    url = os.getenv("WEBHOOK_BASE_URL")  # örn: https://peacemissile-bot-app-xxxx.herokuapp.com
    bot.set_webhook(f"{url}/{TOKEN}")
    app.run(port=5000, debug=True)
