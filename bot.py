import os
import logging
import firebase_admin
import base64
import json
from firebase_admin import credentials, firestore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters # MessageHandler ve filters ekledik

# --- 1. GÜVENLİ KURULUM ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL") # Bu, Render.com'daki oyun arayüzümüzün adresi
FIREBASE_CREDS_BASE64 = os.environ.get("FIREBASE_CREDS_BASE64")

PORT = int(os.environ.get("PORT", 10000)) # Render.com genellikle 10000 portunu bekler 
# Render.com servinizin genel URL'si. Bu genellikle Render tarafından otomatik set edilen
# "RENDER_EXTERNAL_HOSTNAME" gibi bir ortam değişkeninden alınabilir.
# Eğer bu değişken yoksa, Render paneli üzerinden URL'i alıp elle tanımlamanız gerekecek.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_BASE_URL = os.environ.get("RENDER_EXTERNAL_HOSTNAME") 
if not WEBHOOK_BASE_URL:
    logger.warning("RENDER_EXTERNAL_HOSTNAME environment variable not found. Please ensure WEBHOOK_BASE_URL is set correctly in Render.com environment.")
    # Fallback olarak WEB_APP_URL'i kullanabiliriz ama bu ideal değil
    WEBHOOK_BASE_URL = WEB_APP_URL.split('?')[0] # Parametreleri kaldır

# Telegram botunuzun webhook path'i için güvenli bir yol oluşturun
# Bu, Telegram'ın botunuza mesaj göndermek için kullanacağı URL yolu olacak.
# Genellikle Telegram tokenı kullanılır.
WEBHOOK_URL_PATH = f"/{TELEGRAM_TOKEN}"

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

# --- WEB APP'TEN GELEN VERİLERİ İŞLEME FONKSİYONU ---
async def web_app_data_handler(update: Update, context: CallbackContext) -> None:
    """Web App'ten gelen verileri (örn. oyun skoru) işler."""
    if not update.effective_message or not update.effective_message.web_app_data:
        logger.warning("No web app data received or effective message is missing.")
        return

    data = update.effective_message.web_app_data.data
    logger.info(f"Received Web App Data: {data}")

    try:
        payload = json.loads(data)
        user_id = payload.get("user_id")
        final_score = payload.get("final_score")

        if not user_id or final_score is None:
            logger.error(f"Invalid payload from Web App: {payload}")
            await update.effective_message.reply_text("Oyun skoru alınamadı, lütfen tekrar deneyin.")
            return

        final_score = int(final_score)
        
        # Kullanıcının Telegram ID'si (update.effective_user.id) ile Web App'ten gelen user_id'yi karşılaştırabiliriz
        # Güvenlik için bu önemli. Eğer oyun içinde user_id'yi kendiniz set ediyorsanız,
        # burada update.effective_user.id'yi kullanmanız daha güvenlidir.
        telegram_user_id = str(update.effective_user.id)
        if telegram_user_id != str(user_id):
            logger.warning(f"User ID mismatch: Telegram ({telegram_user_id}) vs Web App ({user_id})")
            await update.effective_message.reply_text("Kullanıcı ID doğrulaması başarısız oldu. Güvenlik hatası.")
            return

        success = await update_user_score(telegram_user_id, final_score)
        
        if success:
            await update.effective_message.reply_text(
                f"Tebrikler! Yeni skorunuz {final_score} kaydedildi.\n"
                f"Güncel istatistiklerinizi görmek için /score yazın."
            )
        else:
            await update.effective_message.reply_text("Skorunuz kaydedilirken bir sorun oluştu. Lütfen tekrar deneyin.")

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from Web App Data: {data}")
        await update.effective_message.reply_text("Oyun verisi okunamadı.")
    except ValueError:
        logger.error(f"Invalid score value from Web App: {final_score}")
        await update.effective_message.reply_text("Geçersiz skor değeri alındı.")
    except Exception as e:
        logger.error(f"Unhandled error in web_app_data_handler: {e}")
        await update.effective_message.reply_text("Bir hata oluştu, lütfen yöneticinizle iletişime geçin.")


