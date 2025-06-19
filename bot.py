import json
import logging
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def update_user_score(user_id: str, score: int) -> bool:
    """
    Kullanıcının skorunu günceller.
    Gerçek uygulamada burada veritabanı işlemleri yapılmalıdır.
    Şimdilik örnek olarak True döndürülüyor.
    """
    # TODO: Burada skor güncelleme işlemini gerçekleştirin.
    # Örneğin: veritabanına kaydet
    logger.info(f"[DEBUG] update_user_score çağrıldı: user_id={user_id}, score={score}")
    return True

# bot.py'deki bu fonksiyonu A'dan Z'ye şununla değiştirin.
async def web_app_data_handler(update: Update, context: CallbackContext) -> None:
    """[DEBUG] Web App'ten gelen verileri işler."""
    
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
        final_score_str = payload.get("score")
        logger.info(f"[DEBUG] Adım 3 SONUÇ: user_id={user_id} (tipi: {type(user_id)}), final_score_str={final_score_str} (tipi: {type(final_score_str)})")

        if not user_id or final_score_str is None:
            logger.error(f"[DEBUG] Adım 3 BAŞARISIZ: user_id veya score alanlarından biri eksik (None).")
            await update.effective_message.reply_text("Oyun skoru alınamadı (eksik veri), lütfen tekrar deneyin.")
            return
        
        # 4. Skoru integer'a çevirmeyi dene
        logger.info("[DEBUG] Adım 4: Skor integer'a çevriliyor...")
        final_score = int(final_score_str)
        logger.info(f"[DEBUG] Adım 4 BAŞARILI: Skor integer'a çevrildi -> {final_score}")

        # 5. Kullanıcı ID'sini doğrulamayı dene
        logger.info("[DEBUG] Adım 5: Kullanıcı ID'si doğrulanıyor...")
        telegram_user_id = str(update.effective_user.id)
        if telegram_user_id != str(user_id):
            logger.warning(f"[DEBUG] Adım 5 BAŞARISIZ: User ID uyuşmazlığı. Telegram:{telegram_user_id}, WebApp:{user_id}")
            await update.effective_message.reply_text("Kullanıcı ID doğrulaması başarısız oldu. Güvenlik hatası.")
            return
        logger.info("[DEBUG] Adım 5 BAŞARILI: Kullanıcı ID'leri eşleşti.")

        # 6. Ana güncelleme fonksiyonunu çağırmayı dene
        logger.info(f"[DEBUG] Adım 6: update_user_score({telegram_user_id}, {final_score}) çağrılıyor...")
        success = await update_user_score(telegram_user_id, final_score)
        
        # 7. Sonucu kullanıcıya bildir
        if success:
            logger.info("[DEBUG] Adım 7 BAŞARILI: update_user_score 'True' döndürdü.")
            await update.effective_message.reply_text(
                f"Tebrikler! Yeni skorunuz {final_score} kaydedildi.\n"
                f"Güncel istatistiklerinizi görmek için /score yazın."
            )
        else:
            logger.error("[DEBUG] Adım 7 BAŞARISIZ: update_user_score 'False' döndürdü.")
            await update.effective_message.reply_text("Skorunuz kaydedilirken bir sorun oluştu. Lütfen tekrar deneyin.")

    except json.JSONDecodeError as e:
        logger.error(f"[DEBUG] KRİTİK HATA: JSON'a çevirme başarısız oldu. Hata: {e}")
        await update.effective_message.reply_text("Oyun verisi okunamadı (JSON Hatası).")
    except (ValueError, TypeError) as e:
        logger.error(f"[DEBUG] KRİTİK HATA: Skor integer'a çevrilemedi. Hata: {e}")
        await update.effective_message.reply_text("Geçersiz skor değeri alındı (Sayı değil).")
    except Exception as e:
        logger.error(f"[DEBUG] KRİTİK HATA: Beklenmedik bir hata oluştu. Hata: {e}", exc_info=True)
        await update.effective_message.reply_text("Genel bir hata oluştu, lütfen yöneticinizle iletişime geçin.")