# -*- coding: utf-8 -*-

# =====================================================================================
# DORAEMON AI MOVIE BOT - VERSION 2.2 (FINAL & COMPLETE)
# FEATURES:
# - AI-Powered Search using OpenRouter (Gemma Model)
# - AI-Powered General Chat
# - MongoDB for User Statistics
# - Admin Panel (Stats)
# - Keeps alive on hosting platforms like Choreo
# =====================================================================================

import os
import asyncio
from openai import OpenAI
from threading import Thread
from flask import Flask
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import Forbidden

# --- Configuration: Apni details Environment Variables mein set karein ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Optional: Aapki site ka naam OpenRouter par ranking ke liye
YOUR_SITE_URL = "https://t.me/doraemon_all_movies_bycjh" # Aapke bot ya channel ka link
YOUR_SITE_NAME = "Doraemon AI Bot" # Aapke project ka naam

# --- Global Variables ---
db_client, db, users_collection, ai_client = None, None, None, None

def setup_dependencies():
    """AI Client aur MongoDB, dono ko setup karne ka function."""
    global db_client, db, users_collection, ai_client
    
    # AI Client Setup (OpenRouter ke liye)
    try:
        ai_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        print("✅ OpenRouter AI Client successfully load ho gaya!")
    except Exception as e:
        print(f"❌ OpenRouter AI Client load nahi ho paaya. Error: {e}")
    
    # Database Setup
    try:
        db_client = MongoClient(MONGO_URI)
        db = db_client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB se successfully connect ho gaya!")
        return True
    except Exception as e:
        print(f"❌ MongoDB se connect nahi ho paaya. Error: {e}")
        return False

# --- Movie Data (Poori List) ---
MOVIES_DATA = [
    {"title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz", "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png", "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen"},
    {"title": "Doraemon Jadoo Mantar Aur Jahnoom", "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom"},
    {"title": "Doraemon Dinosaur Yoddha", "poster": "https://i.postimg.cc/3w83qTtr/Doraemon-The-Movie-Dinosaur-Yoddhha-Hindi-Tamil-Telugu-Download-FHD-990x557.jpg", "link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha"},
    {"title": "Doraemon Nobita and the Underwater Adventure", "poster": "https://i.postimg.cc/yYLjw5Pn/Doraemon-The-Movie-Nobita.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20and%20the%20Underwater%20Adventure"},
    {"title": "Doraemon Ichi Mera Dost (Yeh Bhi Tha Nobita)", "poster": "https://i.postimg.cc/mrQ7v7Qd/Doraemon-nobita-and-the-legend-of-sun-king-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Legend%20of%20Sun%20King"},
    {"title": "Doraemon Nobita Dorabian Nights", "poster": "https://iili.io/KqRfWdv.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Dorabian%20Nights"},
    {"title": "Doraemon Nobita Chala Chand Pe", "poster": "https://i.postimg.cc/BbmtZs0X/m3.jpg", "link": "https://dorebox.vercel.app/download.html?title=Chronicle%20of%20the%20Moon"},
    {"title": "Doraemon Nobita Ka Aasmaani Utopia", "poster": "https://i.postimg.cc/Nf3QTNXq/doraemon-movie-nobitas-sky-utopia-in-hindi.jpg", "link": "https://dorebox.vercel.app/download.html?title=Sky%20Utopia"},
    {"title": "Doraemon Nobita Chal Pada Antarctica", "poster": "https://iili.io/Kx9Qifn.jpg", "link": "https://dorebox.vercel.app/download.html?title=Antarctic%20Adventure"},
    {"title": "Doraemon Nobita and the New Steel Troops – Winged Angels", "poster": "https://i.postimg.cc/43C9KJr0/Doraemon-The-Movie-Nobita-and-the-Steel-Troops.jpg", "link": "https://dorebox.vercel.app/download.html?title=Steel%20Troops%20%E2%80%93%20New%20Age"},
    {"title": "Stand by Me Doraemon", "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201"},
    {"title": "Stand by Me Doraemon 2", "poster": "https://i.postimg.cc/y8wkR4PJ/Doraemon-The-Movie-Stand-by-Me-2-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202"},
    {"title": "Doraemon Nobita’s Treasure Island", "poster": "https://i.postimg.cc/t46rgZ36/Doraemon-the-Nobita-s-Treasure-Island-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Treasure%20Island"},
    {"title": "Doraemon The Explorer Bow! Bow!", "poster": "https://i.postimg.cc/HxY336f0/The-Movie-Nobita-The-Explorer-Bow-Bow-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20The%20Explorer%20Bow%20Bow"},
    {"title": "Doraemon Nobita in Jannat No.1", "poster": "https://iili.io/KzFgEog.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20In%20Jannat%20No%201"},
    {"title": "Doraemon Nobita and the Birth of Japan", "poster": "https://i.postimg.cc/MKqNrP7Q/Doraemon-The-Movie-Nobita-and-the-birth-of-Japan.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20nobita%20and%20the%20Birthday%20of%20japan"},
    {"title": "Doraemon Nobita and the Galaxy Super Express", "poster": "https://i.postimg.cc/XY6fQ25Z/Doraemon-The-Movie-Galaxy-Super-Express-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Galaxy%20Super%20Express%20Hindi"},
    {"title": "Doraemon: Nobita’s Great Adventure to the South Seas", "poster": "https://i.postimg.cc/8zC06x5V/Nobita-Great-Adventure-to-the-South-Seas-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Great%20Adventure%20in%20the%20South%20Seas"},
    {"title": "Doraemon Nobita Aur Jadooi Tapu", "poster": "https://i.postimg.cc/yd8X0kZv/Doraemon-The-Movie-Nobita-Aur-Jadooi-Tapu-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Island%20of%20Miracle"},
    {"title": "Doraemon Toofani Adventure", "poster": "https://i.postimg.cc/bYFLHHLb/Doraemon-Toofani-Adventure-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Windmasters"},
    {"title": "Doraemon Nobita Bana Superhero", "poster": "https://i.postimg.cc/prbYFGHC/Doraemon-Nobita-Bana-Superhero-Hindi-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Parallel%20Visit%20to%20West"},
    {"title": "Doraemon Nobita and the Kingdom of Robot Singham", "poster": "https://i.postimg.cc/j5fNHPj6/The-Movie-Nobita-and-the-Kingdom-of-Robot-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20And%20The%20Kingdom%20Of%20Robot%20Singham"},
    {"title": "Doraemon Nobita Aur Birdopia Ka Sultan", "poster": "https://i.postimg.cc/hjVgbtRQ/Doraemon-The-Movie-Nobita-Aur-Birdopia-Ka-Sultan.jpg", "link": "https://dorebox.vercel.app/download.html?title=Birdopia%20Ka%20Sultan"},
    {"title": "Doraemon Nobita in Gol Gol Golmaal (Spiral City)", "poster": "https://iili.io/KTEEtjI.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Spiral%20City"}
]
MOVIE_TITLES = [movie["title"] for movie in MOVIES_DATA]

