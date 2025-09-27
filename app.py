import os
import logging
import time
from flask import Flask, request, jsonify
import requests
import threading

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("RAILWAY_STATIC_URL", "")

# Simple movie data
MOVIES = [
    {
        "title": "Doraemon Three Swordsmen",
        "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen"
    },
    {
        "title": "Doraemon Jadoo Mantar",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom"
    },
    {
        "title": "Stand by Me Doraemon",
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201"
    }
]

# Create Flask app
app = Flask(__name__)

# Global variables for bot state
bot_running = False
message_count = 0

def send_telegram_message(chat_id, text):
    """Send message via Telegram API."""
    if not BOT_TOKEN:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False

def get_telegram_updates(offset=None):
    """Get updates from Telegram."""
    if not BOT_TOKEN:
        return None
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"timeout": 10}
        if offset:
            params["offset"] = offset
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get updates: {e}")
    
    return None

def handle_message(chat_id, text, user_name):
    """Handle incoming message."""
    global message_count
    message_count += 1
    
    try:
        # Handle /start command
        if text == "/start":
            welcome = f"""🎬 <b>Welcome {user_name}!</b>
            
🤖 <b>Doraemon Movies Bot</b>

📽️ <b>Available Movies:</b>
1. Doraemon Three Swordsmen
2. Doraemon Jadoo Mantar  
3. Stand by Me Doraemon

📱 <b>How to use:</b>
Type movie name to get download link!

Examples:
• Type "three" for Three Swordsmen
• Type "jadoo" for Jadoo Mantar
• Type "stand" for Stand by Me"""
            
            send_telegram_message(chat_id, welcome)
            return
        
        # Search for movies
        text_lower = text.lower()
        found_movie = None
        
        if "three" in text_lower or "swordsmen" in text_lower:
            found_movie = MOVIES[0]
        elif "jadoo" in text_lower or "mantar" in text_lower:
            found_movie = MOVIES[1] 
        elif "stand" in text_lower or "me" in text_lower:
            found_movie = MOVIES[2]
        
        if found_movie:
            movie_msg = f"""🎬 <b>{found_movie['title']}</b>

📥 <b>Download Link:</b>
{found_movie['link']}

⚡ Click the link above to download!
🎭 Hindi Dubbed | HD Quality"""
            
            send_telegram_message(chat_id, movie_msg)
        else:
            help_msg = """🔍 <b>Movie not found!</b>

📝 <b>Available movies:</b>
• Type "three" for Three Swordsmen
• Type "jadoo" for Jadoo Mantar
• Type "stand" for Stand by Me

Or send /start to see the menu again!"""
            
            send_telegram_message(chat_id, help_msg)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        send_telegram_message(chat_id, "Sorry, something went wrong. Please try again!")

def polling_loop():
    """Main polling loop in background."""
    global bot_running
    
    if not BOT_TOKEN:
        logger.error("No bot token configured!")
        return
    
    logger.info("Starting polling loop...")
    bot_running = True
    offset = None
    
    while bot_running:
        try:
            # Get updates
            result = get_telegram_updates(offset)
            
            if result and result.get("ok"):
                updates = result.get("result", [])
                
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        user_name = message["from"].get("first_name", "User")
                        
                        logger.info(f"Message from {user_name}: {text}")
                        
                        # Handle message in separate thread
                        threading.Thread(
                            target=handle_message,
                            args=(chat_id, text, user_name),
                            daemon=True
                        ).start()
            else:
                logger.warning(f"Failed to get updates: {result}")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)
    
    logger.info("Polling loop stopped")

# Flask routes
@app.route("/")
def home():
    """Simple homepage."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Doraemon Bot - Railway</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                background: #111; 
                color: white; 
                text-align: center; 
                padding: 50px;
            }}
            .status {{ background: #222; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .online {{ color: #00ff00; }}
            .offline {{ color: #ff0000; }}
        </style>
        <meta http-equiv="refresh" content="10">
    </head>
    <body>
        <h1>🤖 Doraemon Movies Bot</h1>
        <div class="status">
            <h2>📊 Bot Status</h2>
            <p><strong>Status:</strong> <span class="{'online' if bot_running else 'offline'}">{'✅ Running' if bot_running else '❌ Stopped'}</span></p>
            <p><strong>Messages Processed:</strong> {message_count}</p>
            <p><strong>Bot Token:</strong> {'✅ Configured' if BOT_TOKEN else '❌ Missing'}</p>
            <p><strong>Movies Available:</strong> {len(MOVIES)}</p>
        </div>
        
        <div class="status">
            <h3>🎬 Available Movies</h3>
            <p>• Doraemon Three Swordsmen</p>
            <p>• Doraemon Jadoo Mantar</p>
            <p>• Stand by Me Doraemon</p>
        </div>
        
        <div class="status">
            <h3>🚀 How to Use</h3>
            <p>1. Find your bot on Telegram</p>
            <p>2. Send /start command</p>
            <p>3. Type movie name to get download link</p>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health():
    """Health check for Railway."""
    return jsonify({
        "status": "healthy",
        "bot_running": bot_running,
        "token_configured": bool(BOT_TOKEN),
        "messages_processed": message_count,
        "movies_count": len(MOVIES)
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint (not used but kept for compatibility)."""
    return jsonify({"status": "webhook not used, using polling"})

# Start polling when app starts
def start_bot():
    """Start the bot in background."""
    if BOT_TOKEN:
        logger.info("Starting bot with polling...")
        threading.Thread(target=polling_loop, daemon=True).start()
    else:
        logger.error("TELEGRAM_TOKEN not configured!")

# Run the app
if __name__ == "__main__":
    logger.info("🚀 Starting Doraemon Bot on Railway...")
    
    # Start bot in background
    start_bot()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask server on port {port}")
    
    try:
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
