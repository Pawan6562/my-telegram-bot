import os
import time
import logging
import requests
import json
from datetime import datetime
from threading import Thread
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

# Movie database
MOVIES = [
    {
        "title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz",
        "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
        "download": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen",
        "keywords": ["three", "swordsmen", "talwar", "teen", "3", "visionary"]
    },
    {
        "title": "Doraemon Jadoo Mantar Aur Jahnoom", 
        "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
        "download": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom",
        "keywords": ["jadoo", "mantar", "magic", "jahnoom", "hell", "underworld"]
    },
    {
        "title": "Stand by Me Doraemon",
        "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png",
        "download": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201",
        "keywords": ["stand by me", "emotional", "3d", "friendship"]
    }
]

# Bot statistics
bot_stats = {
    "total_users": 0,
    "total_messages": 0,
    "uptime_start": datetime.now(),
    "last_update_id": 0
}

# User database (in-memory)
users_db = {}

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.running = False
        self.offset = 0
        
    def call_api(self, method, params=None, data=None):
        """Make API call to Telegram."""
        url = f"{self.base_url}/{method}"
        
        try:
            if data:
                response = requests.post(url, json=data, timeout=10)
            else:
                response = requests.get(url, params=params, timeout=10)
            
            result = response.json()
            
            if not result.get("ok"):
                logger.error(f"API Error: {result}")
                
            return result
            
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None
    
    def get_updates(self, offset=None, timeout=30):
        """Get new messages using long polling."""
        params = {
            "timeout": timeout,
            "allowed_updates": ["message"]
        }
        
        if offset:
            params["offset"] = offset
            
        return self.call_api("getUpdates", params)
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode="Markdown"):
        """Send text message."""
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
            
        return self.call_api("sendMessage", data=data)
    
    def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode="Markdown"):
        """Send photo message."""
        data = {
            "chat_id": chat_id,
            "photo": photo,
            "parse_mode": parse_mode
        }
        
        if caption:
            data["caption"] = caption
            
        if reply_markup:
            data["reply_markup"] = reply_markup
            
        return self.call_api("sendPhoto", data=data)
    
    def create_keyboard(self, buttons):
        """Create custom keyboard."""
        return {
            "keyboard": buttons,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    def create_inline_keyboard(self, buttons):
        """Create inline keyboard.""" 
        return {
            "inline_keyboard": buttons
        }
    
    def handle_start(self, message):
        """Handle /start command."""
        chat_id = message["chat"]["id"]
        user = message["from"]
        user_id = user["id"]
        user_name = user.get("first_name", "User")
        
        # Add user to database
        users_db[user_id] = {
            "name": user_name,
            "username": user.get("username"),
            "chat_id": chat_id,
            "joined_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
        
        bot_stats["total_users"] = len(users_db)
        
        # Create movie keyboard
        keyboard_buttons = []
        for movie in MOVIES:
            keyboard_buttons.append([movie["title"]])
        
        keyboard_buttons.append(["🔍 Search Movies", "📊 Bot Stats", "ℹ️ Help"])
        keyboard = self.create_keyboard(keyboard_buttons)
        
        welcome_text = f"""👋 *Welcome {user_name}!* 🎬

🤖 *Doraemon Movies Bot*

🎯 यहाँ मिलती हैं सबसे बेहतरीन Doraemon movies!

✨ *Features:*
🔸 Hindi Dubbed Movies
🔸 HD Quality Downloads  
🔸 Direct Download Links
🔸 Fast & Free
🔸 Always Online

📱 *How to use:*
• Select movie from keyboard below
• Or type movie name to search
• Get instant download links

🎬 *Available Movies: {len(MOVIES)}*
👥 *Total Users: {len(users_db)}*

👇 *Choose a movie from the menu:*"""
        
        self.send_message(chat_id, welcome_text, keyboard)
    
    def find_movie(self, query):
        """Search for movies."""
        query = query.lower()
        found_movies = []
        
        for movie in MOVIES:
            # Check title
            if query in movie["title"].lower():
                found_movies.append(movie)
                continue
                
            # Check keywords
            for keyword in movie["keywords"]:
                if query in keyword.lower() or keyword.lower() in query:
                    found_movies.append(movie)
                    break
        
        return found_movies
    
    def send_movie(self, chat_id, movie):
        """Send movie with download button."""
        inline_keyboard = self.create_inline_keyboard([[{
            "text": "📥 Download Now",
            "url": movie["download"]
        }]])
        
        caption = f"""🎬 **{movie['title']}**

📱 *Click button below to download*
⚡ *Direct & Fast Download*  
🎭 *Hindi Dubbed*
🔗 *Multiple quality options available*"""
        
        # Try sending photo first, fallback to text
        result = self.send_photo(chat_id, movie["poster"], caption, inline_keyboard)
        
        if not result or not result.get("ok"):
            # Fallback to text message
            text_msg = f"{caption}

📥 Direct Download: {movie['download']}"
            self.send_message(chat_id, text_msg, inline_keyboard)
    
    def handle_message(self, message):
        """Process incoming message."""
        try:
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            user_name = message["from"].get("first_name", "User")
            text = message.get("text", "")
            
            # Update user activity
            if user_id in users_db:
                users_db[user_id]["last_active"] = datetime.now().isoformat()
            
            bot_stats["total_messages"] += 1
            
            logger.info(f"Message from {user_name} ({user_id}): {text}")
            
            # Handle commands
            if text.startswith("/start"):
                self.handle_start(message)
                return
                
            if text.startswith("/help") or text == "ℹ️ Help":
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
                
                self.send_message(chat_id, help_text)
                return
            
            if "stats" in text.lower() or text == "📊 Bot Stats":
                uptime = datetime.now() - bot_stats["uptime_start"]
                uptime_str = str(uptime).split('.')[0]
                
                stats_text = f"""📊 *Bot Statistics*

👥 *Users:* {len(users_db)}
📱 *Messages:* {bot_stats['total_messages']}
⏰ *Uptime:* {uptime_str}
🎬 *Movies:* {len(MOVIES)}
🤖 *Status:* Online ✅"""
                
                self.send_message(chat_id, stats_text)
                return
            
            # Handle search
            if "search" in text.lower() or text == "🔍 Search Movies":
                search_help = """🔍 *Movie Search*

Type any movie name or keyword:

💡 *Examples:*
• `jadoo` ➜ Magic movies
• `stand` ➜ Stand by Me series
• `three` ➜ Three Swordsmen

Just type what you're looking for!"""
                
                self.send_message(chat_id, search_help)
                return
            
            # Handle exact movie title match
            selected_movie = None
            for movie in MOVIES:
                if text == movie["title"]:
                    selected_movie = movie
                    break
            
            if selected_movie:
                self.send_movie(chat_id, selected_movie)
                return
            
            # Handle movie search
            if text and not text.startswith("/"):
                found_movies = self.find_movie(text)
                
                if not found_movies:
                    not_found_msg = """😔 *No movies found!*

🔍 *Try searching for:*
• `jadoo` (magic movies)
• `stand` (Stand by Me series)  
• `three` (Three Swordsmen)

💡 *Use the keyboard menu for easy access!*"""
                    
                    self.send_message(chat_id, not_found_msg)
                    
                elif len(found_movies) == 1:
                    # Single movie found
                    self.send_movie(chat_id, found_movies[0])
                    
                else:
                    # Multiple movies found
                    result_msg = f"🎯 *Found {len(found_movies)} movies:*

"
                    
                    for i, movie in enumerate(found_movies, 1):
                        result_msg += f"{i}. {movie['title']}
"
                    
                    result_msg += "
💡 *Tap exact movie title from keyboard!*"
                    self.send_message(chat_id, result_msg)
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def start_polling(self):
        """Start the polling loop."""
        if not self.token:
            logger.error("❌ No bot token provided!")
            return
        
        logger.info("🚀 Starting bot with polling...")
        self.running = True
        
        # Test bot token
        me = self.call_api("getMe")
        if not me or not me.get("ok"):
            logger.error("❌ Invalid bot token!")
            return
        
        bot_info = me["result"]
        logger.info(f"✅ Bot started: @{bot_info['username']} ({bot_info['first_name']})")
        
        # Main polling loop
        while self.running:
            try:
                # Get updates with long polling
                result = self.get_updates(self.offset)
                
                if result and result.get("ok"):
                    updates = result.get("result", [])
                    
                    for update in updates:
                        self.offset = update["update_id"] + 1
                        bot_stats["last_update_id"] = update["update_id"]
                        
                        if "message" in update:
                            # Process message in separate thread
                            Thread(target=self.handle_message, args=(update["message"],), daemon=True).start()
                        
                else:
                    logger.error(f"Failed to get updates: {result}")
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(5)
        
        self.running = False
        logger.info("👋 Bot polling stopped")

# Initialize bot
bot = TelegramBot(BOT_TOKEN) if BOT_TOKEN else None

# Flask app for health checks
app = Flask(__name__)

@app.route("/")
def home():
    """Homepage with bot status."""
    if not bot:
        status = "❌ Bot token not configured"
        bot_running = False
    else:
        status = "✅ Bot is running with polling" if bot.running else "⏸️ Bot is stopped"
        bot_running = bot.running
    
    uptime = datetime.now() - bot_stats["uptime_start"]
    uptime_str = str(uptime).split('.')[0]
    
    return f"""
    <html>
    <head><title>🤖 Doraemon Movies Bot - Polling</title></head>
    <body style="font-family:Arial; background:#111; color:white; text-align:center; padding:50px;">
        <h1>🤖 Doraemon Movies Bot</h1>
        <h2>✅ Polling Mode - No Webhooks!</h2>
        
        <div style="background:#222; padding:20px; border-radius:10px; margin:20px 0;">
            <h3>📊 Bot Status</h3>
            <p><strong>Status:</strong> <span style="color:{'#00ff00' if bot_running else '#ff6600'}">{status}</span></p>
            <p><strong>Mode:</strong> Polling (More Reliable)</p>
            <p><strong>Platform:</strong> Railway</p>
            <p><strong>Uptime:</strong> {uptime_str}</p>
        </div>
        
        <div style="background:#222; padding:20px; border-radius:10px; margin:20px 0;">
            <h3>📈 Statistics</h3>
            <p><strong>Total Users:</strong> {len(users_db)}</p>
            <p><strong>Messages:</strong> {bot_stats['total_messages']}</p>
            <p><strong>Movies:</strong> {len(MOVIES)}</p>
        </div>
        
        <div style="background:#222; padding:20px; border-radius:10px;">
            <h3>🎬 Available Movies</h3>
            {"".join([f"<p>• {movie['title']}</p>" for movie in MOVIES])}
        </div>
        
        <p>Start the bot: Send /start to your bot on Telegram!</p>
    </body>
    </html>
    """

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "bot_running": bot.running if bot else False,
        "mode": "polling",
        "total_users": len(users_db),
        "total_messages": bot_stats["total_messages"],
        "movies_count": len(MOVIES)
    })

# Start bot automatically when deployed
def start_bot_automatically():
    """Start bot in background thread."""
    if bot and BOT_TOKEN:
        logger.info("🤖 Auto-starting bot...")
        Thread(target=bot.start_polling, daemon=True).start()
    else:
        logger.error("❌ Cannot start bot - token missing")

# Main execution
if __name__ == "__main__":
    if BOT_TOKEN:
        # Start bot in background
        start_bot_automatically()
        
        # Start Flask for health checks
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"🌐 Starting Flask health server on port {port}")
        
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False
        )
    else:
        logger.error("❌ TELEGRAM_TOKEN environment variable not set!")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))