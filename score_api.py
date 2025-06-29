import os
import base64
from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, firestore

# Ortamdan firebase anahtarı al, yoksa local dosya
if os.environ.get("FIREBASE_CREDS_BASE64"):
    with open("firebase-key.json", "w") as f:
        f.write(base64.b64decode(os.environ["FIREBASE_CREDS_BASE64"]).decode())

cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

@app.route("/save_score", methods=["POST"])
def save_score():
    data = request.json
    user_id = str(data.get("user_id"))
    score = int(data.get("score", 0))
    username = data.get("username", "Player")

    user_ref = db.collection("users").document(user_id)
    user = user_ref.get().to_dict() or {}

    prev_max = user.get("score", 0)
    prev_total = user.get("total_score", 0)
    prev_coins = user.get("total_pmno_coins", 0)

    # MAX skor ve toplam skor güncellemesi
    new_max_score = max(prev_max, score)
    new_total_score = prev_total + score
    new_total_coins = prev_coins + score

    # DEBUG LOG
    print(f"[LOG] user_id={user_id}, score={score}, username={username}")
    print(f"[LOG] prev_max={prev_max}, prev_total={prev_total}, prev_coins={prev_coins}")
    print(f"[LOG] new_max_score={new_max_score}, new_total_score={new_total_score}, new_total_coins={new_total_coins}")

    # Firebase'e yaz
    user_ref.set({
        "username": username,
        "score": new_max_score,                # MAX skor (hiçbir zaman azalmaz)
        "total_score": new_total_score,        # Tüm oyunların toplamı
        "total_pmno_coins": new_total_coins    # Tüm oyunların toplamı (ayrıca bonuslar ekleyebilirsin)
    }, merge=True)
    return "OK", 200

@app.route("/", methods=["GET"])
def root():
    return "Peace Missile Score API OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
