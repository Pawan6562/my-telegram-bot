import os
import sys
import time
import logging
from flask import Flask, jsonify
import requests
import threading

# Setup logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Print startup info for Railway logs
print("🚀 Doraemon Bot Starting...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Environment variables with defaults
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

print(f"PORT: {PORT}")
print(f"Bot token configured: {bool(BOT_TOKEN)}")

# Create Flask app with Railway-specific settings
app = Flask(__name__)
app.config['DEBUG'] = False

# Global state
bot_active = False
message_count = 0

def make_request(url, method="GET", data=None, timeout=10):
    """Safe HTTP request wrapper."""
    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"HTTP {response.status_code}: {url}")
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout: {url}")
    except Exception as e:
        logger.error(f"Request error: {e}")
    
    return None

def send_telegram_message(chat_id, text):
    """Send message via Telegram API."""
    if not BOT_TOKEN:
        logger.warning("No bot token - cannot send message")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    result = make_request(url, "POST", data)
    if result and result.get("ok"):
        logger.info(f"Message sent to {chat_id}")
        return True
    else:
        logger.warning(f"Failed to send message to {chat_id}")
        return False

def get_telegram_updates(offset=None):
    """Get updates from Telegram."""
    if not BOT_TOKEN:
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    
    # Build URL with parameters
    if params:
        url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    return make_request(url)

def process_message(chat_id, text, user_name):
    """Process user message."""
    global message_count
    message_count += 1
    
    logger.info(f"Processing message from {user_name}: {text}")
    
    try:
        if text == "/start":
            welcome_text = f"""🎬 <b>Welcome {user_name}!</b>

🤖 <b>Doraemon Movies Bot</b>

📺 <b>Available Movies:</b>
• Three Swordsmen
• Jadoo Mantar  
• Stand by Me

💬 <b>How to use:</b>
Type movie name to get download link

<b>Examples:</b>
• Type "jadoo" for Jadoo Mantar
• Type "three" for Three Swordsmen
• Type "stand" for Stand by Me"""

            send_telegram_message(chat_id, welcome_text)
            
        elif "jadoo" in text.lower() or "mantar" in text.lower():
            movie_text = """🎬 <b>Doraemon Jadoo Mantar Aur Jahnoom</b>

📥 <b>Download Link:</b>
https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom

⚡ Click link above to download
🎭 Hindi Dubbed | HD Quality"""

            send_telegram_message(chat_id, movie_text)
            
        elif "three" in text.lower() or "swordsmen" in text.lower():
            movie_text = """🎬 <b>Doraemon Three Swordsmen</b>

📥 <b>Download Link:</b>
https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen

⚡ Click link above to download  
🎭 Hindi Dubbed | HD Quality"""

            send_telegram_message(chat_id, movie_text)
            
        elif "stand" in text.lower():
            movie_text = """🎬 <b>Stand by Me Doraemon</b>

📥 <b>Download Link:</b>
https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201

⚡ Click link above to download
🎭 Hindi Dubbed | 3D Quality"""

            send_telegram_message(chat_id, movie_text)
            
        else:
            help_text = """🔍 <b>Available Movies:</b>

• Type <code>jadoo</code> for Jadoo Mantar
• Type <code>three</code> for Three Swordsmen  
• Type <code>stand</code> for Stand by Me

Or send /start to see menu again!"""

            send_telegram_message(chat_id, help_text)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        send_telegram_message(chat_id, "❌ Error occurred. Try /start")

def telegram_polling():
    """Main polling function."""
    global bot_active
    
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not configured!")
        return
    
    # Test bot token first
    test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    bot_info = make_request(test_url)
    
    if not bot_info or not bot_info.get("ok"):
        logger.error("❌ Invalid bot token!")
        return
    
    bot_data = bot_info["result"]
    logger.info(f"✅ Bot verified: @{bot_data['username']} ({bot_data['first_name']})")
    
    bot_active = True
    offset = 0
    
    logger.info("🔄 Starting polling loop...")
    
    while bot_active:
        try:
            updates = get_telegram_updates(offset)
            
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    try:
                        offset = update["update_id"] + 1
                        
                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg["chat"]["id"]
                            text = msg.get("text", "")
                            user_name = msg["from"].get("first_name", "User")
                            
                            # Process in separate thread
                            threading.Thread(
                                target=process_message, 
                                args=(chat_id, text, user_name),
                                daemon=True
                            ).start()
                            
                    except Exception as e:
                        logger.error(f"Update processing error: {e}")
                        
            else:
                logger.warning("No updates received, continuing...")
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)
    
    logger.info("📴 Polling stopped")

# Flask routes
@app.route("/")
def home():
    """Home page with bot status."""
    try:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Doraemon Movies Bot</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ font-family: Arial; background: #111; color: white; padding: 20px; text-align: center; }}
        .card {{ background: #222; padding: 20px; margin: 20px 0; border-radius: 10px; }}
        .green {{ color: #00ff00; }}
        .red {{ color: #ff0000; }}
        .blue {{ color: #00bfff; }}
    </style>
</head>
<body>
    <h1 class="blue">🤖 Doraemon Movies Bot</h1>
    
    <div class="card">
        <h2>📊 Status Dashboard</h2>
        <p><strong>Bot Status:</strong> <span class="{'green' if bot_active else 'red'}">{'🟢 Active' if bot_active else '🔴 Inactive'}</span></p>
        <p><strong>Token:</strong> <span class="{'green' if BOT_TOKEN else 'red'}">{'🟢 Configured' if BOT_TOKEN else '🔴 Missing'}</span></p>
        <p><strong>Messages:</strong> {message_count}</p>
        <p><strong>Port:</strong> {PORT}</p>
    </div>
    
    <div class="card">
        <h3>🎬 Available Movies</h3>
        <p>• Doraemon Three Swordsmen</p>
        <p>• Doraemon Jadoo Mantar</p>
        <p>• Stand by Me Doraemon</p>
    </div>
</body>
</html>
        """
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

@app.route("/health")
def health():
    """Health check for Railway."""
    return jsonify({
        "status": "healthy",
        "bot_active": bot_active,
        "token_configured": bool(BOT_TOKEN),
        "messages_processed": message_count,
        "port": PORT
    })

@app.route("/ping")
def ping():
    """Simple ping test."""
    return "pong"

# Main entry point
if __name__ == "__main__":
    print("=" * 50)
    print("🎬 DORAEMON MOVIES BOT - RAILWAY")
    print("=" * 50)
    
    try:
        logger.info("🚀 Starting Doraemon Movies Bot...")
        logger.info(f"📊 Port: {PORT}")
        logger.info(f"🔑 Token configured: {bool(BOT_TOKEN)}")
        
        # Start bot in background thread
        if BOT_TOKEN:
            logger.info("🤖 Starting Telegram bot...")
            bot_thread = threading.Thread(target=telegram_polling, daemon=True)
            bot_thread.start()
            logger.info("✅ Bot thread started")
        else:
            logger.warning("⚠️ Bot token not configured - bot disabled")
        
        # Start Flask server
        logger.info(f"🌐 Starting Flask server on 0.0.0.0:{PORT}")
        
        app.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        # Keep process alive even if Flask fails
        logger.info("Keeping process alive...")
        while True:
            time.sleep(60)