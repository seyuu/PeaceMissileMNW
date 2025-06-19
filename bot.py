import os
import logging
import json
import firebase_admin
from firebase_admin import credentials, firestore
import base64
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# --- 1. Temel Kurulum ve Ortam Değişkenleri ---
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

# --- 3. Telegram Bot Application'ı Oluşturma ve Handler'ları Ekleme ---
# Application'ı burada, global kapsamda oluşturuyoruz.
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Tüm komut ve mesaj işleyicilerini (handler) buraya ekliyoruz.
async def post_init(app: Application):
    """Webhook'u ayarlar."""
    logger.info("Setting webhook...")
    await app.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}")

# Bot fonksiyonlarınız (start, score, web_app_data_handler vb.) buraya gelecek...
# Önceki kodunuzdan kopyalayıp yapıştırabilirsiniz, içeriklerinde bir değişiklik yok.
# Sadece `CallbackContext` yerine `ContextTypes.DEFAULT_TYPE` kullandığınızdan emin olun.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db: await update.message.reply_text("Database error."); return
    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))
    if not user_ref.get().exists:
        user_ref.set({'username': user.username or user.first_name, 'first_name': user.first_name, 'score': 0, 'total_score': 0, 'total_pmno_coins': 0, 'user_id': user.id})
    keyboard = [[InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel")), InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran"))]]
    await update.message.reply_photo(photo="https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/public/assets/logo.png", caption=f"Welcome, Peace Ambassador {user.first_name}!", reply_markup=InlineKeyboardMarkup(keyboard))

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db: await update.message.reply_text("Database error."); return
    user_doc = db.collection('users').document(str(update.message.from_user.id)).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        await update.message.reply_text(f"Highest Score: {data.get('score', 0)}\nTotal Score: {data.get('total_score', 0)}\nCoins: {data.get('total_pmno_coins', 0)}")
    else:
        await update.message.reply_text("No score yet.")
        
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data_str = update.effective_message.web_app_data.data
    logger.info(f"Received Web App Data: {data_str}")
    try:
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
            new_total_score = user_data.get('total_score', 0) + game_score
            new_coins = user_data.get('total_pmno_coins', 0) + game_score
            new_high_score = user_data.get('score', 0)
            if game_score > new_high_score:
                new_high_score = game_score
                new_coins += game_score * 100
            
            user_ref.update({
                'score': new_high_score,
                'total_score': new_total_score,
                'total_pmno_coins': new_coins
            })
            await update.message.reply_text(f"Score {game_score} saved! Your new high score is {new_high_score}.")
        else:
            logger.warning(f"User {user_id} not found in DB.")

    except Exception as e:
        logger.error(f"Error processing web app data: {e}")

# Handler'ları application'a ekle
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("score", score))
# Diğer komut handler'larınız (leaderboard, help vb.) buraya eklenebilir
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

# Webhook'u ayarlamak için post_init fonksiyonunu kullan
application.post_init = post_init

# --- 4. FastAPI Sunucusunu Kurma ---
api = FastAPI()

@api.post(WEBHOOK_URL_PATH)
async def telegram_webhook(request: Request) -> Response:
    """Gelen Telegram güncellemelerini PTB application'a yönlendirir."""
    await application.update_queue.put(Update.de_json(await request.json(), application.bot))
    return Response(status_code=200)

@api.get("/")
def health_check():
    """Heroku'nun sağlık kontrolü için."""
    return {"status": "ok, bot is running"}

# --- 5. Uygulamanın Başlangıç ve Bitiş Olayları (Lifespan) ---

@api.on_event("startup")
async def on_startup():
    """Uygulama başladığında webhook'u ayarlar."""
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}")
    logger.info("Application startup complete and webhook is set.")


@api.on_event("shutdown")
async def on_shutdown():
    """Uygulama kapandığında webhook'u kaldırır ve botu durdurur."""
    logger.info("Application shutdown, deleting webhook...")
    await application.stop()
    await application.bot.delete_webhook()
    await application.shutdown()