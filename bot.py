import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes

# --- Kurulum ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL") # Oyunun adresi
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL")
WEBHOOK_URL_PATH = f"/{TELEGRAM_TOKEN}"

application = Application.builder().token(TELEGRAM_TOKEN).build()
api = FastAPI()

# --- SADECE TEK BİR FONKSİYON ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sadece oyun linkini içeren bir buton gönderir."""
    keyboard = [[
        InlineKeyboardButton("Start Game", web_app=WebAppInfo(url=WEB_APP_URL))
    ]]
    await update.message.reply_text(
        f"Welcome! Click the button below to play.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- Sunucu ve Webhook Kurulumu ---
@api.post(WEBHOOK_URL_PATH)
async def telegram_webhook(request: Request) -> Response:
    """Gelen isteği alır ve sadece /start ise cevaplar."""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    
    if update.message and update.message.text == "/start":
        await start(update, None)
        
    return Response(status_code=200)

@api.on_event("startup")
async def on_startup():
    await application.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}")

@api.on_event("shutdown")
async def on_shutdown():
    await application.bot.delete_webhook()