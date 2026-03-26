from flask import Flask, render_template, request, redirect
import os
import requests
import sqlite3

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

BOT_TOKEN = "8687466350:AAGGRX_4WTkyRUo_fcnVHWJT6CYpn1gKFlI"
ADMIN_CHAT_ID = "8537142398"

# DATABASE
conn = sqlite3.connect('data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS peminjaman (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    nim TEXT,
    barang TEXT,
    foto TEXT,
    status TEXT
)
''')
conn.commit()

# HOME
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nama = request.form["nama"]
        nim = request.form["nim"]
        barang = request.form["barang"]

        file = request.files["foto"]
        filename = file.filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        c.execute("INSERT INTO peminjaman (nama,nim,barang,foto,status) VALUES (?,?,?,?,?)",
                  (nama, nim, barang, filename, "Menunggu"))
        conn.commit()

        id_data = c.lastrowid

        kirim_telegram(nama, nim, barang, path, id_data)

        return redirect("/")

    data = c.execute("SELECT * FROM peminjaman").fetchall()
    return render_template("index.html", data=data)

# KIRIM TELEGRAM
def kirim_telegram(nama, nim, barang, foto_path, id_data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve_{id_data}"},
            {"text": "❌ Reject", "callback_data": f"reject_{id_data}"}
        ]]
    }

    with open(foto_path, "rb") as foto:
        requests.post(url,
            data={
                "chat_id": ADMIN_CHAT_ID,
                "caption": f"📥 PEMINJAMAN\n\n👤 {nama}\n🎓 {nim}\n📦 {barang}",
                "reply_markup": str(keyboard)
            },
            files={"photo": foto}
        )

# WEBHOOK TELEGRAM
@app.route("/callback", methods=["POST"])
def callback():
    data = request.json

    if "callback_query" in data:
        query = data["callback_query"]
        action = query["data"]

        id_data = action.split("_")[1]

        if "approve" in action:
            status = "Disetujui"
        else:
            status = "Ditolak"

        c.execute("UPDATE peminjaman SET status=? WHERE id=?", (status, id_data))
        conn.commit()

    return "ok"

app.run(debug=True)