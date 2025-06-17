import os
import logging
import firebase_admin
import base64
import json
from firebase_admin import credentials, firestore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext

# --- 1. GÜVENLİ KURULUM ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL") # Bu, Render.com'daki oyun arayüzümüzün adresi
FIREBASE_CREDS_BASE64 = os.environ.get("FIREBASE_CREDS_BASE64")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = None
try:
    if FIREBASE_CREDS_BASE64:
        decoded_creds = base64.b64decode(FIREBASE_CREDS_BASE64)
        cred_json = json.loads(decoded_creds)
        cred = credentials.Certificate(cred_json)
        logger.info("Firebase credentials loaded from environment variable.")
    else:
        cred = credentials.Certificate("firebase-key.json")
        logger.info("Firebase credentials loaded from local file.")
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase connection successful.")
except Exception as e:
    logger.error(f"FATAL: Could not initialize Firebase: {e}")

# --- 2. BOT FONKSİYONLARI ---

async def start(update: Update, context: CallbackContext) -> None:
    """/start komutuna cevap verir ve taraf seçimi butonlarını gönderir."""
    if not db:
        await update.message.reply_text("Database connection error. Please contact admin.")
        return

    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))

    if not user_ref.get().exists:
        user_data = {
            'username': user.username or user.first_name,
            'first_name': user.first_name,
            'score': 0,
            'user_id': user.id
        }
        user_ref.set(user_data)
        logger.info(f"New user created in Firestore: {user.username or user.first_name}")

    # --- DÜZELTME: Taraf seçimi butonları burada ---
    keyboard = [
        [
            InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel")),
            InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran"))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo_url = "https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/assets/logo.png"
    
    await update.message.reply_photo(
        photo=photo_url,
        caption=f"Welcome, Peace Ambassador {user.first_name}!\n\n"
                "The skies are filled with conflict. Choose a side to defend and turn rockets into doves of peace. Your mission starts now.",
        reply_markup=reply_markup
    )

async def score(update: Update, context: CallbackContext) -> None:
    """Kullanıcının skorunu gösterir."""
    if not db:
        await update.message.reply_text("Database connection error.")
        return

    user_id = str(update.message.from_user.id)
    user_doc = db.collection('users').document(user_id).get()

    if user_doc.exists:
        current_score = user_doc.to_dict().get('score', 0)
        await update.message.reply_text(f"Your total Peace Score is: {current_score} ☮️")
    else:
        await update.message.reply_text("You haven't played yet! Use /start to begin.")

# --- 3. BOTU BAŞLATMA ---
def main() -> None:
    if not all([TELEGRAM_TOKEN, WEB_APP_URL, db]):
        logger.error("CRITICAL: Missing environment variables or DB connection failed. Bot will not start.")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))

    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()