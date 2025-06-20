import os
import logging
import json
import base64
import time
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# --- Ortam değişkenleri ve ayar ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL")
FIREBASE_CREDS_BASE64 = os.environ.get("FIREBASE_CREDS_BASE64")
PORT = int(os.environ.get("PORT", 8000))

# --- Logger ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PMNOFO-BOT")

# --- Firebase Bağlantısı ---
if FIREBASE_CREDS_BASE64:
    creds_json = json.loads(base64.b64decode(FIREBASE_CREDS_BASE64))
    cred = credentials.Certificate(creds_json)
else:
    cred = credentials.Certificate("firebase-key.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Başlangıç Komutu ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_ref = db.collection('users').document(str(user.id))
    if not user_ref.get().exists:
        user_data = {
            'username': user.username or user.first_name,
            'score': 0,
            'total_score': 0,
            'total_pmno_coins': 0,
            'user_id': user.id
        }
        user_ref.set(user_data)

    keyboard = [
        [
            InlineKeyboardButton("🇮🇱 Defend Israel", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=israel")),
            InlineKeyboardButton("🇮🇷 Defend Iran", web_app=WebAppInfo(url=f"{WEB_APP_URL}?side=iran"))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Taraf seçin ve oyuna başlayın!\nDaha fazla bilgi için /help yazın.",
        reply_markup=reply_markup
    )

# --- Yardım Komutu ---
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕊️ Füzeleri güvercine çevir, binaları koru!\n"
        "Her yeni skorunu oyun sonunda bize gönder.\n"
        "Rekorunu kırarsan bonus coin ve puan kazanırsın!\n"
        "Komutlar:\n/score - Skorunu gör\n/leaderboard - En iyiler"
    )

# --- Skor Komutu ---
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    doc = db.collection('users').document(user_id).get()
    if not doc.exists:
        await update.message.reply_text("Henüz hiç oynamadın. /start ile başla!")
        return
    d = doc.to_dict()
    await update.message.reply_text(
        f"En Yüksek Skorun: {d.get('score',0)} 🏆\n"
        f"Toplam Skorun: {d.get('total_score',0)} ☮️\n"
        f"Toplam PMNOFO Coin: {d.get('total_pmno_coins',0)} 💰"
    )

# --- Leaderboard Komutu ---
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    docs = db.collection('users').order_by('total_score', direction=firestore.Query.DESCENDING).limit(10).stream()
    txt = "🏆 **PMNOFO Leaderboard** 🏆\n\n"
    for i, doc in enumerate(docs, 1):
        d = doc.to_dict()
        name = d.get('username') or "Anon"
        txt += f"{i}. {name} - {d.get('total_score',0)} ☮️\n"
    await update.message.reply_text(txt)

# --- WebApp Skor POST Handler ---
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.web_app_data:
        return
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user_id = str(data.get("user_id"))
        score = int(data.get("score", 0))
        if str(update.effective_user.id) != user_id:
            await update.effective_message.reply_text("Kullanıcı doğrulama hatası!")
            return
        ok = update_user_score(user_id, score)
        if ok:
            await update.effective_message.reply_text(f"Skorun kaydedildi: {score}")
        else:
            await update.effective_message.reply_text("Kayıt hatası, lütfen /start ile tekrar başla.")
    except Exception as e:
        logger.error("Skor kaydı hata: %s", e)
        await update.effective_message.reply_text("Bir hata oluştu, yöneticinize haber verin.")

# --- Skor Güncelleme (Hesaplamalar burada) ---
def update_user_score(user_id, new_score):
    try:
        ref = db.collection('users').document(user_id)
        doc = ref.get()
        if not doc.exists:
            return False
        d = doc.to_dict()
        current_max = d.get('score', 0)
        total = d.get('total_score', 0)
        bonus = 0

        # Kişisel rekor kontrolü
        broke_personal = new_score > current_max

        # Leaderboard rekoru
        leaderboard_max = 0
        for doc2 in db.collection('users').order_by('score', direction=firestore.Query.DESCENDING).limit(1).stream():
            leaderboard_max = doc2.to_dict().get('score', 0)
        broke_leaderboard = new_score > leaderboard_max

        # Skor ekle
        total += new_score
        if broke_personal:
            current_max = new_score
            bonus += new_score * 100
        if broke_leaderboard:
            bonus += new_score * 250

        total_with_bonus = total + bonus
        total_coins = total_with_bonus * 10

        ref.update({
            'score': current_max,
            'total_score': total_with_bonus,
            'total_pmno_coins': total_coins
        })
        return True
    except Exception as e:
        logger.error("update_user_score hata: %s", e)
        return False

# --- Main ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    app.run_polling() # Webhook gerekiyorsa run_polling yerine webhook fonksiyonu koyabilirsin.

if __name__ == "__main__":
    main()
