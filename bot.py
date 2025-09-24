import os
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import requests
from threading import Thread
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
MONGO_URI = os.environ.get("MONGO_URI")

if not TOKEN:
    logger.error("TELEGRAM_TOKEN not found!")
    exit(1)

if not MONGO_URI:
    logger.error("MONGO_URI not found!")
    exit(1)

# Database setup
client = None
db = None
users_collection = None
analytics_collection = None
movies_collection = None

def setup_database():
    """Setup MongoDB connection and collections."""
    global client, db, users_collection, analytics_collection, movies_collection
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        analytics_collection = db.analytics
        movies_collection = db.movies
        
        # Create indexes
        users_collection.create_index("user_id", unique=True)
        analytics_collection.create_index("timestamp")
        movies_collection.create_index("title", unique=True)
        
        # Initialize movies data if empty
        if movies_collection.count_documents({}) == 0:
            initialize_movies_data()
        
        logger.info("✅ MongoDB connected successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False

def initialize_movies_data():
    """Initialize movies collection with data."""
    movies_data = [
        {
            "title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz",
            "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
            "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen",
            "keywords": ["three", "3", "teen", "visionary", "drishti", "swordsmen", "talwar"],
            "year": "2023",
            "quality": "HD",
            "active": True,
            "downloads": 0,
            "added_date": datetime.now()
        },
        {
            "title": "Doraemon Jadoo Mantar Aur Jahnoom",
            "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
            "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom",
            "keywords": ["jadoo", "magic", "mantar", "jahnoom", "hell", "underworld"],
            "year": "2022",
            "quality": "HD",
            "active": True,
            "downloads": 0,
            "added_date": datetime.now()
        },
        {
            "title": "Doraemon Dinosaur Yoddha",
            "poster": "https://i.postimg.cc/3w83qTtr/Doraemon-The-Movie-Dinosaur-Yoddhha-Hindi-Tamil-Telugu-Download-FHD-990x557.jpg",
            "link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha",
            "keywords": ["dinosaur", "dino", "yodha", "warrior", "knight"],
            "year": "2021",
            "quality": "FHD",
            "active": True,
            "downloads": 0,
            "added_date": datetime.now()
        },
        {
            "title": "Stand by Me Doraemon",
            "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png",
            "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201",
            "keywords": ["stand by me", "3d", "emotional", "friendship"],
            "year": "2020",
            "quality": "3D",
            "active": True,
            "downloads": 0,
            "added_date": datetime.now()
        },
        {
            "title": "Stand by Me Doraemon 2",
            "poster": "https://i.postimg.cc/y8wkR4PJ/Doraemon-The-Movie-Stand-by-Me-2-by-cjh.png",
            "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202",
            "keywords": ["stand by me 2", "part 2", "sequel", "3d"],
            "year": "2021",
            "quality": "3D",
            "active": True,
            "downloads": 0,
            "added_date": datetime.now()
        }
    ]
    
    movies_collection.insert_many(movies_data)
    logger.info(f"✅ Initialized {len(movies_data)} movies in database")

# Analytics functions
def log_user_activity(user_id, activity, details=None):
    """Log user activity to analytics collection."""
    try:
        analytics_collection.insert_one({
            "user_id": user_id,
            "activity": activity,
            "details": details,
            "timestamp": datetime.now()
        })
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

def add_or_update_user(user):
    """Add new user or update existing user info."""
    try:
        user_data = {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code,
            "last_active": datetime.now()
        }
        
        users_collection.update_one(
            {"user_id": user.id},
            {"$set": user_data, "$setOnInsert": {"joined_date": datetime.now()}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to add/update user: {e}")
        return False

# Flask app for webhook
app = Flask(__name__)

# Bot application
bot_application = None

def init_bot():
    """Initialize bot application."""
    global bot_application
    try:
        bot_application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        bot_application.add_handler(CommandHandler("start", start_command))
        bot_application.add_handler(CommandHandler("help", help_command))
        bot_application.add_handler(CommandHandler("stats", stats_command))
        bot_application.add_handler(CommandHandler("broadcast", broadcast_command))
        bot_application.add_handler(CommandHandler("addmovie", add_movie_command))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Bot application initialized!")
        return True
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        return False

# [Continue with bot handlers...]
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    # Add/update user in database
    add_or_update_user(user)
    log_user_activity(user.id, "start_command")
    
    # Check if new user
    user_doc = users_collection.find_one({"user_id": user.id})
    is_new_user = (datetime.now() - user_doc.get("joined_date", datetime.now())).seconds < 60
    
    # Send admin notification for new users
    if ADMIN_ID and str(user.id) != ADMIN_ID and is_new_user:
        try:
            total_users = users_collection.count_documents({})
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 *New User Alert!* 🎉

"
                     f"👤 Name: {user.full_name}
"
                     f"🔖 Username: @{user.username or 'N/A'}
"
                     f"🆔 ID: `{user.id}`
"
                     f"🌐 Language: {user.language_code or 'N/A'}
"
                     f"👥 Total Users: *{total_users}*",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    # Get active movies from database
    movies = list(movies_collection.find({"active": True}).sort("downloads", -1))
    
    # Create keyboard with movie titles
    keyboard = []
    for movie in movies:
        keyboard.append([movie["title"]])
    
    # Add utility buttons
    keyboard.append(["🔍 Search Movies", "📊 My Stats", "ℹ️ Help"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_message = (
        f"👋 *Welcome {user.first_name}!* 🎬

"
        "🤖 *Doraemon Movies Bot*

"
        "🎯 यहाँ आपको मिलेंगी सबसे बेहतरीन Doraemon movies!

"
        "✨ *Features:*
"
        "🔸 Hindi Dubbed Movies
"
        "🔸 High Quality Downloads
"
        "🔸 Direct Download Links
"
        "🔸 Fast & Free
"
        "🔸 User Statistics
"
        "🔸 Search by Keywords

"
        "📱 *How to use:*
"
        "• Select movie from keyboard
"
        "• Or type movie name to search
"
        "• Click download button

"
        f"🎬 *Available Movies: {len(movies)}*
"
        f"👥 *Total Users: {users_collection.count_documents({})}*

"
        "👇 *Choose a movie from the menu below:*"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

# [Include all other bot handlers here - stats_command, broadcast_command, etc.]

# Flask routes
@app.route('/')
def home():
    """Admin dashboard homepage."""
    try:
        total_users = users_collection.count_documents({})
        total_movies = movies_collection.count_documents({"active": True})
        total_downloads = sum([movie.get("downloads", 0) for movie in movies_collection.find({"active": True})])
        
        dashboard_html = f"""
        <html>
        <head>
            <title>Doraemon Bot Dashboard</title>
            <style>
                body {{ font-family: Arial; background: #111; color: white; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .stat-card {{ background: #222; padding: 20px; border-radius: 10px; text-align: center; }}
                .stat-number {{ font-size: 2em; color: #00bfff; font-weight: bold; }}
                .stat-label {{ color: #999; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Doraemon Movies Bot Dashboard</h1>
                    <p>Admin Panel - Real-time Statistics</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{total_users}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_movies}</div>
                        <div class="stat-label">Active Movies</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_downloads}</div>
                        <div class="stat-label">Total Downloads</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">✅</div>
                        <div class="stat-label">Bot Status</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return dashboard_html
        
    except Exception as e:
        return f"<h1>Dashboard Error: {e}</h1>"

# [Continue with webhook and other routes...]

# Main function
def main():
    """Start the application."""
    logger.info("🚀 Starting Doraemon Movies Telegram Bot with MongoDB...")
    
    # Setup database
    if not setup_database():
        logger.error("❌ Database setup failed. Exiting...")
        return
    
    # Initialize bot
    if not init_bot():
        logger.error("❌ Bot initialization failed. Exiting...")
        return
    
    # Start Flask server
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"✅ Starting Flask server on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()