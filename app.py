import os
import secrets
import psycopg2

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash


# =========================================================
# .ENV DOSYASINI YÜKLE
# =========================================================

load_dotenv()


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


# =========================================================
# SESSION GÜVENLİĞİ
# =========================================================

secret_key = os.environ.get("SECRET_KEY")

if not secret_key:
    raise Exception(
        "SECRET_KEY .env dosyasında bulunamadı!"
    )

app.secret_key = secret_key

# Session cookie güvenliği
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# HTTPS kullanıyorsan True yapabilirsin.
# Localhost testinde False bırak.
app.config["SESSION_COOKIE_SECURE"] = False


# =========================================================
# YARDIMCI FONKSİYON
# =========================================================

def admin_giris_kontrolu():

    if not session.get("admin_logged_in"):
        return False

    return True


# =========================================================
# VERİTABANI BAĞLANTISI
# =========================================================

def get_db_connection():

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception(
            "DATABASE_URL bulunamadı!"
        )

    return psycopg2.connect(database_url)


# =========================================================
# RANDEVU KODU OLUŞTUR
# =========================================================

def generate_appointment_code():

    return "KR-" + secrets.token_hex(4).upper()


# =========================================================
# TABLO OLUŞTURMA
# =========================================================

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
            appointment_code VARCHAR(20) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()


# =========================================================
# ANA SAYFA
# =========================================================

@app.route("/")
def ana_sayfa():

    return render_template("index.html")


# =========================================================
# RANDEVU
# =========================================================

@app.route("/randevu", methods=["GET", "POST"])
def randevu():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service = request.form.get("service", "").strip()

        # Basit boş alan kontrolü
        if not name or not email:

            return render_template(
                "randevu.html",
                error="Lütfen gerekli alanları doldurun."
            )

        # Benzersiz randevu kodu oluştur
        appointment_code = generate_appointment_code()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Kod çakışması kontrolü
        cursor.execute("""
            SELECT id
            FROM appointments
            WHERE appointment_code = %s
        """, (appointment_code,))

        existing = cursor.fetchone()

        while existing:

            appointment_code = generate_appointment_code()

            cursor.execute("""
                SELECT id
                FROM appointments
                WHERE appointment_code = %s
            """, (appointment_code,))

            existing = cursor.fetchone()

        # Randevuyu kaydet
        cursor.execute("""
            INSERT INTO appointments
            (
                name,
                email,
                phone,
                service,
                appointment_code
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            name,
            email,
            phone,
            service,
            appointment_code
        ))

        conn.commit()

        cursor.close()
        conn.close()

        print("----- YENİ RANDEVU -----")
        print("Randevu Kodu:", appointment_code)
        print("Ad Soyad:", name)
        print("E-posta:", email)
        print("Telefon:", phone)
        print("Görüşme Konusu:", service)
        print("------------------------")

        return render_template(
            "randevu-basarili.html",
            name=name,
            email=email,
            phone=phone,
            service=service,
            appointment_code=appointment_code
        )

    return render_template("randevu.html")


# =========================================================
# RANDEVU SORGULA
# =========================================================

@app.route("/randevu-sorgula", methods=["GET", "POST"])
def randevu_sorgula():

    appointment = None
    error = None

    if request.method == "POST":

        appointment_code = request.form.get(
            "appointment_code",
            ""
        ).strip().upper()

        if not appointment_code:

            error = "Lütfen randevu kodunuzu girin."

        else:

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    name,
                    email,
                    phone,
                    service,
                    status,
                    appointment_code,
                    created_at
                FROM appointments
                WHERE appointment_code = %s
            """, (appointment_code,))

            appointment = cursor.fetchone()

            cursor.close()
            conn.close()

            if not appointment:

                error = (
                    "Bu randevu koduna ait "
                    "bir kayıt bulunamadı."
                )

    return render_template(
        "randevu-sorgula.html",
        appointment=appointment,
        error=error
    )


# =========================================================
# ADMIN GİRİŞ
# =========================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        admin_username = os.environ.get(
            "ADMIN_USERNAME"
        )

        admin_password = os.environ.get(
            "ADMIN_PASSWORD"
        )

        if not admin_username or not admin_password:

            return (
                "Admin bilgileri .env dosyasında bulunamadı!",
                500
            )

        try:

            password_correct = check_password_hash(
                admin_password,
                password
            )

        except Exception:

            password_correct = False

        if (
            username == admin_username
            and password_correct
        ):

            # Eski session verisini temizle
            session.clear()

            # Yeni admin session oluştur
            session["admin_logged_in"] = True

            return redirect(
                url_for("admin_panel")
            )

        return render_template(
            "admin-login.html",
            error="Kullanıcı adı veya şifre hatalı!"
        )

    return render_template(
        "admin-login.html"
    )


# =========================================================
# ADMIN PANELİ
# =========================================================

@app.route("/admin/panel")
def admin_panel():

    if not admin_giris_kontrolu():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            phone,
            service,
            status,
            appointment_code,
            created_at
        FROM appointments
        ORDER BY created_at DESC
    """)

    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin-panel.html",
        appointments=appointments
    )


# =========================================================
# RANDEVU ONAYLA
# =========================================================

@app.route(
    "/admin/randevu/<int:appointment_id>/onayla",
    methods=["POST"]
)
def randevu_onayla(appointment_id):

    if not admin_giris_kontrolu():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET status = 'approved'
        WHERE id = %s
    """, (appointment_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        url_for("admin_panel")
    )


# =========================================================
# RANDEVU İPTAL
# =========================================================

@app.route(
    "/admin/randevu/<int:appointment_id>/iptal",
    methods=["POST"]
)
def randevu_iptal(appointment_id):

    if not admin_giris_kontrolu():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled'
        WHERE id = %s
    """, (appointment_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        url_for("admin_panel")
    )


# =========================================================
# RANDEVU SİL
# =========================================================

@app.route(
    "/admin/randevu/<int:appointment_id>/sil",
    methods=["POST"]
)
def randevu_sil(appointment_id):

    if not admin_giris_kontrolu():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM appointments
        WHERE id = %s
    """, (appointment_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        url_for("admin_panel")
    )


# =========================================================
# ADMIN ÇIKIŞ
# =========================================================

@app.route("/admin/cikis")
def admin_cikis():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# VERİTABANI BAŞLAT
# =========================================================

try:

    init_db()

    print(
        "PostgreSQL bağlantısı başarılı! ✅"
    )

    print(
        "appointments tablosu hazır! ✅"
    )

except Exception as e:

    print(
        "Veritabanı bağlantı hatası:",
        e
    )


# =========================================================
# FLASK
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )