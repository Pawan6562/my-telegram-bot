import os
import asyncio
from flask import Flask, request
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- Environment & Database ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")

# Global variables for database connection
client = None
db = None
users_collection = None

def setup_database():
    """Database connection ko setup karta hai."""
    global client, db, users_collection
    # Agar pehle se connected hai, toh dobara na karein
    if db:
        return True
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB se successfully connect ho gaya!")
        return True
    except Exception as e:
        print(f"❌ MongoDB se connect nahi ho paaya. Error: {e}")
        return False

# --- Vercel ke liye Flask App ---
app = Flask(__name__)

# --- Telegram Application Object ---
# Application ko global scope mein banayein
application = Application.builder().token(TOKEN).build()

# --- Movie Data ---
MOVIES_DATA = [
    {"title": "Doraemon jadoo Mantar aur jhanoom", "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom"},
    {"title": "Dinosaur Yodha", "poster": "https://i.postimg.cc/3w83qTtr/Doraemon-The-Movie-Dinosaur-Yoddhha-Hindi-Tamil-Telugu-Download-FHD-990x557.jpg", "link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha"},
    {"title": "Doraemon The Movie Nobita and the Underwater Adventure", "poster": "https://i.postimg.cc/yYLjw5Pn/Doraemon-The-Movie-Nobita.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20and%20the%20Underwater%20Adventure"},
    {"title": "ICHI MERA DOST", "poster": "https://i.postimg.cc/xjpCppDL/Doraemon-The-Movie-Nobita-in-Ichi-Mera-Dost-Hindi.png", "link": "https://dorebox.vercel.app/download.html?title=ICHI%20MERA%20DOST"},
    {"title": "Doraemon Nobita's Dorabian Nights", "poster": "https://iili.io/KqRfWdv.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Dorabian%20Nights"},
    {"title": "Chronicle of the Moon", "poster": "https://i.postimg.cc/BbmtZs0X/m3.jpg", "link": "https://dorebox.vercel.app/download.html?title=Chronicle%20of%20the%20Moon"},
    {"title": "Sky Utopia", "poster": "https://i.postimg.cc/Nf3QTNXq/doraemon-movie-nobitas-sky-utopia-in-hindi.jpg", "link": "https://dorebox.vercel.app/download.html?title=Sky%20Utopia"},
    {"title": "Antarctic Adventure", "poster": "https://iili.io/Kx9Qifn.jpg", "link": "https://dorebox.vercel.app/download.html?title=Antarctic%20Adventure"},
    {"title": "Steel Troops – New Age", "poster": "https://i.postimg.cc/43C9KJr0/Doraemon-The-Movie-Nobita-and-the-Steel-Troops.jpg", "link": "https://dorebox.vercel.app/download.html?title=Steel%20Troops%20%E2%80%93%20New%20Age"},
    {"title": "Stand by Me – Part 2", "poster": "https://i.postimg.cc/y8wkR4PJ/Doraemon-The-Movie-Stand-by-Me-2-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202"},
    {"title": "Doraemon Nobita's Treasure Island", "poster": "https://i.postimg.cc/t46rgZ36/Doraemon-the-Nobita-s-Treasure-Island-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Treasure%20Island"},
    {"title": "Doraemon The Movie Nobita The Explorer Bow Bow", "poster": "https://i.postimg.cc/HxY336f0/The-Movie-Nobita-The-Explorer-Bow-Bow-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20The%20Explorer%20Bow%20Bow"},
    {"title": "Doraemon The Movie Nobita In Jannat No 1", "poster": "https://iili.io/KzFgEog.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20In%20Jannat%20No%201"}
]
MOVIE_TITLES = [movie["title"] for movie in MOVIES_DATA]
MOVIE_DICT = {movie["title"]: movie for movie in MOVIES_DATA}

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        if not users_collection.find_one({"user_id": user.id}):
            users_collection.insert_one({"user_id": user.id, "name": user.full_name, "username": user.username})
            if ADMIN_ID:
                admin_message = (f"🔔 New User: {user.full_name} (@{user.username if user.username else 'N/A'})")
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    except Exception as e:
        print(f"Error in start command: {e}")
    keyboard = [[title] for title in MOVIE_TITLES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    welcome_text = "👋 *Welcome to Doraemon Movies Bot!* 🎬\n\n👇 Neeche diye gaye menu se apni pasand ki movie select kijiye."
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def movie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_data = MOVIE_DICT.get(update.message.text)
    if movie_data:
        caption = f"🎬 **{movie_data['title']}**\n\n📥 Download from the button below!"
        keyboard = [[InlineKeyboardButton("📥 Download Now", url=movie_data['link'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=movie_data['poster'], caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# --- Admin Commands ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID: return
    try:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(f"📊 *Bot Statistics*\n\nTotal Users: *{total_users}*", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Error fetching stats: {e}")

# (Broadcast aur Import functions ko abhi ke liye hata diya hai, kyunki woh Vercel ke 30s timeout mein problem kar sakte hain)
# Hum unhe baad mein alag tarike se add kar sakte hain.

# --- Handlers ko Application se Jodein ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_handler))

# --- Webhook Endpoint (Vercel ka main entry point) ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['POST'])
def webhook(path):
    # Har request par DB connection check karein
    if not setup_database():
        return "Database connection failed", 500

    # Asynchronously update ko process karein
    async def process_update():
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)

    # Ek naya event loop banayein aur usmein task run karein
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_update())
    
    return 'ok'

# Yeh line zaroori hai taaki app start hote hi DB connect ho jaaye
setup_database()
