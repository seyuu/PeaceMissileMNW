import os
import logging
import json
import firebase_admin
import base64
from fastapi import FastAPI, Request, Response
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes
from firebase_admin import credentials, firestore

# --- 1. Kurulum ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
FIREBASE_CREDS_BASE64 = os.environ.get("FIREBASE_CREDS_BASE64")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL")
WEBHOOK_URL_PATH = f"/{TELEGRAM_TOKEN}"

# --- 2. Firebase Bağlantısı ---
db = None
try:
    decoded_creds = base64.b64decode(FIREBASE_CREDS_BASE64)
    cred_json = json.loads(decoded_creds)
    cred = credentials.Certificate(cred_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase connection successful.")
except Exception as e:
    logger.error(f"FATAL: Could not initialize Firebase: {e}")

# --- 3. Telegram Bot Application ---
application = Application.builder().token(TELEGRAM_TOKEN).build()
api = FastAPI()

# --- 4. Bot Fonksiyonları ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıyı karşılar, DB'de oluşturur ve oyun linkini verir."""
    if not db:
        await update.message.reply_text("Database not connected. Please contact admin.")
        return
        
    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))
    if not user_ref.get().exists:
        user_ref.set({
            'username': user.username or user.first_name,
            'first_name': user.first_name,
            'score': 0, 'total_score': 0, 'total_pmno_coins': 0, 'user_id': user.id
        })
    
    keyboard = [[
        InlineKeyboardButton("Start Game", web_app=WebAppInfo(url=WEB_APP_URL))
    ]]
    # Fotoğraf ve metni bir arada gönderiyoruz.
    await update.message.reply_photo(
        photo="https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/public/assets/logo.png",
        caption=f"Welcome, {user.first_name}! Click the button below to play.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_score_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """WebApp'ten gelen skoru alır ve Firebase'e yazar."""
    logger.info("--- Web App Data Received ---")
    try:
        data_str = update.effective_message.web_app_data.data
        payload = json.loads(data_str)
        user_id = str(payload.get("user_id"))
        game_score = int(payload.get("score"))
        
        if str(update.effective_user.id) != user_id:
            logger.warning("User ID mismatch!")
            return

        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()

        if doc.exists:
            user_data = doc.to_dict()
            current_high_score = user_data.get('score', 0)
            total_score = user_data.get('total_score', 0) + game_score
            total_coins = user_data.get('total_pmno_coins', 0) + game_score
            is_new_record = False
            if game_score > current_high_score:
                is_new_record = True
                current_high_score = game_score
                total_coins += game_score * 100
            
            user_ref.update({'score': current_high_score, 'total_score': total_score, 'total_pmno_coins': total_coins})
            logger.info(f"SUCCESS: DB updated for user {user_id}.")
            
            message = f"Score saved: {game_score}."
            if is_new_record: message += f"\n\n🏆 NEW HIGH SCORE: {current_high_score}! 🏆"
            await update.effective_message.reply_text(message)
    except Exception as e:
        logger.error(f"ERROR processing score: {e}", exc_info=True)

# --- 5. Sunucu ve Ana İstek İşleyici ---

@api.post(WEBHOOK_URL_PATH)
async def main_webhook_handler(request: Request) -> Response:
    """Gelen tüm güncellemeleri alır ve içeriğine göre yönlendirir."""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    
    if update.message and update.message.text and update.message.text == "/start":
        await start(update, None)
    elif update.message and update.message.web_app_data:
        await process_score_update(update, None)
        
    return Response(status_code=200)

@api.on_event("startup")
async def on_startup():
    await application.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}")

@api.on_event("shutdown")
async def on_shutdown():
    await application.bot.delete_webhook()