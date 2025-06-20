import os
from telegram.ext import Application, CommandHandler

async def start(update, context):
    await update.message.reply_text('Hello!')

app = Application.builder().token("7620538088:AAGCKXgtDrzfg2jUnAY4WYp9rgwxNy6oOOE").build()
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url="https://peacemissile-bot-app-50391cca531c.herokuapp.com/7620538088:AAGCKXgtDrzfg2jUnAY4WYp9rgwxNy6oOOE"
    )
