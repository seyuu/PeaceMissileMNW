import os
import logging
import json
import firebase_admin
import base64
from fastapi import FastAPI, Request, Response
import telegram  # Bu import önemli
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

# --- 1. Temel Kurulum ve Ortam Değişkenleri ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
FIREBASE_CREDS_BASE64 = os.environ.get("FIREBASE_CREDS_BASE64")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL")
WEBHOOK_URL_PATH = f"/{TELEGRAM_TOKEN}"

# --- 2. Firebase Bağlantısı ---
db = None
try:
    if FIREBASE_CREDS_BASE64:
        decoded_creds = base64.b64decode(FIREBASE_CREDS_BASE64)
        cred_json = json.loads(decoded_creds)
        cred = credentials.Certificate(cred_json)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase connection successful.")
    else:
        logger.error("FATAL: FIREBASE_CREDS_BASE64 environment variable not set.")
except Exception as e:
    logger.error(f"FATAL: Could not initialize Firebase: {e}")

# --- 3. Telegram Bot Application'ı Oluşturma ---
# Kütüphane versiyonuna göre Application'ı doğru şekilde oluştur
# Bu, WebApp verisinin doğru işlenmesi için kritik
try:
    ptb_version_tuple = tuple(map(int, telegram.__version__.split('.')))
    if ptb_version_tuple >= (21, 0):
        application = Application.builder().token(TELEGRAM_TOKEN).arbitrary_callback_data(True).build()
    else:
        # Eski versiyonlar için fallback
        application = Application.builder().token(TELEGRAM_TOKEN).build()
except Exception:
    # Versiyon okunamaması gibi nadir durumlar için
    application = Application.builder().token(TELEGRAM_TOKEN).build()


# --- 4. Bot Fonksiyonları (Komut ve Mesaj İşleyicileri) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db:
        await update.message.reply_text("Database connection error. Please contact admin.")
        return
    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))
    if not user_ref.get().exists:
        user_ref.set({'username': user.username or user.first_name, 'first_name': user.first_name, 'score': 0, 'total_score': 0, 'total_pmno_coins': 0, 'user_id': user.id})
    
    keyboard = [[
        InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel")),
        InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran"))
    ]]
    await update.message.reply_photo(
        photo="https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/public/assets/logo.png",
        caption=f"Welcome, Peace Ambassador {user.first_name}!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db:
        await update.message.reply_text("Database error.")
        return
    user_doc = db.collection('users').document(str(update.message.from_user.id)).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        await update.message.reply_text(f"Highest Score: {data.get('score', 0)}\nTotal Score: {data.get('total_score', 0)}\nCoins: {data.get('total_pmno_coins', 0)}")
    else:
        await update.message.reply_text("No score yet. Use /start to play.")

# bot.py'deki web_app_data_handler fonksiyonunun NİHAİ ve DOĞRU hali

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Web App data received, processing...")

    try:
        data_str = update.effective_message.web_app_data.data
        payload = json.loads(data_str)
        
        user_id = str(payload.get("user_id"))
        game_score = int(payload.get("score"))

        if not user_id or game_score is None:
            logger.error(f"Incomplete data from WebApp: {payload}")
            return

        # Güvenlik kontrolü
        if str(update.effective_user.id) != user_id:
            logger.warning(f"User ID mismatch! TG: {update.effective_user.id}, WA: {user_id}")
            return

        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()

        if doc.exists:
            user_data = doc.to_dict()
            
            # Mevcut değerleri al
            current_high_score = user_data.get('score', 0)
            total_score = user_data.get('total_score', 0)
            total_coins = user_data.get('total_pmno_coins', 0)

            # Yeni değerleri hesapla
            total_score += game_score
            total_coins += game_score # Her oyun için standart coin

            is_new_record = False
            if game_score > current_high_score:
                is_new_record = True
                current_high_score = game_score  # Rekoru güncelle
                total_coins += game_score * 100 # Rekor bonusunu ekle
            
            # Veritabanını güncelle
            user_ref.update({
                'score': current_high_score,
                'total_score': total_score,
                'total_pmno_coins': total_coins
            })
            
            logger.info(f"User {user_id} score updated successfully. New high score: {current_high_score}")

            # Kullanıcıyı bilgilendir
            message = f"Tebrikler! {game_score} puanlık oyununuz kaydedildi."
            if is_new_record:
                message += f"\n\n🏆 YENİ REKOR: {current_high_score}! 🏆\nBonus olarak {game_score * 100} coin kazandınız!"
            
            await update.effective_message.reply_text(message)

        else:
            logger.warning(f"User {user_id} not found in DB. Should have been created by /start.")

    except Exception as e:
        logger.error(f"CRITICAL ERROR in web_app_data_handler: {e}", exc_info=True)
        await update.effective_message.reply_text("Skorunuz işlenirken bir hata oluştu.")

# --- 5. Handler'ları Application'a Ekleme ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("score", score))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

# --- 6. FastAPI Sunucusunu ve Webhook'u Ayarlama ---
api = FastAPI()

@api.post(WEBHOOK_URL_PATH)
async def telegram_webhook(request: Request) -> Response:
    """Gelen Telegram güncellemelerini PTB application'a yönlendirir."""
    try:
        await application.update_queue.put(Update.de_json(await request.json(), application.bot))
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error in webhook endpoint: {e}")
        return Response(status_code=500)

@api.get("/")
def health_check():
    """Heroku'nun sağlık kontrolü için."""
    return {"status": "ok, bot is running"}

@api.on_event("startup")
async def on_startup():
    """Uygulama başladığında webhook'u ayarlar."""
    await application.initialize()
    # Webhook'u sadece bir kez ve uygulama tamamen hazır olduğunda ayarla
    await application.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}", allowed_updates=Update.ALL_TYPES)
    await application.start()
    logger.info("Application startup complete and webhook is set.")

@api.on_event("shutdown")
async def on_shutdown():
    """Uygulama kapandığında botu ve webhook'u temiz bir şekilde durdurur."""
    logger.info("Application shutdown...")
    await application.stop()
    await application.bot.delete_webhook()
    await application.shutdown()