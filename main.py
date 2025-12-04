from flask import Flask, request, jsonify
import threading
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from pyzbar.pyzbar import decode
from PIL import Image
import os
import asyncio

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
    return jsonify({
        "url": url,
        "status": "safe",
        "info": "This is demo result"
    })

# --------- Telegram Bot ---------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8585326191:AAGWahXKfYW_FvyLtg5g8xDU_KdkHkX8QW0")
API_URL = "https://QrScanTele-2.onrender.com/scan"

def extract_qr(image_path):
    img = Image.open(image_path)
    data = decode(img)
    if data:
        return data[0].data.decode()
    return None

async def handle_photo(update: Update, context):
    try:
        file = await update.message.photo[-1].get_file()
        file_path = "qr.jpg"
        await file.download_to_drive(file_path)
        
        await update.message.reply_text("🔍 Scanning QR code...")
        
        url = extract_qr(file_path)
        if not url:
            await update.message.reply_text("❌ No URL found in QR code.")
            os.remove(file_path)
            return
        
        resp = requests.get(API_URL, params={"url": url})
        result = resp.json()
        msg = f"🔗 QR URL: {url}\n✅ Status: {result.get('status', 'unknown')}\nℹ️ Info: {result.get('info', 'No info')}"
        await update.message.reply_text(msg)
        
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)

def start_bot():
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Build application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Run bot
    print("🤖 Starting Telegram bot...")
    application.run_polling(drop_pending_updates=True)

# --------- Run Telegram bot in a separate thread ---------
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

# --------- Run Flask ---------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
