import os
from telegram.ext import Application, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN") or "7620538088:AAGCKXgtDrzfg2jUnAY4WYp9rgwxNy6oOOE"
PORT = int(os.environ.get('PORT', 5000))
WEBHOOK = f"https://peacemissile-bot-app-50391cca531c.herokuapp.com/{TOKEN}"

app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Peace Missile Game Bot Online!")

app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    print("PEACEMISSILE BOT BAŞLIYOR!")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK
    )