# --- Flask App (Bot ko zinda rakhne ke liye) ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot is alive and running!"

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command ko handle karta hai."""
    user = update.effective_user
    try:
        if users_collection and not users_collection.find_one({"user_id": user.id}):
            users_collection.insert_one({"user_id": user.id, "name": user.full_name, "username": user.username})
            if ADMIN_ID:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 New User: {user.full_name} (@{user.username})")
    except Exception as e:
        print(f"Start command mein error: {e}")

    keyboard = [[title] for title in MOVIE_TITLES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, placeholder="Movie select karein ya naam likhein...")
    welcome_text = ("👋 *Welcome to Doraemon AI Bot (OpenRouter Edition)!* 🎬\n\n"
                    "Aap movie ka naam likh sakte hain ya mujhse normal baat bhi kar sakte hain.")
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ke sabhi text messages ko OpenRouter AI se handle karta hai."""
    user_message = update.message.text
    
    exact_match = next((movie for movie in MOVIES_DATA if movie['title'] == user_message), None)
    if exact_match:
        caption = f"🎬 **{exact_match['title']}**\n\n📥 Download from the button below!"
        keyboard = [[InlineKeyboardButton("📥 Download Now", url=exact_match['link'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=exact_match['poster'], caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    if not ai_client:
        await update.message.reply_text("Maaf kijiye, AI service abhi kaam nahi kar rahi hai.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    movie_titles_str = ", ".join(f"'{title}'" for title in MOVIE_TITLES)
    system_prompt = f"""
    Aap ek Doraemon movie expert bot ho. Aapka kaam user ke message ko samajhna hai.
    Aapke paas yeh movies available hain: {movie_titles_str}.
    Rules:
    1. Agar user movie maang raha hai, toh upar di gayi list mein se sirf movie ka EXACT title output mein do. Aur kuch nahi.
    2. Agar movie nahi mili, toh jawab do "NO_MOVIE_FOUND".
    3. Agar user normal baat kar raha hai, toh usse ek friendly, short, aur helpful Hinglish mein jawab do.
    """
    
    try:
        completion = ai_client.chat.completions.create(
            extra_headers={"HTTP-Referer": YOUR_SITE_URL, "X-Title": YOUR_SITE_NAME},
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
        )
        ai_response_text = completion.choices[0].message.content.strip().replace("'", "")

        found_movie = next((movie for movie in MOVIES_DATA if movie['title'] == ai_response_text), None)

        if found_movie:
            caption = f"🎬 **{found_movie['title']}**\n\n✅ AI ko lagta hai aap yeh movie dhoondh rahe hain!"
            keyboard = [[InlineKeyboardButton("📥 Download Now", url=found_movie['link'])]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_photo(photo=found_movie['poster'], caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        elif "NO_MOVIE_FOUND" in ai_response_text:
            await update.message.reply_text("🤔 Maaf kijiye, main samajh nahi paaya ki aap kaunsi movie dhoondh rahe hain.")
        else:
            await update.message.reply_text(ai_response_text)
    except Exception as e:
        print(f"AI handler mein error: {e}")
        await update.message.reply_text("Kuch takneeki samasya aa gayi hai.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin ke liye stats command."""
    if str(update.effective_user.id) != ADMIN_ID: return
    if not users_collection: return await update.message.reply_text("DB not connected.")
    total_users = users_collection.count_documents({})
    await update.message.reply_text(f"📊 Total Users: *{total_users}*", parse_mode=ParseMode.MARKDOWN)

# --- Main Function ---
def main():
    """Bot ko start aur run karne wala main function."""
    if not all([TOKEN, ADMIN_ID, MONGO_URI, OPENROUTER_API_KEY]):
        print("❌ Error: Zaroori Environment Variables set nahi hain!")
        return

    if not setup_dependencies():
        print("❌ Bot band ho raha hai kyunki dependencies setup nahi ho paayin.")
        return

    port = int(os.environ.get('PORT', 8080))
    flask_thread = Thread(target=lambda: flask_app.run(host='0.0.0.0', port=port, debug=False))
    flask_thread.start()
    print(f"✅ Flask server port {port} par shuru ho raha hai...")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_handler))

    print("✅ Bot polling shuru ho gaya hai...")
    application.run_polling()

if __name__ == '__main__':
    main()