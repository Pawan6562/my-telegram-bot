import os
import logging
import json
from flask import Flask, request, jsonify
import requests
from threading import Thread
import time

# Configure logging for Railway
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("WEBHOOK_URL")
ADMIN_ID = os.environ.get("ADMIN_ID")

# Movie data
MOVIES = [
    {
        "title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz",
        "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
        "download": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen",
        "keywords": ["three", "swordsmen", "talwar", "teen", "3"]
    },
    {
        "title": "Doraemon Jadoo Mantar Aur Jahnoom",
        "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
        "download": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom",
        "keywords": ["jadoo", "mantar", "magic", "jahnoom", "hell"]
    },
    {
        "title": "Stand by Me Doraemon",
        "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png",
        "download": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201",
        "keywords": ["stand by me", "emotional", "3d"]
    }
]

# Create Flask app
app = Flask(__name__)

# Store user data in memory (Railway compatible)
user_data = {}

def call_telegram_api(method, data=None):
    """Make API calls to Telegram."""
    if not BOT_TOKEN:
        logger.error("No bot token found")
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    
    try:
        if data:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        result = response.json()
        if not result.get("ok"):
            logger.error(f"Telegram API error: {result}")
        return result
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    """Send message to user."""
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    return call_telegram_api("sendMessage", data)

def send_photo(chat_id, photo_url, caption, reply_markup=None):
    """Send photo with caption."""
    data = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    return call_telegram_api("sendPhoto", data)

def create_keyboard(buttons):
    """Create custom keyboard."""
    return {
        "keyboard": buttons,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def create_inline_keyboard(buttons):
    """Create inline keyboard."""
    return {
        "inline_keyboard": buttons
    }

def handle_start_command(chat_id, user_name, user_id):
    """Handle /start command."""
    # Store user data
    user_data[user_id] = {
        "name": user_name,
        "chat_id": chat_id,
        "last_active": time.time()
    }
    
    # Create movie keyboard
    keyboard_buttons = []
    for movie in MOVIES:
        keyboard_buttons.append([movie["title"]])
    
    keyboard_buttons.append(["🔍 Search Movies", "ℹ️ Help"])
    keyboard = create_keyboard(keyboard_buttons)
    
    welcome_text = f"""👋 *Welcome {user_name}!* 🎬

🤖 *Doraemon Movies Bot*

🎯 यहाँ मिलती हैं बेहतरीन Doraemon movies!

✨ *Features:*
🔸 Hindi Dubbed Movies
🔸 HD Quality Downloads
🔸 Direct Download Links
🔸 Fast & Free

📱 *How to use:*
• Select movie from keyboard below
• Or type movie name to search
• Get instant download links

🎬 *Available Movies: {len(MOVIES)}*

👇 *Choose a movie:*"""
    
    send_message(chat_id, welcome_text, keyboard)

def find_movie(query):
    """Find movie by title or keywords."""
    query = query.lower()
    found_movies = []
    
    for movie in MOVIES:
        # Check title
        if query in movie["title"].lower():
            found_movies.append(movie)
            continue
        
        # Check keywords
        for keyword in movie["keywords"]:
            if query in keyword or keyword in query:
                found_movies.append(movie)
                break
    
    return found_movies

def send_movie(chat_id, movie):
    """Send movie with download button."""
    inline_keyboard = create_inline_keyboard([[{
        "text": "📥 Download Now",
        "url": movie["download"]
    }]])
    
    caption = f"""🎬 **{movie['title']}**

📱 *Click button below to download*
⚡ *Direct & Fast Download*
🎭 *Hindi Dubbed*"""
    
    # Try to send photo, fallback to text
    result = send_photo(chat_id, movie["poster"], caption, inline_keyboard)
    
    if not result or not result.get("ok"):
        # Fallback to text message
        text_msg = f"{caption}

📥 Download: {movie['download']}"
        send_message(chat_id, text_msg, inline_keyboard)

def process_message(message):
    """Process incoming message."""
    try:
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        user_name = message["from"].get("first_name", "User")
        text = message.get("text", "")
        
        logger.info(f"Message from {user_name} ({user_id}): {text}")
        
        # Handle commands
        if text.startswith("/start"):
            handle_start_command(chat_id, user_name, user_id)
            return
        
        if "help" in text.lower() or "ℹ️" in text:
            help_text = """🤖 *Doraemon Movies Bot Help*

🎬 *Available Movies:*
• Three Swordsmen
• Jadoo Mantar  
• Stand by Me

🔍 *Search Examples:*
• Type "jadoo" for magic movies
• Type "stand" for Stand by Me
• Type "three" for Three Swordsmen

Just select from keyboard or type movie name!"""
            
            send_message(chat_id, help_text)
            return
        
        # Handle search request
        if "search" in text.lower() or "🔍" in text:
            send_message(chat_id, "🔍 Type movie name or keyword to search!")
            return
        
        # Handle exact movie title selection
        selected_movie = None
        for movie in MOVIES:
            if text == movie["title"]:
                selected_movie = movie
                break
        
        if selected_movie:
            send_movie(chat_id, selected_movie)
            return
        
        # Handle movie search
        if text and not text.startswith("/"):
            found_movies = find_movie(text)
            
            if not found_movies:
                not_found_msg = """😔 *No movies found!*

🔍 *Try searching for:*
• jadoo (magic movies)
• stand (Stand by Me)
• three (Three Swordsmen)

💡 *Use the keyboard menu below!*"""
                
                send_message(chat_id, not_found_msg)
                
            elif len(found_movies) == 1:
                # Single movie found
                send_movie(chat_id, found_movies[0])
                
            else:
                # Multiple movies found
                result_msg = f"🎯 *Found {len(found_movies)} movies:*

"
                
                for i, movie in enumerate(found_movies, 1):
                    result_msg += f"{i}. {movie['title']}
"
                
                result_msg += "
💡 *Tap exact movie title from keyboard!*"
                send_message(chat_id, result_msg)
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Flask routes
@app.route("/")
def home():
    """Homepage showing bot status."""
    return f"""
    <html>
    <head><title>🤖 Doraemon Movies Bot</title></head>
    <body style="font-family:Arial; background:#111; color:white; text-align:center; padding:50px;">
        <h1>🤖 Doraemon Movies Bot</h1>
        <p>✅ Bot is running on Railway!</p>
        <p>📱 Movies Available: {len(MOVIES)}</p>
        <p>👥 Active Users: {len(user_data)}</p>
        <hr>
        <p>Start the bot on Telegram: /start</p>
    </body>
    </html>
    """

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle Telegram webhook."""
    try:
        update = request.get_json()
        
        if not update:
            return jsonify({"status": "no update data"})
        
        # Process message in separate thread
        if "message" in update:
            thread = Thread(target=process_message, args=(update["message"],), daemon=True)
            thread.start()
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/set_webhook")
def set_webhook():
    """Set webhook URL."""
    if not BOT_TOKEN:
        return "❌ No bot token configured"
    
    if not WEBHOOK_URL:
        return "❌ No webhook URL configured"
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    
    result = call_telegram_api("setWebhook", {"url": webhook_url})
    
    if result and result.get("ok"):
        return f"✅ Webhook set to: {webhook_url}"
    else:
        return f"❌ Failed to set webhook: {result}"

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "bot_configured": bool(BOT_TOKEN),
        "movies_count": len(MOVIES),
        "users_count": len(user_data),
        "platform": "Railway"
    })

# Main execution
if __name__ == "__main__":
    logger.info("🚀 Starting Doraemon Movies Bot on Railway...")
    
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN environment variable not set!")
        exit(1)
    
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Starting Flask server on port {port}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )