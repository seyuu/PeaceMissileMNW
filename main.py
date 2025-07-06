import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
import telebot
from telebot.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from collections import defaultdict
import time

# Ortam değişkenleri
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
SERVER_URL = os.environ.get("SERVER_URL")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
ANALYTICS_TOKEN = os.environ.get("ANALYTICS_TOKEN")

# Firebase config (environment variable'dan)
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
FIREBASE_MESSAGING_SENDER_ID = os.environ.get("FIREBASE_MESSAGING_SENDER_ID")
FIREBASE_APP_ID = os.environ.get("FIREBASE_APP_ID")

# Flask ve bot başlat
app = Flask(__name__)

# CORS desteği ekle
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://peacemissile-game-ui.onrender.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN ortam değişkeni eksik!")
bot = telebot.TeleBot(BOT_TOKEN)
user_last_command = defaultdict(float)
RATE_LIMIT_SECONDS = 2

# Firebase başlatma ve log
try:
    print("[LOG] Firebase başlatılıyor...")
    
    # Environment variable'dan Firebase key'i al
    firebase_creds_base64 = os.environ.get('FIREBASE_CREDS_BASE64')
    
    if firebase_creds_base64:
        # Base64'ten decode et ve JSON parse et
        import json
        import base64
        firebase_key_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
        firebase_key_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(firebase_key_dict)
    else:
        # Dosyadan oku (local development için)
        cred = credentials.Certificate("firebase-key.json")
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("[LOG] Firebase başarıyla başlatıldı.")
except Exception as e:
    print(f"[LOG] Firebase başlatılamadı: {e}")
    db = None

def check_rate_limit(user_id: str) -> bool:
    current_time = time.time()
    last_time = user_last_command.get(str(user_id), 0)
    if current_time - last_time < RATE_LIMIT_SECONDS:
        return False
    user_last_command[str(user_id)] = current_time
    return True

@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        if not check_rate_limit(message.from_user.id):
            return
        user_id = str(message.from_user.id)
        username = message.from_user.username or message.from_user.first_name or "Player"
        print(f"[LOG] /start: user_id={user_id}, username={username}")
        print(f"[LOG] /start: message.from_user.id (int) = {message.from_user.id}")
        print(f"[LOG] /start: message.from_user.id (str) = {str(message.from_user.id)}")

        if db is not None:
            try:
                ref = db.collection("users").document(user_id)
                doc = ref.get()
                if not doc.exists:
                    print(f"[LOG] Yeni kullanıcı oluşturuluyor: {user_id} - {username}")
                    ref.set({"username": username, "score": 0, "total_score": 0, "total_pmno_coins": 0})
                else:
                    print(f"[LOG] Mevcut kullanıcı: {doc.to_dict()}")
            except Exception as e:
                print(f"[LOG] Firestore kullanıcı kaydı/okuma hatası: {e}")
        else:
            print("[LOG] Firebase mevcut değil, kullanıcı verisi kaydedilmiyor")

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        webapp_url_with_user = f"{WEB_APP_URL}?user_id={user_id}"
        markup.add(KeyboardButton("🚀 Play Peace Missile!", web_app=WebAppInfo(url=webapp_url_with_user)))
        message_text = (
            "🚀🕊️☮️ <b>PEACE MISSILE</b> ☮️🕊️🚀\n\n"
            "welcome to peace missile!\n\n"
            "Turn missiles into doves and bring peace to the world!\n\n"
            "Tap the button below to start your mission.\n\n"
            "<b>Commands:</b>\n"
            "📊 /score - View your scores\n"
            "❓ /help - Get help\n"
            "🔒 /privacy - Privacy policy"
        )
        bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"[LOG] HATA (/start): {e}")

