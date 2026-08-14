import logging
import os
import time
import requests
from flask import Flask
from threading import Thread

# Flask ရဲ့ Log စာကြောင်းများ မရှုပ်အောင် ပိတ်ထားမည်
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Replit/Node Server နဲ့ မငြိစေရန် Port 5050 သို့ ပြောင်းသုံးပါမည်
PORT = int(os.environ.get("PORT", "5050"))

@app.route('/')
@app.route('/<path:path>')
def home(path=""):
    return "🤖 Bot Self-Ping System is Active!", 200

def self_ping_loop():
    time.sleep(5)  # Web Server တက်လာအောင် ၅ စက္ကန့် ခဏစောင့်မည်
    while True:
        try:
            res = requests.get(f"http://127.0.0.1:{PORT}/", timeout=5)
            print(f"🔄 [Self-Ping Success] Status: {res.status_code}")
        except Exception as e:
            print(f"⚠️ [Self-Ping Error]: {e}")
        
        time.sleep(180)  # ၃ မိနစ်တစ်ကြိမ် Self-Ping ရိုက်မည်

def run_flask():
    try:
        app.run(host='0.0.0.0', port=PORT)
    except Exception as e:
        print(f"⚠️ [Flask Server Error]: {e}")

def keep_alive():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    ping_thread = Thread(target=self_ping_loop)
    ping_thread.daemon = True
    ping_thread.start()

    print(f"🚀 Keep-Alive Web Server started on Port {PORT}!")
    