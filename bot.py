import os
import logging
from flask import Flask, request, jsonify
import requests
from threading import Thread
import json
import time

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Movie data (hardcoded - no database issues)
MOVIES = [
    {
        "title": "Doraemon Three Swordsmen",
        "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
        "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen"
    },
    {
        "title": "Doraemon Jadoo Mantar",
        "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom"
    },
    {
        "title": "Stand by Me Doraemon",
        "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201"
    }
]

# Create Flask app
app = Flask(__name__)

def send_message(chat_id, text, reply_markup=None):
    """Send message via Telegram API."""
    if not TOKEN:
        return False
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return False

def send_photo(chat_id, photo, caption, reply_markup=None):
    """Send photo via Telegram API."""
    if not TOKEN:
        return False
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    data = {
        "chat_id": chat_id,
        "photo": photo,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Send photo error: {e}")
        return False

def handle_start(chat_id, user_name):
    """Handle /start command."""
    keyboard = {
        "keyboard": [[movie["title"]] for movie in MOVIES],
        "resize_keyboard": True
    }
    
    welcome_text = f"""👋 *Welcome {user_name}!* 🎬

🤖 *Doraemon Movies Bot*

🎯 Get your favorite Doraemon movies here!

✨ *Features:*
🔸 Hindi Dubbed Movies
🔸 HD Quality Downloads  
🔸 Direct Links
🔸 Fast & Free

👇 *Choose a movie:*"""
    
    send_message(chat_id, welcome_text, keyboard)

def handle_movie_request(chat_id, movie_title):
    """Handle movie selection."""
    movie = None
    for m in MOVIES:
        if movie_title.lower() in m["title"].lower() or m["title"].lower() in movie_title.lower():
            movie = m
            break
    
    if movie:
        keyboard = {
            "inline_keyboard": [[{
                "text": "📥 Download Now",
                "url": movie["link"]
            }]]
        }
        
        caption = f"🎬 **{movie['title']}**

📥 Click below to download!"
        
        # Try to send photo, fallback to text if fails
        success = send_photo(chat_id, movie["poster"], caption, keyboard)
        if not success:
            send_message(chat_id, f"{caption}

🔗 Download: {movie['link']}")
    else:
        # Movie not found - show available movies
        movies_list = "
".join([f"• {m['title']}" for m in MOVIES])
        text = f"😔 Movie not found!

📝 Available movies:
{movies_list}"
        send_message(chat_id, text)

def process_update(update_data):
    """Process incoming Telegram update."""
    try:
        message = update_data.get("message")
        if not message:
            return
        
        chat_id = message["chat"]["id"]
        user_name = message["from"].get("first_name", "User")
        text = message.get("text", "")
        
        logger.info(f"Message from {user_name}: {text}")
        
        if text.startswith("/start"):
            handle_start(chat_id, user_name)
        elif text and text != "/start":
            handle_movie_request(chat_id, text)
            
    except Exception as e:
        logger.error(f"Process update error: {e}")

# Flask routes
@app.route('/')
def home():
    return """
    <html>
    <head><title>Doraemon Movies Bot</title></head>
    <body style="font-family:Arial; background:#111; color:white; text-align:center; padding:50px;">
        <h1>🤖 Doraemon Movies Bot</h1>
        <p>✅ Bot is running successfully!</p>
        <p>📱 Start the bot on Telegram to download movies.</p>
        <hr>
        <h3>📊 Bot Status</h3>
        <p><strong>Status:</strong> Online ✅</p>
        <p><strong>Movies Available:</strong> 3</p>
        <p><strong>Features:</strong> Hindi Dubbed, HD Quality</p>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook from Telegram."""
    try:
        update_data = request.get_json()
        if update_data:
            # Process in separate thread to avoid blocking
            thread = Thread(target=process_update, args=(update_data,), daemon=True)
            thread.start()
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook')
def set_webhook():
    """Set webhook URL."""
    if not TOKEN:
        return jsonify({"error": "TOKEN not configured"}), 400
    
    if not WEBHOOK_URL:
        return jsonify({"error": "WEBHOOK_URL not configured"}), 400
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            json={"url": webhook_url},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                return jsonify({
                    "success": True,
                    "message": f"Webhook set to: {webhook_url}"
                })
        
        return jsonify({"error": "Failed to set webhook"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "bot": "online",
        "movies": len(MOVIES),
        "webhook_configured": bool(WEBHOOK_URL and TOKEN)
    })

# Main function
if __name__ == '__main__':
    # Log startup
    logger.info("🚀 Starting Doraemon Movies Bot...")
    logger.info(f"TOKEN configured: {bool(TOKEN)}")
    logger.info(f"WEBHOOK_URL configured: {bool(WEBHOOK_URL)}")
    
    # Start Flask
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"✅ Starting on port {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise