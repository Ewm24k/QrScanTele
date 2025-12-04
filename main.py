from flask import Flask, request, jsonify
import threading
import requests
from telegram.ext import Updater, MessageHandler, Filters
from pyzbar.pyzbar import decode
from PIL import Image
import os
import sys
import types

# --------- Patch imghdr for Python 3.13 ---------
try:
    import imghdr
except ModuleNotFoundError:
    imghdr = types.ModuleType("imghdr")
    sys.modules["imghdr"] = imghdr

# --------- Flask API ---------
app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "Python API is running on Render!"}

@app.route("/scan")
def scan():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Example logic — replace with real phishing check
    return jsonify({
        "url": url,
        "status": "safe",
        "info": "This is demo result"
    })

# --------- Telegram Bot ---------
TELEGRAM_TOKEN = "8585326191:AAGWahXKfYW_FvyLtg5g8xDU_KdkHkX8QW0"
API_URL = "https://QrScanTele-2.onrender.com/scan"

def extract_qr(image_path):
    img = Image.open(image_path)
    data = decode(img)
    if data:
        return data[0].data.decode()
    return None

def handle_photo(update, context):
    file = update.message.photo[-1].get_file()
    file_path = "qr.jpg"
    file.download(file_path)

    update.message.reply_text("🔍 Scanning QR code...")

    url = extract_qr(file_path)
    if not url:
        update.message.reply_text("❌ No URL found in QR code.")
        os.remove(file_path)
        return

    resp = requests.get(API_URL, params={"url": url})
    result = resp.json()

    msg = f"🔗 QR URL: {url}\nResult: {result}"
    update.message.reply_text(msg)
    os.remove(file_path)

def start_bot():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    updater.start_polling()
    updater.idle()

# --------- Run Telegram bot in a separate thread ---------
bot_thread = threading.Thread(target=start_bot)
bot_thread.start()

# --------- Run Flask ---------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
