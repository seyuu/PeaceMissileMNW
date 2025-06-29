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
    user = user_ref.get().to_dict()
    total_score = score
    total_pmno_coins = score

    # Varsa toplam skorları ekle
    if user:
        total_score += user.get("total_score", 0)
        total_pmno_coins += user.get("total_pmno_coins", 0)

    # Kayıt et
    user_ref.set({
        "username": username,
        "score": max(user.get("score", 0) if user else 0, score),
        "total_score": total_score,
        "total_pmno_coins": total_pmno_coins
    }, merge=True)
    return "OK", 200

@app.route("/", methods=["GET"])
def root():
    return "Peace Missile Score API OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
