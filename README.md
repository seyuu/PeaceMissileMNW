# Peace Missile Bot 🚀

Telegram WebApp oyunu - Füzeleri güvercinlere çevirerek barış getirin!

## 🎮 Özellikler

- **Telegram WebApp**: Doğrudan Telegram içinde oynanabilir
- **Skor Sistemi**: Yüksek skorlar ve toplam puanlar
- **PMNOFO Coins**: Oyun içi para sistemi
- **Leaderboard**: En iyi oyuncular
- **Güvenli**: Telegram initData doğrulaması

## 🚀 Deployment

### Google Cloud Run (Bot Backend)

1. **Ortam Değişkenleri**:
   ```bash
   TELEGRAM_TOKEN=your_bot_token
   WEB_APP_URL=https://your-game-url.onrender.com
   SERVER_URL=https://your-bot-url.run.app
   FIREBASE_CREDS_BASE64=your_base64_firebase_creds
   ```

2. **Deploy**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/peacebot
   gcloud run deploy peacebot --image gcr.io/PROJECT_ID/peacebot --platform managed --region europe-central2 --allow-unauthenticated
   ```

### Render (Game Frontend)

1. **Static Site** oluşturun
2. **Source**: GitHub repo
3. **Publish Directory**: `public`
4. **Build Command**: (boş bırakın)

## 📋 Komutlar

- `/start` - Oyunu başlat
- `/score` - Skorlarınızı görüntüle
- `/help` - Yardım
- `/privacy` - Gizlilik politikası

## 🔒 Güvenlik

- Telegram initData doğrulaması
- Rate limiting (1 saniye/komut)
- Firebase güvenli bağlantı
- Sadece gerekli veriler kaydedilir

## 📊 Monitoring

- Health check: `/health`
- Status endpoint: `/`
- Webhook endpoint: `/{BOT_TOKEN}`

## 🛠️ Teknolojiler

- **Backend**: Python, Flask, pyTelegramBotAPI
- **Database**: Firebase Firestore
- **Frontend**: HTML5, JavaScript, Phaser.js
- **Deployment**: Google Cloud Run, Render

## 📝 Lisans

MIT License 