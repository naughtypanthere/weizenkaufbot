import json, os, requests
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("BOT_TOKEN")
API = "https://api.telegram.org/bot" + TOKEN
DATEI = "einkaufsliste.json"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot läuft!"

def lade():
    try:
        with open(DATEI) as f:
            return json.load(f)
    except Exception:
        return []

def speichere(liste):
    with open(DATEI, "w") as f:
        json.dump(liste, f, ensure_ascii=False)

def sende(chat_id, text):
    requests.post(API + "/sendMessage", json={"chat_id": chat_id, "text": 
text})

def formatiere(liste):
    if not liste:
        return "🛒 Einkaufsliste ist leer."
    return "🛒 Einkaufsliste:\n" + "\n".join("• " + e for e in liste)

def verarbeite(msg):
    text = msg.get("text", "")
    chat_id = msg["chat"]["id"]
    if not text.startswith("/list"):
        return
    rest = text[5:].strip()  # alles nach "/list"
    liste = lade()

    if rest == "":
        sende(chat_id, formatiere(liste))
    elif rest.lower() == "clear":
        speichere([])
        sende(chat_id, "🗑 Liste gelöscht.")
    elif rest.startswith("-"):
        entfernen = [x.strip().lower() for x in rest[1:].split(",") if 
x.strip()]
        liste = [e for e in liste if e.lower() not in entfernen]
        speichere(liste)
        sende(chat_id, "✅ Erledigt/entfernt:\n" + formatiere(liste))
    else:
        liste += [x.strip() for x in rest.split(",") if x.strip()]
        speichere(liste)
        sende(chat_id, "📝 Aktualisiert:\n" + formatiere(liste))

def polling():
    offset = 0
    while True:
        try:
            r = requests.get(API + "/getUpdates",
                             params={"timeout": 25, "offset": offset},
                             timeout=30).json()
            for update in r.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    verarbeite(update["message"])
        except Exception:
            pass  # bei Netzwerkproblemen einfach weiterlaufen

Thread(target=polling, daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