# --- 2. BOT FONKSİYONLARI (önceki haliyle aynı, sadece kopyalayıp yapıştırın) ---

async def start(update: Update, context: CallbackContext) -> None:
    """/start komutuna cevap verir ve taraf seçimi butonlarını gönderir."""
    if not db:
        await update.message.reply_text("Database connection error. Please contact admin.")
        return

    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))

    # Kullanıcının belgesini kontrol et
    user_doc = user_ref.get()

    if not user_doc.exists: # Kullanıcı yoksa, yeni belge oluştur
        user_data = {
            'username': user.username or user.first_name,
            'first_name': user.first_name,
            'score': 0, # En yüksek tekil oyun skoru (mevcut bu)
            'total_score': 0, # Yeni: Tüm oyunların toplam skoru
            'total_pmno_coins': 0, # Yeni: Toplam PMNOFO Coin
            'user_id': user.id
        }
        user_ref.set(user_data)
        logger.info(f"New user created in Firestore: {user.username or user.first_name} with initial scores.")
    else:
        # Kullanıcı zaten varsa, mevcut verilerini güncelleme veya kontrol etme
        existing_data = user_doc.to_dict()
        update_needed = False
        if 'total_score' not in existing_data:
            existing_data['total_score'] = 0
            update_needed = True
        if 'total_pmno_coins' not in existing_data:
            existing_data['total_pmno_coins'] = 0
            update_needed = True
        if 'score' not in existing_data: 
            existing_data['score'] = 0
            update_needed = True

        if update_needed:
            user_ref.update(existing_data)
            logger.info(f"Existing user {user.username or user.first_name} updated with missing score/coin fields.")


    # --- Taraf seçimi butonları burada ---
    keyboard = [
        [
            InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel")),
            InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran"))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo_url = "https://raw.githubusercontent.com/seyuu/PeaceMissileBot/main/public/assets/logo.png"
    
    await update.message.reply_photo(
        photo=photo_url,
        caption=f"Welcome, Peace Ambassador {user.first_name}!\n\n"
                "The skies are filled with conflict. Choose a side to defend and turn rockets into doves of peace. Your mission starts now.\n\n"
                "Oyunun amacı ve coin kazanma hakkında bilgi almak için /help komutunu kullanın.",
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
        user_data = user_doc.to_dict()
        current_highest_score = user_data.get('score', 0) 
        total_accumulated_score = user_data.get('total_score', 0) 
        total_pmno_coins = user_data.get('total_pmno_coins', 0) 

        await update.message.reply_text(
            f"Your stats, Peace Ambassador:\n"
            f"Current Highest Game Score: {current_highest_score} 🏆\n"
            f"Total Accumulated Score: {total_accumulated_score} ☮️\n"
            f"Total PMNOFO Coins: {total_pmno_coins} 💰"
        )
    else:
        await update.message.reply_text("You haven't played yet! Use /start to begin.")

async def update_user_score(user_id: str, new_game_score: int):
    """Web App'ten gelen skorları işler ve Firebase'i günceller."""
    if not db:
        logger.error("Database connection error in update_user_score.")
        return False 

    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        
        current_highest_score = user_data.get('score', 0) 
        total_accumulated_score = user_data.get('total_score', 0) 
        total_pmno_coins = user_data.get('total_pmno_coins', 0) 

        # 1. Her oyun için puanları toplam puana ekle
        total_accumulated_score += new_game_score

        # 2. Her oyun için puan kadar coin ekle
        total_pmno_coins += new_game_score

        # 3. Yeni rekor kırıldıysa bonus coin ekle
        if new_game_score > current_highest_score:
            coin_bonus = new_game_score * 100
            total_pmno_coins += coin_bonus
            current_highest_score = new_game_score # En yüksek skoru güncelle

        # Firebase'i güncelle
        user_ref.update({
            'score': current_highest_score,        # Tekil oyun en yüksek skoru
            'total_score': total_accumulated_score, # Tüm oyunların toplam skoru
            'total_pmno_coins': total_pmno_coins   # Toplam PMNOFO Coin
        })
        logger.info(f"User {user_id} scores updated. New highest: {current_highest_score}, Total Score: {total_accumulated_score}, Total Coins: {total_pmno_coins}")
        return True 
    else:
        logger.warning(f"User {user_id} not found when trying to update score. User must /start first.")
        return False 


async def leaderboard(update: Update, context: CallbackContext) -> None:
    """Genel liderlik tablosunu gösterir."""
    if not db:
        await update.message.reply_text("Database connection error.")
        return

    users_ref = db.collection('users').order_by('total_score', direction=firestore.Query.DESCENDING).limit(10)

    docs = users_ref.stream()

    leaderboard_text = "🏆 **Global Peace Leaderboard (Toplam Puan)** 🏆\n\n"
    position = 1
    for doc in docs:
        user_data = doc.to_dict()
        username = user_data.get('username') or user_data.get('first_name', 'Bilinmeyen Kullanıcı')
        total_score = user_data.get('total_score', 0)
        leaderboard_text += f"{position}. {username} - {total_score} ☮️\n"
        position += 1
    
    if position == 1: 
        leaderboard_text += "Henüz kimse oynamamış! İlk sen ol!"

    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

async def show_help(update: Update, context: CallbackContext) -> None:
    """Oyunun amacını ve kurallarını açıklar."""
    help_text = (
        "🕊️ **Barış Füzesi Botuna Hoş Geldiniz!** 🕊️\n\n"
        "Bu oyunda amacınız, gökyüzündeki füzeleri barış güvercinlerine dönüştürerek "
        "dünyaya barış getirmek. Her başarılı dönüşüm size puan kazandırır.\n\n"
        "💰 **PMNOFO Coini Nasıl Kazanılır?**\n"
        "Her oynadığınız oyunda kazandığınız puan kadar PMNOFO Coini hesabınıza eklenir. "
        "Ayrıca, eğer yeni bir kişisel rekor kırarsanız, kırdığınız rekor puanının "
        "**100 katı** kadar devasa bir bonus PMNOFO Coini kazanırsınız! Unutmayın, rekorlar kırın, daha çok coin toplayın!\n\n"
        "📊 **Genel Liderlik Tablosu**\n"
        "En yüksek toplam puana veya en çok PMNOFO Coini'ne sahip oyuncuları görmek için "
        "`/leaderboard` komutunu kullanın. Adınızı zirveye taşıyın!\n\n"
        "📢 **Unutmayın:** Her bir puanınız, dünyaya bir adım daha fazla barış getirme çabanızı temsil ediyor. "
        "Haydi, göreve başlayın!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


# --- 3. BOTU BAŞLATMA ---
def main() -> None:
    if not all([TELEGRAM_TOKEN, WEB_APP_URL, WEBHOOK_BASE_URL, db]):
        logger.error("CRITICAL: Missing environment variables or DB connection failed. Bot will not start.")
        if not TELEGRAM_TOKEN: logger.error("TELEGRAM_TOKEN missing.")
        if not WEB_APP_URL: logger.error("WEB_APP_URL missing.")
        if not WEBHOOK_BASE_URL: logger.error("WEBHOOK_BASE_URL missing.")
        if not db: logger.error("Firebase DB connection failed.")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(CommandHandler("leaderboard", leaderboard)) 
    application.add_handler(CommandHandler("help", show_help)) 
    
    # Web App'ten gelen verileri işlemek için yeni handler
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    
    # Telegram bot webhook'unu başlat
    application.run_webhook(
        listen="0.0.0.0", 
        port=PORT,
        url_path=WEBHOOK_URL_PATH,
        webhook_url=f"https://{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}" # HTTPS kullanıyoruz
    )
    logger.info(f"Bot running with webhook on port {PORT}, URL: https://{WEBHOOK_BASE_URL}{WEBHOOK_URL_PATH}")

if __name__ == '__main__':
    main()