@bot.message_handler(commands=['score'])
def score_handler(message):
    try:
        user_id = str(message.from_user.id)
        print(f"[LOG] /score: user_id={user_id}")
        if db is not None:
            try:
                user_doc = db.collection("users").document(user_id).get()
                print(f"[LOG] Firestore: users/{user_id} exists={user_doc.exists}")
                if user_doc.exists:
                    user = user_doc.to_dict()
                    print(f"[LOG] Kullanıcı verisi: {user}")
                    score_message = (
                        f"🚀🕊️☮️ <b>PEACE MISSILE BOT</b> ☮️🕊️🚀\n\n"
                        f"🏆 <b>Your Score</b> 🏆\n\n"
                        f"📈 <b>High Score:</b> {user.get('score', 0) if user else 0}\n"
                        f"📊 <b>Total Score:</b> {user.get('total_score', 0) if user else 0}\n"
                        f"🪙 <b>MNW Coins:</b> {user.get('total_pmno_coins', 0) if user else 0}"
                    )
                    bot.send_message(message.chat.id, score_message, parse_mode="HTML")
                else:
                    print("[LOG] Kullanıcı dokümanı bulunamadı")
                    bot.send_message(message.chat.id, "You don't have a score yet. Play first!")
            except Exception as e:
                print(f"[LOG] Firestore kullanıcı okuma hatası: {e}")
        else:
            print("[LOG] Firebase mevcut değil, mock veri gönderiliyor")
            bot.send_message(message.chat.id, "Firebase bağlantısı yok.")
    except Exception as e:
        print(f"[LOG] HATA (/score): {e}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    help_text = (
        "🚀🕊️☮️ <b>PEACE MISSILE BOT</b> ☮️🕊️🚀\n\n"
        "🎮🕊️☮️ <b>Commands:</b> ☮️🕊️🎮\n"
        "🚀 /start - Start the game\n"
        "📊 /score - View your scores\n"
        "❓ /help - This help message\n"
        "🔒 /privacy - Privacy policy\n\n"
        "🎯 <b>How to Play:</b>\n"
        "• Convert missiles into doves\n"
        "• Earn points for peace\n"
        "• Beat your high score!\n\n"
        "💰 <b>MNW Coin System:</b>\n"
        "• Base: 1 coin per 10 points\n"
        "• High Score Bonus: 10x base coins\n"
        "• Leader Bonus: 25x base coins\n\n"
        "📈 <b>Example:</b> 100 points = 10 base coins\n"
        "If new high score: +100 bonus\n"
        "If leader: +250 bonus\n"
        "Total: 360 coins!\n\n"
        "🔒 <b>Privacy:</b>\n"
        "Only your game scores are saved.\n"
        "Your personal data is not shared."
    )
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

@bot.message_handler(commands=['privacy'])
def privacy_handler(message):
    privacy_text = (
        "🚀🕊️☮️ <b>PEACE MISSILE BOT</b> ☮️🕊️🚀\n\n"
        "🔒 <b>Privacy Policy</b> 🔒\n\n"
        "✅ Only your game scores are saved\n"
        "✅ Your personal data is not shared\n"
        "✅ Your data is stored securely\n"
        "✅ Not shared with third parties\n\n"
        "For more info: /help"
    )
    bot.send_message(message.chat.id, privacy_text, parse_mode="HTML")

@bot.message_handler(commands=['leaderboard'])
def leaderboard_handler(message):
    try:
        if db is not None:
            try:
                # Top 10 oyuncuyu al
                users_ref = db.collection("users").order_by("total_score", direction="DESCENDING").limit(10)
                users = users_ref.stream()
                
                leaderboard_text = "🚀🕊️☮️ <b>PEACE MISSILE LEADERBOARD</b> ☮️🕊️🚀\n\n"
                leaderboard_text += "🏆 <b>Top 10 Players</b> 🏆\n\n"
                
                for i, user in enumerate(users, 1):
                    user_data = user.to_dict()
                    if user_data:
                        username = user_data.get('username', 'Anonymous')
                        total_score = user_data.get('total_score', 0)
                        score = user_data.get('score', 0)
                        coins = user_data.get('total_pmno_coins', 0)
                    
                    # Emoji'ler
                    if i == 1:
                        medal = "🥇"
                    elif i == 2:
                        medal = "🥈"
                    elif i == 3:
                        medal = "🥉"
                    else:
                        medal = f"{i}."
                    
                    leaderboard_text += f"{medal} <b>{username}</b>\n"
                    leaderboard_text += f"   📊 Total: {total_score:,} | 🏅 High: {score:,} | 🪙 Coins: {coins:,}\n\n"
                
                bot.send_message(message.chat.id, leaderboard_text, parse_mode="HTML")
                
            except Exception as e:
                print(f"[LOG] Leaderboard Firestore hatası: {e}")
                bot.send_message(message.chat.id, "Leaderboard yüklenirken hata oluştu.")
        else:
            bot.send_message(message.chat.id, "Leaderboard şu anda kullanılamıyor.")
            
    except Exception as e:
        print(f"[LOG] Leaderboard handler hatası: {e}")
        bot.send_message(message.chat.id, "Bir hata oluştu.")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "bot": "running"})

# Bot config endpoint (frontend için)
@app.route('/get_bot_config', methods=['GET'])
def get_bot_config():
    """Frontend için bot config'ini döndür"""
    return jsonify({
        "bot_username": BOT_USERNAME,
        "access_token": ANALYTICS_TOKEN
    })

# Firebase config endpoint (frontend için)
@app.route('/get_firebase_config', methods=['GET'])
def get_firebase_config():
    """Frontend için Firebase config'ini döndür"""
    return jsonify({
        "apiKey": FIREBASE_API_KEY,
        "authDomain": FIREBASE_AUTH_DOMAIN,
        "projectId": FIREBASE_PROJECT_ID,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": FIREBASE_MESSAGING_SENDER_ID,
        "appId": FIREBASE_APP_ID
    })

# Skor kaydetme endpoint'i
@app.route('/save_score', methods=['POST'])
def save_score():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        score = data.get('score')
        
        if not user_id or not score:
            return jsonify({"error": "Missing user_id or score"}), 400
        
        print(f"[LOG] Skor kaydetme isteği: user_id={user_id}, score={score}")
        
        if db is not None:
            try:
                user_ref = db.collection("users").document(str(user_id))
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    if user_data:
                        current_score = user_data.get('score', 0)
                        current_total_score = user_data.get('total_score', 0)
                        current_coins = user_data.get('total_pmno_coins', 0)
                    else:
                        current_score = 0
                        current_total_score = 0
                        current_coins = 0
                    
                    # Yeni skor daha yüksekse güncelle
                    new_score = max(current_score, score)
                    new_total_score = current_total_score + score
                    
                    # Temel coin hesaplaması
                    base_coins = score // 10
                    coins_earned = base_coins
                    bonus_message = ""
                    
                    # High score bonus (10x base coins)
                    if score > current_score:
                        high_score_bonus = base_coins * 10
                        coins_earned += high_score_bonus
                        bonus_message += f"🏆 High Score Bonus: +{high_score_bonus} coins\n"
                    
                    # Leader bonus kontrolü (en yüksek skorlu kullanıcı)
                    try:
                        # Tüm kullanıcıları al ve en yüksek skoru bul
                        all_users = db.collection("users").stream()
                        highest_score = 0
                        for user in all_users:
                            user_data = user.to_dict()
                            if user_data.get('score', 0) > highest_score:
                                highest_score = user_data.get('score', 0)
                        
                        # Eğer bu kullanıcı en yüksek skora sahipse leader bonus
                        if score >= highest_score and score > current_score:
                            leader_bonus = base_coins * 25
                            coins_earned += leader_bonus
                            bonus_message += f"👑 Leader Bonus: +{leader_bonus} coins\n"
                    except Exception as e:
                        print(f"[LOG] Leader bonus hesaplama hatası: {e}")
                    
                    new_total_coins = current_coins + coins_earned
                    
                    user_ref.update({
                        'score': new_score,
                        'total_score': new_total_score,
                        'total_pmno_coins': new_total_coins
                    })
                    
                    print(f"[LOG] Skor başarıyla kaydedildi: user_id={user_id}, new_score={new_score}, new_total_score={new_total_score}, new_total_coins={new_total_coins}")
                    
                    return jsonify({
                        "success": True,
                        "new_score": new_score,
                        "new_total_score": new_total_score,
                        "new_total_coins": new_total_coins,
                        "coins_earned": coins_earned,
                        "bonus_message": bonus_message,
                        "base_coins": base_coins
                    })
                else:
                    print(f"[LOG] Kullanıcı bulunamadı: {user_id}")
                    return jsonify({"error": "User not found"}), 404
                    
            except Exception as e:
                print(f"[LOG] Firestore skor kaydetme hatası: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            print("[LOG] Firebase bağlantısı yok")
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"[LOG] Skor kaydetme endpoint hatası: {e}")
        return jsonify({"error": "Server error"}), 500

@app.route('/webhook-7f3a2b1c', methods=['POST'])
def telegram_webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    if update:
        bot.process_new_updates([update])
    return '', 200

if __name__ == "__main__":
    print("[LOG] Bot başlatılıyor...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)