from flask import Flask, render_template, request

app = Flask(__name__)


# Ana sayfa
@app.route("/")
def ana_sayfa():
    return render_template("index.html")


# Randevu sayfası
@app.route("/randevu", methods=["GET", "POST"])
def randevu():

    # Form gönderildiğinde
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        service = request.form.get("service")

        # Bilgileri terminale yazdır
        print("----- YENİ RANDEVU -----")
        print("Ad Soyad:", name)
        print("E-posta:", email)
        print("Telefon:", phone)
        print("Görüşme Konusu:", service)
        print("------------------------")

        return "Randevu bilgileri Python tarafından alındı! ✅"

    # Sayfa ilk açıldığında
    return render_template("randevu.html")


# Flask uygulamasını başlat
if __name__ == "__main__":
    app.run(debug=True)