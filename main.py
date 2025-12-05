from flask import Flask, request, jsonify
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import cv2
import os

# --------- Flask API ---------
app = Flask(__name__)

# --------- Telegram Bot ---------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8585326191:AAGWahXKfYW_FvyLtg5g8xDU_KdkHkX8QW0")
API_URL = "https://qrscantele-2.onrender.com/scan"
WEBHOOK_URL = "https://qrscantele-2.onrender.com/webhook"

# Create bot application
application = Application.builder().token(TELEGRAM_TOKEN).build()

def extract_qr(image_path):
    """Extract QR code from image using OpenCV"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            print("Failed to load image", flush=True)
            return None
        
        detector = cv2.QRCodeDetector()
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
        file = await update.message.photo[-1].get_file()
        file_path = "qr_temp.jpg"
        
        print("Downloading photo...", flush=True)
        await file.download_to_drive(file_path)
        
        await update.message.reply_text("🔍 Scanning QR code...")
        
        url = extract_qr(file_path)
        
        if not url:
            await update.message.reply_text("❌ No QR code found in the image. Please send a clear QR code.")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
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
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Error handling photo: {e}", flush=True)
        await update.message.reply_text(f"❌ Error processing image: {str(e)}")
        if os.path.exists("qr_temp.jpg"):
            os.remove("qr_temp.jpg")

# Add handler
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

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

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming Telegram updates via webhook"""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}", flush=True)
        return "Error", 500

@app.route("/set_webhook")
def set_webhook():
    """Set the webhook URL"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    response = requests.post(url, json=payload)
    return response.json()

print("Flask app initialized", flush=True)
print("Bot webhook handler ready", flush=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
