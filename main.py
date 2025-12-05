from flask import Flask, request, jsonify
import threading
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import cv2
import numpy as np
from PIL import Image
import os
import asyncio
import time

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
API_URL = "https://qrscantele-2.onrender.com/scan"

def extract_qr(image_path):
    """Extract QR code from image using OpenCV"""
    try:
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            print("Failed to load image", flush=True)
            return None
        
        # Initialize QR code detector
        detector = cv2.QRCodeDetector()
        
        # Detect and decode QR code
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        
        if data:
            print(f"QR Code detected: {data}", flush=True)
            return data
        
        print("No QR code found in image", flush=True)
        return None
        
    except Exception as e:
        print(f"Error extracting QR code: {e}", flush=True)
        return None

async def handle_photo(update: Update, context):
    """Handle incoming photos from Telegram"""
    print(f"Received photo from user {update.message.from_user.id}", flush=True)
    try:
        # Get the photo file
        file = await update.message.photo[-1].get_file()
        file_path = "qr_temp.jpg"
        
        print("Downloading photo...", flush=True)
        # Download the photo
        await file.download_to_drive(file_path)
        
        await update.message.reply_text("🔍 Scanning QR code...")
        
        # Extract QR code
        url = extract_qr(file_path)
        
        if not url:
            await update.message.reply_text("❌ No QR code found in the image. Please send a clear QR code.")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # Check URL with API
        try:
            resp = requests.get(API_URL, params={"url": url}, timeout=10)
            result = resp.json()
            
            msg = (
                f"✅ QR Code Scanned Successfully!\n\n"
                f"🔗 URL: {url}\n"
                f"📊 Status: {result.get('status', 'unknown')}\n"
                f"ℹ️ Info: {result.get('info', 'No additional info')}"
            )
        except Exception as api_error:
            print(f"API error: {api_error}", flush=True)
            msg = f"✅ QR Code Found!\n\n🔗 URL: {url}\n\n⚠️ Unable to check URL safety at this time."
        
        await update.message.reply_text(msg)
        print("Response sent to user", flush=True)
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Error handling photo: {e}", flush=True)
        await update.message.reply_text(f"❌ Error processing image: {str(e)}")
        if os.path.exists("qr_temp.jpg"):
            os.remove("qr_temp.jpg")

def start_bot():
    """Start the Telegram bot in a separate thread"""
    print("Initializing bot...", flush=True)
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print(f"Using token: {TELEGRAM_TOKEN[:10]}...", flush=True)
        
        # Build application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add photo handler
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        print("Telegram bot started successfully!", flush=True)
        print("Bot is now listening for photos...", flush=True)
        
        # Run bot
        application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"Bot error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# --------- Start bot in background thread ---------
print("Flask app initialized", flush=True)
print("Starting Telegram bot thread...", flush=True)

bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

# Give bot time to initialize
time.sleep(2)
print("Bot thread is running", flush=True)

# --------- Run Flask ---------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask server on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
