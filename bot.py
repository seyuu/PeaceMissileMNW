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
        
# bot.py'deki bu fonksiyonu A'dan Z'ye şununla değiştirin.
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """[DEBUG] Web App'ten gelen verileri işler."""
    logger.info("[DEBUG] Adım 0: web_app_data_handler tetiklendi.")
    
    # 1. Verinin gelip gelmediğini logla
    if not update.effective_message or not update.effective_message.web_app_data:
        logger.error("[DEBUG] Adım 1 BAŞARISIZ: Etkin mesaj veya web_app_data bulunamadı.")
        return

    data_str = update.effective_message.web_app_data.data
    logger.info(f"[DEBUG] Adım 1 BAŞARILI: Ham veri alındı -> {data_str}")

    try:
        # 2. JSON'a çevirmeyi dene
        logger.info("[DEBUG] Adım 2: JSON'a çevirme deneniyor...")
        payload = json.loads(data_str)
        logger.info(f"[DEBUG] Adım 2 BAŞARILI: JSON'a çevrildi -> {payload}")

        # 3. Gerekli alanları (user_id ve score) almayı dene
        logger.info("[DEBUG] Adım 3: 'user_id' ve 'score' alanları alınıyor...")
        user_id = payload.get("user_id")
        game_score_str = payload.get("score") # Değişken adını değiştirdim
        logger.info(f"[DEBUG] Adım 3 SONUÇ: user_id={user_id}, game_score_str={game_score_str}")

        if not user_id or game_score_str is None:
            logger.error(f"[DEBUG] Adım 3 BAŞARISIZ: user_id veya score alanlarından biri eksik (None).")
            return
        
        # 4. Skoru integer'a çevirmeyi dene
        logger.info("[DEBUG] Adım 4: Skor integer'a çevriliyor...")
        game_score = int(game_score_str)
        logger.info(f"[DEBUG] Adım 4 BAŞARILI: Skor integer'a çevrildi -> {game_score}")
        
        # 5. Firebase'e erişmeyi dene
        logger.info(f"[DEBUG] Adım 5: Firebase'e erişiliyor. User ID: {user_id}")
        user_ref = db.collection('users').document(str(user_id))
        doc = user_ref.get()
        logger.info(f"[DEBUG] Adım 5 BAŞARILI: Firebase'den belge alındı. Belge var mı? -> {doc.exists}")
        
        if doc.exists:
            user_data = doc.to_dict()
            logger.info(f"[DEBUG] Adım 6: Mevcut veriler okundu -> {user_data}")
            
            # 7. Yeni skorları hesapla
            current_high_score = user_data.get('score', 0)
            new_total_score = user_data.get('total_score', 0) + game_score
            new_coins = user_data.get('total_pmno_coins', 0) + game_score
            is_new_high_score = False

            if game_score > current_high_score:
                is_new_high_score = True
                new_high_score = game_score
                new_coins += game_score * 100
                logger.info(f"[DEBUG] Adım 7: YENİ REKOR! Eski: {current_high_score}, Yeni: {new_high_score}")
            else:
                new_high_score = current_high_score
                logger.info(f"[DEBUG] Adım 7: Rekor kırılamadı. Mevcut rekor: {current_high_score}")

            update_data = {
                'score': new_high_score,
                'total_score': new_total_score,
                'total_pmno_coins': new_coins
            }
            logger.info(f"[DEBUG] Adım 8: Veritabanı güncellenecek veri -> {update_data}")
            
            # 9. Veritabanına yaz
            user_ref.update(update_data)
            logger.info("[DEBUG] Adım 9 BAŞARILI: Veritabanı güncellendi.")
            
            # 10. Kullanıcıya mesaj gönder
            await update.effective_message.reply_text(f"Skorunuz ({game_score}) başarıyla kaydedildi!")

        else:
            logger.warning(f"[DEBUG] Adım 6 BAŞARISIZ: Kullanıcı {user_id} veritabanında bulunamadı. Yeni kullanıcı oluşturulacak.")
            # İsteğe bağlı: Kullanıcı yoksa burada da oluşturabilirsiniz.
            # Şimdilik sadece uyarı verelim.

    except Exception as e:
        logger.error(f"[DEBUG] KRİTİK HATA: web_app_data_handler içinde bir hata oluştu: {e}", exc_info=True)
        
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