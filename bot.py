import os
import logging
import time
import firebase_admin
import base64
import json
import asyncio
from fastapi import FastAPI, Request, Response
import uvicorn

from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# --- 1. GÜVENLİ KURULUM ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
FIREBASE_CREDS_BASE64 = os.environ.get("FIREBASE_CREDS_BASE64")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL")
WEBHOOK_URL_PATH = f"/{TELEGRAM_TOKEN}"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

db = None
try:
    if FIREBASE_CREDS_BASE64:
        decoded_creds = base64.b64decode(FIREBASE_CREDS_BASE64)
        cred_json = json.loads(decoded_creds)
        cred = credentials.Certificate(cred_json)
        logger.info("Firebase credentials loaded from environment variable.")
    else:
        # Yerel çalışma için bir fallback (Heroku'da bu kısım kullanılmayacak)
        cred = credentials.Certificate("firebase-key.json")
        logger.info("Firebase credentials loaded from local file.")
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase connection successful.")
except Exception as e:
    logger.error(f"FATAL: Could not initialize Firebase: {e}")
    db = None # Hata durumunda db'yi None yap

# Telegram Bot Application'ı oluştur
application = Application.builder().token(TELEGRAM_TOKEN).build()

# FastAPI uygulamasını oluştur
api = FastAPI()

# --- 2. BOT FONKSİYONLARI (Hiçbir değişiklik yok, sadece async ContextTypes.DEFAULT_TYPE ekledik) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Bu fonksiyonun içeriği tamamen aynı kalıyor...
    if not db:
        await update.message.reply_text("Database connection error. Please contact admin.")
        return
    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()
    if not user_doc.exists:
        user_data = {
            'username': user.username or user.first_name,
            'first_name': user.first_name, 'score': 0, 'total_score': 0,
            'total_pmno_coins': 0, 'user_id': user.id
        }
        user_ref.set(user_data)
        logger.info(f"New user created in Firestore: {user.username or user.first_name}")
    else:
        existing_data = user_doc.to_dict()
        update_needed = False
        if 'total_score' not in existing_data: existing_data['total_score'] = 0; update_needed = True
        if 'total_pmno_coins' not in existing_data: existing_data['total_pmno_coins'] = 0; update_needed = True
        if 'score' not in existing_data: existing_data['score'] = 0; update_needed = True
        if update_needed:
            user_ref.update(existing_data)
            logger.info(f"Existing user {user.username or user.first_name} updated.")
    keyboard = [[
        InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel&v={int(time.time())}")),
        InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran&v={int(time.time())}"))
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    photo_url = "https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/public/assets/logo.png"
    await update.message.reply_photo(
        photo=photo_url,
        caption=f"Welcome, Peace Ambassador {user.first_name}!\n\n"
                "The skies are filled with conflict. Choose a side to defend and turn rockets into doves of peace. Your mission starts now.\n\n"
                "Oyunun amacı ve coin kazanma hakkında bilgi almak için /help komutunu kullanın.",
        reply_markup=reply_markup
    )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Bu fonksiyonun içeriği tamamen aynı kalıyor...
    if not db: await update.message.reply_text("Database error."); return
    user_id = str(update.message.from_user.id)
    user_doc = db.collection('users').document(user_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        await update.message.reply_text(
            f"Your stats, Peace Ambassador:\n"
            f"Current Highest Game Score: {user_data.get('score', 0)} 🏆\n"
            f"Total Accumulated Score: {user_data.get('total_score', 0)} ☮️\n"
            f"Total PMNOFO Coins: {user_data.get('total_pmno_coins', 0)} 💰"
        )
    else:
        await update.message.reply_text("You haven't played yet! Use /start to begin.")

async def update_user_score(user_id: str, new_game_score: int):
    # Bu fonksiyonun içeriği tamamen aynı kalıyor...
    if not db: logger.error("DB error in update_user_score."); return False
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        current_highest_score = user_data.get('score', 0)
        total_accumulated_score = user_data.get('total_score', 0)
        total_pmno_coins = user_data.get('total_pmno_coins', 0)
        total_accumulated_score += new_game_score
        total_pmno_coins += new_game_score
        if new_game_score > current_highest_score:
            total_pmno_coins += new_game_score * 100
            current_highest_score = new_game_score
        user_ref.update({
            'score': current_highest_score, 'total_score': total_accumulated_score,
            'total_pmno_coins': total_pmno_coins
        })
        logger.info(f"User {user_id} scores updated.")
        return True
    else:
        logger.warning(f"User {user_id} not found to update score.")
        return False

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Bu fonksiyonun içeriği tamamen aynı kalıyor...
    data = update.effective_message.web_app_data.data
    logger.info(f"Received Web App Data: {data}")
    try:
        payload = json.loads(data)
        user_id = payload.get("user_id")
        final_score = payload.get("score")
        if not user_id or final_score is None:
            logger.error(f"Invalid payload from Web App: {payload}")
            return
        final_score = int(final_score)
        telegram_user_id = str(update.effective_user.id)
        if telegram_user_id != str(user_id):
            logger.warning(f"User ID mismatch: Telegram ({telegram_user_id}) vs Web App ({user_id})")
            return
        success = await update_user_score(telegram_user_id, final_score)
        if success:
            await update.effective_message.reply_text(
                f"Tebrikler! Yeni skorunuz {final_score} kaydedildi.\n"
                f"Güncel istatistiklerinizi görmek için /score yazın."
            )
        else:
            await update.effective_message.reply_text("Skorunuz kaydedilirken bir sorun oluştu.")
    except Exception as e:
        logger.error(f"Error in web_app_data_handler: {e}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Bu fonksiyonun içeriği tamamen aynı kalıyor...
    if not db: await update.message.reply_text("Database error."); return
    users_ref = db.collection('users').order_by('total_score', direction=firestore.Query.DESCENDING).limit(10)
    docs = users_ref.stream()
    leaderboard_text = "🏆 **Global Peace Leaderboard (Toplam Puan)** 🏆\n\n"
    position = 1
    for doc in docs:
        user_data = doc.to_dict()
        username = user_data.get('username') or user_data.get('first_name', 'Bilinmeyen')
        total_score = user_data.get('total_score', 0)
        leaderboard_text += f"{position}. {username} - {total_score} ☮️\n"
        position += 1
    if position == 1: leaderboard_text += "Henüz kimse oynamamış! İlk sen ol!"
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Bu fonksiyonun içeriği tamamen aynı kalıyor...
    help_text = "..." # (kısaltıldı)
    await update.message.reply_text(help_text, parse_mode='Markdown')

# --- 3. BOTU VE SUNUCUYU BAŞLATMA (Tamamen yeni yapı) ---

@api.post(WEBHOOK_URL_PATH)
async def telegram_webhook(request: Request) -> Response:
    """Gelen Telegram isteklerini alır ve PTB application'a işlettirir."""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error in webhook endpoint: {e}")
        return Response(status_code=500)

@api.get("/")
def health_check():
    """Heroku'nun sağlık kontrolü için basit bir endpoint."""
    return {"status": "ok"}

@api.on_event("startup")
async def on_startup():
    """Uygulama başladığında webhook'u ayarlar."""
    logger.info("Setting webhook...")
    await application.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}")
    # Handler'ları burada ekliyoruz
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("help", show_help))

@api.on_event("shutdown")
async def on_shutdown():
    """Uygulama kapandığında webhook'u kaldırır."""
    logger.info("Deleting webhook...")
    await application.bot.delete_webhook()