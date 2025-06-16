import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext

# --- 1. KURULUM ---

# Firebase anahtar dosyasının adını buraya yazın
# Bu dosyanın bot.py ile aynı dizinde olduğundan emin olun!
FIREBASE_KEY_FILENAME = "firebase-key.json"

# Ortam değişkenlerinden Telegram token'ını ve Web App URL'sini al
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")

# Logging ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase bağlantısını kurma
try:
    cred = credentials.Certificate(FIREBASE_KEY_FILENAME)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase connection successful.")
except Exception as e:
    logger.error(f"Could not initialize Firebase: {e}")
    # Eğer Firebase'e bağlanamazsa, botun çökmesini engelle ama çalışmaya devam etme
    db = None

# --- 2. BOT FONKSİYONLARI ---

async def start(update: Update, context: CallbackContext) -> None:
    """/start komutuna cevap verir ve oyun butonlarını gönderir."""
    if not db:
        await update.message.reply_text("Database connection error. Please contact admin.")
        return

    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))

    # Kullanıcı veritabanında yoksa, oluştur.
    if not user_ref.get().exists:
        user_data = {
            'username': user.username or user.first_name,
            'first_name': user.first_name,
            'score': 0
        }
        user_ref.set(user_data)
        logger.info(f"New user created in Firestore: {user.username}")

    keyboard = [
        [
            InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel")),
            InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran"))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Not: Ana menü resmi için GitHub Raw linki kullanıyoruz
    photo_url = "https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/assets/logo.png"
    
    await update.message.reply_photo(
        photo=photo_url,
        caption=f"Welcome, Peace Ambassador {user.first_name}!\n\n"
                "Choose a side to defend and turn rockets into doves of peace. Your mission starts now.",
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
    """Botu çalıştırır."""
    if not TELEGRAM_TOKEN or not WEB_APP_URL:
        logger.error("Missing TELEGRAM_TOKEN or WEB_APP_URL in environment variables!")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))

    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()