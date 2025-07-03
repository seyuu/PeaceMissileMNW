# Python 3.11'ı temel al
FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarının tamamını kopyala
COPY . .

# Procfile'daki komutu çalıştır
# Cloud Run, PORT ortam değişkenini otomatik olarak sağlar.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
