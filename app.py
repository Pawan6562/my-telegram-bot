# -*- coding: utf-8 -*-

# =====================================================================================
# DORAEMON AI MOVIE BOT - VERSION 2.0
# FEATURES:
# - AI-Powered Movie Search (using Google Gemini)
# - AI-Powered General Chat
# - MongoDB for User Statistics
# - Admin Panel (Stats, Broadcast, Import)
# - Keeps alive on hosting platforms like Render
# =====================================================================================

import os
import asyncio
import google.generativeai as genai
from threading import Thread
from flask import Flask
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import Forbidden

# --- Step 1: Bot Configuration (Aapki details yahaan daalein) ---
# Apne Environment Variables mein yeh details set karein.
# Agar aap local machine par test kar rahe hain, toh "YOUR_..." ki jagah direct value daal sakte hain.
TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID", "YOUR_ADMIN_ID") # Yeh aapki Telegram User ID (number) hai
MONGO_URI = os.environ.get("MONGO_URI", "YOUR_MONGODB_CONNECTION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# --- Step 2: AI Model & Database Setup ---
# Global variables
client, db, users_collection, model = None, None, None, None

def setup_dependencies():
    """AI Model aur MongoDB, dono ko setup karne ka function."""
    global client, db, users_collection, model
    
    # AI Model Setup
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash') # 'gemini-1.5-flash' tez aur sasta hai
        print("✅ Gemini AI Model successfully load ho gaya!")
    except Exception as e:
        print(f"❌ Gemini AI Model load nahi ho paaya. Error: {e}")
        # Agar AI load na ho toh bot band nahi hoga, bas AI features kaam nahi karenge.
    
    # Database Setup
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database('dorebox_bot') # Aap database ka naam badal sakte hain
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB se successfully connect ho gaya!")
        return True
    except Exception as e:
        print(f"❌ MongoDB se connect nahi ho paaya. Error: {e}")
        return False

# --- Step 3: Movie Data ---
# Aapki sabhi movies ki list
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

# --- Step 4: Flask App (Render ko 'alive' rakhne ke liye) ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot is alive and running!"

# --- Step 5: Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handle karta hai."""
    user = update.effective_user
    try:
        if users_collection and not users_collection.find_one({"user_id": user.id}):
            users_collection.insert_one({"user_id": user.id, "name": user.full_name, "username": user.username})
            if ADMIN_ID:
                admin_message = (f"🔔 New User Alert! 🔔\n\n"
                                 f"Name: {user.full_name}\n"
                                 f"Username: @{user.username if user.username else 'N/A'}\n"
                                 f"Telegram ID: `{user.id}`")
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Start command mein user check karte waqt error: {e}")

    keyboard = [[title] for title in MOVIE_TITLES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, placeholder="Movie select karein ya naam likhein...")
    
    welcome_text = ("👋 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗔𝗜 𝗠𝗼𝘃𝗶𝗲𝘀 𝗕𝗼𝘁!* 🎬💙\n\n"
                    "🚀 𝗬𝗮𝗵𝗮𝗮𝗻 𝗮𝗮𝗽𝗸𝗼 𝗺𝗶𝗹𝘁𝗶 𝗵𝗮𝗶𝗻 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗸𝗶 𝘀𝗮𝗯𝘀𝗲 𝘇𝗮𝗯𝗮𝗿𝗱𝗮𝘀𝘁 𝗺𝗼𝘃𝗶𝗲𝘀, 𝗯𝗶𝗹𝗸𝘂𝗹 𝗲𝗮𝘀𝘆 𝗮𝘂𝗿 𝗳𝗮𝘀𝘁 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗸𝗲 𝘀𝗮𝗮𝘁𝗵।\n\n"
                    "✨ *Ab yeh bot AI se chalta hai!* Aap movie ka naam jaise marzi likh sakte hain ya mujhse normal baat bhi kar sakte hain.\n\n"
                    "👉 *Bas movie ka naam likhiye ya neeche diye gaye menu se select kijiye!* 🍿💙\n\n"
                    "📢 Hamare [𝗗𝗢𝗥𝗔𝗘𝗠𝗢𝗡 𝗠𝗢𝗩𝗜𝗘𝗦](https://t.me/doraemon_all_movies_bycjh) channel ko join karna na bhoolen!")

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ke sabhi text messages ko AI se handle karta hai."""
    user_message = update.message.text

    # Pehle check karo ki user ne keyboard se exact title select kiya hai ya nahi
    exact_match = next((movie for movie in MOVIES_DATA if movie['title'] == user_message), None)
    if exact_match:
        caption = f"🎬 **{exact_match['title']}**\n\n📥 Download from the button below!"
        keyboard = [[InlineKeyboardButton("📥 Download Now", url=exact_match['link'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=exact_match['poster'], caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    # Agar exact match nahi hai, tab AI ka istemal karo
    if not model:
        await update.message.reply_text("Maaf kijiye, AI service abhi kaam nahi kar rahi hai. Aap keyboard se movie select kar sakte hain.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    movie_titles_str = ", ".join(f"'{title}'" for title in MOVIE_TITLES)
    system_prompt = f"""
    Aap ek Doraemon movie expert bot ho. Aapka kaam user ke message ko samajhna aur unhe sahi movie dhoondhne mein madad karna hai.
    Aapke paas yeh movies available hain: {movie_titles_str}.
    Rules:
    1.  Agar user koi movie maang raha hai (jaise "dino wali movie" ya "stand by me 2"), toh uske message ko samajhkar upar di gayi list mein se **sirf aur sirf movie ka EXACT title** output mein do. Aur kuch nahi.
    2.  Agar aapko 100% yakeen nahi hai ki user kaunsi movie maang raha hai, toh jawab do "NO_MOVIE_FOUND".
    3.  Agar user movie nahi maang raha, balki normal baat-cheet kar raha hai (jaise 'hello', 'thank you'), toh usse ek friendly, short, aur helpful response do.
    4.  Apne jawab hamesha Hinglish (Hindi in English script) mein do.
    """
    
    try:
        full_prompt = f"{system_prompt}\n\nUser ka message hai: '{user_message}'"
        response = await model.generate_content_async(full_prompt)
        ai_response_text = response.text.strip().replace("'", "")

        found_movie = next((movie for movie in MOVIES_DATA if movie['title'] == ai_response_text), None)

        if found_movie:
            caption = f"🎬 **{found_movie['title']}**\n\n✅ AI ko lagta hai aap yeh movie dhoondh rahe hain!"
            keyboard = [[InlineKeyboardButton("📥 Download Now", url=found_movie['link'])]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_photo(photo=found_movie['poster'], caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        elif "NO_MOVIE_FOUND" in ai_response_text:
            await update.message.reply_text("🤔 Maaf kijiye, main samajh nahi paaya ki aap kaunsi movie dhoondh rahe hain. Kya aap keyboard se select kar sakte hain ya thoda alag tarike se likh sakte hain?")
        else:
            await update.message.reply_text(ai_response_text)
    except Exception as e:
        print(f"AI handler mein error: {e}")
        await update.message.reply_text("Kuch takneeki samasya aa gayi hai. Kripya thodi der baad koshish karein.")

# --- Admin Commands ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID: return
    if not users_collection:
        await update.message.reply_text("Database se connection nahi hai.")
        return
    try:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(f"📊 *Bot Statistics*\n\nTotal Unique Users: *{total_users}*", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Stats fetch karte waqt error: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID: return
    if not users_collection:
        await update.message.reply_text("Database se connection nahi hai.")
        return

    message_to_broadcast = " ".join(context.args)
    if not message_to_broadcast:
        await update.message.reply_text("Example: `/broadcast Hello everyone!`")
        return

    user_ids = [user["user_id"] for user in users_collection.find({}, {"user_id": 1})]
    if not user_ids:
        await update.message.reply_text("Database mein koi user nahi hai.")
        return

    await update.message.reply_text(f"📢 Broadcast shuru ho raha hai {len(user_ids)} users ke liye...")
    success_count, fail_count = 0, 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_broadcast, parse_mode=ParseMode.MARKDOWN)
            success_count += 1
        except Forbidden: fail_count += 1
        except Exception: fail_count += 1
        await asyncio.sleep(0.1)
    await update.message.reply_text(f"✅ Broadcast Complete!\n\nSent: {success_count}\nFailed: {fail_count}")

# --- Step 6: Main Function ---
def main():
    """Bot ko start aur run karne wala main function."""
    if "YOUR_" in TOKEN or "YOUR_" in ADMIN_ID or "YOUR_" in MONGO_URI or "YOUR_" in GEMINI_API_KEY:
        print("❌ Error: Zaroori variables (TOKEN, ADMIN_ID, MONGO_URI, GEMINI_API_KEY) set nahi hain!")
        return

    if not setup_dependencies():
        print("❌ Database setup fail ho gaya. Bot band ho raha hai.")
        return

    port = int(os.environ.get('PORT', 8080))
    flask_thread = Thread(target=lambda: flask_app.run(host='0.0.0.0', port=port, debug=False))
    flask_thread.start()
    print(f"✅ Flask server port {port} par shuru ho raha hai...")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_handler))

    print("✅ Bot polling shuru ho gaya hai...")
    application.run_polling()

if __name__ == '__main__':
    main()