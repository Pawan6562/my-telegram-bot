# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import requests
import asyncio
from threading import Thread
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")  
MONGO_URI = os.environ.get("MONGO_URI")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Flask app
app = Flask(__name__)
bot_app = None

# Database setup
client = None
db = None
users_collection = None

def setup_database():
    global client, db, users_collection
    try:
        if not MONGO_URI:
            return False
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        logger.info("Database connected")
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

# Movie data
MOVIES_DATA = [
    {
        "title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz",
        "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
        "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen",
        "year": "2023",
        "quality": "HD"
    },
    {
        "title": "Doraemon Jadoo Mantar Aur Jahnoom", 
        "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom",
        "year": "2022",
        "quality": "HD"
    },
    {
        "title": "Stand by Me Doraemon",
        "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png", 
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201",
        "year": "2020",
        "quality": "3D"
    }
]

# Website template
WEBSITE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Doraemon Movies - Hindi Dubbed</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0f0f0f; color: white; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); padding: 40px 20px; text-align: center; }
        .title { font-size: 3em; margin-bottom: 10px; }
        .subtitle { font-size: 1.2em; opacity: 0.9; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .movies-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin: 40px 0; }
        .movie-card { background: #1e1e1e; border-radius: 15px; overflow: hidden; transition: transform 0.3s; }
        .movie-card:hover { transform: translateY(-5px); }
        .movie-poster { width: 100%; height: 350px; object-fit: cover; }
        .movie-info { padding: 20px; }
        .movie-title { font-size: 1.1em; font-weight: bold; color: #00d4ff; margin-bottom: 10px; }
        .movie-meta { color: #aaa; margin-bottom: 15px; }
        .download-btn { background: linear-gradient(45deg, #00d4ff, #0099cc); color: white; padding: 12px 20px; border: none; border-radius: 25px; text-decoration: none; display: inline-block; font-weight: bold; }
        .download-btn:hover { opacity: 0.9; }
        .stats { background: #2d2d2d; padding: 30px; text-align: center; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-item { }
        .stat-number { font-size: 2.5em; color: #00d4ff; font-weight: bold; }
        .stat-label { color: #aaa; }
        .bot-section { background: #1a1a1a; padding: 40px 20px; text-align: center; }
        .bot-btn { background: #0088cc; color: white; padding: 15px 30px; border-radius: 30px; text-decoration: none; font-weight: bold; display: inline-block; margin: 20px 0; }
        .footer { background: #111; padding: 30px; text-align: center; color: #666; }
        @media (max-width: 768px) {
            .title { font-size: 2em; }
            .movies-grid { grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🎬 Doraemon Movies</div>
        <div class="subtitle">Free Hindi Dubbed Movies • HD Quality • Fast Downloads</div>
    </div>

    <div class="stats">
        <div class="stat-item">
            <div class="stat-number">{{ total_movies }}</div>
            <div class="stat-label">Movies Available</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ total_users }}</div>
            <div class="stat-label">Happy Users</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">HD</div>
            <div class="stat-label">Quality</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">Free</div>
            <div class="stat-label">Always</div>
        </div>
    </div>

    <div class="container">
        <div class="movies-grid">
            {% for movie in movies %}
            <div class="movie-card">
                <img src="{{ movie.poster }}" alt="{{ movie.title }}" class="movie-poster">
                <div class="movie-info">
                    <div class="movie-title">{{ movie.title }}</div>
                    <div class="movie-meta">{{ movie.year }} • {{ movie.quality }} • Hindi Dubbed</div>
                    <a href="{{ movie.link }}" target="_blank" class="download-btn">📥 Download Now</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="bot-section">
        <h2>🤖 Use Our Telegram Bot</h2>
        <p>Get instant access to all movies through our Telegram bot!</p>
        <a href="https://t.me/{{ bot_username }}" class="bot-btn">📱 Start Bot</a>
    </div>

    <div class="footer">
        <p>&copy; 2025 Doraemon Movies. Made with ❤️ for fans.</p>
    </div>
</body>
</html>
"""

# Bot functions
def init_bot():
    global bot_app
    try:
        if not TOKEN:
            return False
        bot_app = Application.builder().token(TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot initialized")
        return True
    except Exception as e:
        logger.error(f"Bot error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if users_collection:
        try:
            users_collection.insert_one({
                "user_id": user.id,
                "name": user.full_name,
                "username": user.username,
                "joined_at": datetime.now()
            })
        except:
            pass

    keyboard = [[movie["title"]] for movie in MOVIES_DATA]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        "👋 *Welcome to Doraemon Movies Bot!* 🎬

"
        "🚀 यहाँ मिलती हैं सबसे बेहतरीन Doraemon movies!

"
        "✨ *Features:*
"
        "🔹 Hindi Dubbed Movies
"
        "🔹 HD Quality Downloads
"
        "🔹 Fast Direct Links

"
        "👇 *Select a movie from the menu:*"
    )

    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup, 
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    # Find movie
    movie = None
    for m in MOVIES_DATA:
        if m["title"] == message_text or message_text.lower() in m["title"].lower():
            movie = m
            break
    
    if movie:
        caption = f"🎬 **{movie['title']}**

📥 Click below to download!"
        keyboard = [[InlineKeyboardButton("📥 Download", url=movie['link'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=movie['poster'],
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

# Flask routes
@app.route('/')
def home():
    try:
        total_users = users_collection.count_documents({}) if users_collection else 100
    except:
        total_users = 100
    
    return render_template_string(
        WEBSITE_TEMPLATE,
        movies=MOVIES_DATA,
        total_movies=len(MOVIES_DATA),
        total_users=total_users,
        bot_username="YourBotUsername"
    )

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "movies": len(MOVIES_DATA),
        "bot": bot_app is not None
    })

@app.route('/set_webhook')
def set_webhook():
    if not bot_app or not WEBHOOK_URL:
        return jsonify({"error": "Bot or webhook not configured"}), 400
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    response = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", {
        'url': webhook_url
    })
    
    if response.status_code == 200:
        return jsonify({"message": f"Webhook set: {webhook_url}"})
    else:
        return jsonify({"error": "Failed"}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    if not bot_app:
        return jsonify({"error": "Bot not ready"}), 500
    
    try:
        update_data = request.get_json()
        update = Update.de_json(update_data, bot_app.bot)
        
        def process():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(bot_app.process_update(update))
            finally:
                loop.close()
        
        Thread(target=process, daemon=True).start()
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# Main function
def main():
    logger.info("Starting application...")
    
    # Setup database (optional)
    setup_database()
    
    # Setup bot (optional)  
    init_bot()
    
    # Start Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()