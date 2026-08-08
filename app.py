import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template, request

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)


# ==============================
# VERİTABANI BAĞLANTISI
# ==============================

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL bulunamadı!")

    return psycopg2.connect(database_url)


# ==============================
# TABLO OLUŞTURMA
# ==============================

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL,
            phone VARCHAR(30),
            service VARCHAR(100),
            status VARCHAR(30) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()


# ==============================
# ANA SAYFA
# ==============================

@app.route("/")
def ana_sayfa():
    return render_template("index.html")


# ==============================
# RANDEVU SAYFASI
# ==============================

@app.route("/randevu", methods=["GET", "POST"])
def randevu():

    # Form gönderildiğinde
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        service = request.form.get("service")

        # Veritabanına kaydet
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO appointments
            (name, email, phone, service)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            email,
            phone,
            service
        ))

        conn.commit()

        cursor.close()
        conn.close()

        # Terminale yazdır
        print("----- YENİ RANDEVU -----")
        print("Ad Soyad:", name)
        print("E-posta:", email)
        print("Telefon:", phone)
        print("Görüşme Konusu:", service)
        print("------------------------")

        return """
        <h2>Randevu talebiniz alındı! ✅</h2>
        <p>Bilgileriniz başarıyla kaydedildi.</p>
        <a href="/">Ana Sayfaya Dön</a>
        """

    # Sayfa ilk açıldığında
    return render_template("randevu.html")


# ==============================
# UYGULAMA BAŞLARKEN
# ==============================

try:
    init_db()
    print("PostgreSQL bağlantısı başarılı! ✅")
    print("appointments tablosu hazır! ✅")

except Exception as e:
    print("Veritabanı bağlantı hatası:", e)


# ==============================
# FLASK
# ==============================

if __name__ == "__main__":
    app.run(debug=True)