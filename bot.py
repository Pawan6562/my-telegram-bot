# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import requests
from threading import Thread
import json

# --- Logging Configuration ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Your Render app URL

# Validate required environment variables
if not all([TOKEN, ADMIN_ID, MONGO_URI]):
    logger.error("❌ Missing required environment variables: TOKEN, ADMIN_ID, MONGO_URI")
    exit(1)

# --- Database Setup ---
client = None
db = None
users_collection = None

def setup_database():
    """Setup MongoDB connection and collections."""
    global client, db, users_collection
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.server_info()
        
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        
        logger.info("✅ MongoDB connected successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False

# --- Movie Data ---
MOVIES_DATA = [
    {
        "title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz",
        "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
        "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen",
        "keywords": ["three", "3", "teen", "visionary", "drishti", "dristi", "swordsmen", "swords", "talwarbaaz", "talwar", "sword", "teen swordsmen", "visionary swordsmen", "sword wali", "talwar wali"]
    },
    {
        "title": "Doraemon Jadoo Mantar Aur Jahnoom",
        "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom",
        "keywords": ["jadoo", "jadu", "jaadu", "mantar", "mantra", "magic", "jahnoom", "jhanoom", "jahanum", "jahanam", "jahnum", "underworld", "under world", "jadu wali", "mantar wali", "jahnoom wali", "magic wali"]
    },
    {
        "title": "Doraemon Dinosaur Yoddha",
        "poster": "https://i.postimg.cc/3w83qTtr/Doraemon-The-Movie-Dinosaur-Yoddhha-Hindi-Tamil-Telugu-Download-FHD-990x557.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha",
        "keywords": ["dinosaur", "dinasor", "dinasour", "dino", "yodha", "yoddha", "yodhha", "dino wali", "dinosaur wali", "yodha wali", "knight", "knights", "dino knight"]
    },
    {
        "title": "Doraemon Nobita and the Underwater Adventure",
        "poster": "https://i.postimg.cc/yYLjw5Pn/Doraemon-The-Movie-Nobita.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20and%20the%20Underwater%20Adventure",
        "keywords": ["underwater", "under water", "undersea", "sea", "samundar", "adventure", "devil", "undersea devil", "samundar wali", "sea wali", "underwater wali", "under water wali"]
    },
    {
        "title": "Doraemon Ichi Mera Dost (Yeh Bhi Tha Nobita)",
        "poster": "https://i.postimg.cc/mrQ7v7Qd/Doraemon-nobita-and-the-legend-of-sun-king-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Legend%20of%20Sun%20King",
        "keywords": ["ichi", "icchi", "ichhi", "mera dost", "dost", "dost wali", "ichi dost", "ichi wali", "yeh bhi nobita", "woh bhi nobita", "yeh nobita", "wo nobita", "ye nobita", "wo bhi nobita", "nobita double", "two nobita", "twin nobita", "do nobita", "nobita twins", "double nobita movie", "sun king", "legend of sun king"]
    },
    {
        "title": "Doraemon Nobita Dorabian Nights",
        "poster": "https://iili.io/KqRfWdv.png",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Dorabian%20Nights",
        "keywords": ["dorabian", "dorabiyan", "dorabiya", "night", "nights", "dorabian night", "dorabian nights", "arabian", "arabiya", "arab wali", "raat wali", "dorabian wali"]
    },
    {
        "title": "Doraemon Nobita Chala Chand Pe",
        "poster": "https://i.postimg.cc/BbmtZs0X/m3.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Chronicle%20of%20the%20Moon",
        "keywords": ["chaand", "chala", "challa", "chalaa", "chand", "chand pe", "chala chand", "chala chand pe", "moon", "moon exploration", "moon wali", "chronicle", "chronicle moon", "moon chronicle", "chand wali", "moon wali movie"]
    },
    {
        "title": "Doraemon Nobita Ka Aasmaani Utopia",
        "poster": "https://i.postimg.cc/Nf3QTNXq/doraemon-movie-nobitas-sky-utopia-in-hindi.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Sky%20Utopia",
        "keywords": ["sky", "sky utopia", "skyutopia", "asmaan", "aasmaan", "utopia", "utopya", "ypytopia", "sky wali", "utopia wali", "aasmaan wali", "nobita sky", "nobita utopia"]
    },
    {
        "title": "Doraemon Nobita Chal Pada Antarctica",
        "poster": "https://iili.io/Kx9Qifn.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Antarctic%20Adventure",
        "keywords": ["antarctica", "antartica", "antarktika", "antarc", "kachi kochi", "kochi", "thand", "baraf", "snow", "ice", "icy", "antarctica wali", "baraf wali", "thand wali", "snow wali", "adventure antarctica", "ice wali movie"]
    },
    {
        "title": "Doraemon Nobita and the New Steel Troops – Winged Angels",
        "poster": "https://i.postimg.cc/43C9KJr0/Doraemon-The-Movie-Nobita-and-the-Steel-Troops.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Steel%20Troops%20%E2%80%93%20New%20Age",
        "keywords": ["steel", "steel troop", "steel troops", "trops", "robot", "robo", "robotic", "wing", "wings", "winged", "winged angel", "angels", "steel wali", "robot wali", "troop wali", "angel wali"]
    },
    {
        "title": "Stand by Me Doraemon",
        "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201",
        "keywords": ["stand by me", "stand byme", "standby me", "standbyme", "stand 1", "part 1", "first part", "1st part", "stand wali", "3d wali", "3d movie", "doraemon stand", "stand movie"]
    },
    {
        "title": "Stand by Me Doraemon 2",
        "poster": "https://i.postimg.cc/y8wkR4PJ/Doraemon-The-Movie-Stand-by-Me-2-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202",
        "keywords": ["stand by me 2", "stand byme 2", "standby me 2", "standbyme2", "stand by me part 2", "part 2", "2nd part", "sequel", "stand 2", "stand wali 2", "3d 2", "3d movie 2", "doraemon stand 2", "stand wali second"]
    },
    {
        "title": "Doraemon Nobita's Treasure Island",
        "poster": "https://i.postimg.cc/t46rgZ36/Doraemon-the-Nobita-s-Treasure-Island-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Treasure%20Island",
        "keywords": ["treasure", "treasure island", "trezor", "treashure", "island", "island wali", "island movie", "nobita treasure", "nobita island", "nobita wali", "treasure wali", "treasure movie"]
    },
    {
        "title": "Doraemon The Explorer Bow! Bow!",
        "poster": "https://i.postimg.cc/HxY336f0/The-Movie-Nobita-The-Explorer-Bow-Bow-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20The%20Explorer%20Bow%20Bow",
        "keywords": ["explorer", "explore", "exploring", "bow bow", "bowbow", "bow-bow", "adventure", "explorer wali", "adventure wali", "doraemon explorer", "bow bow wali"]
    },
    {
        "title": "Doraemon Nobita in Jannat No.1",
        "poster": "https://iili.io/KzFgEog.png",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20In%20Jannat%20No%201",
        "keywords": ["jannat", "jannat no 1", "jannat no ek", "jannat1", "heaven", "no1", "number 1", "first", "jannat wali", "no1 wali", "heaven wali", "nobita jannat", "nobita wali"]
    },
    {
        "title": "Doraemon Nobita and the Birth of Japan",
        "poster": "https://i.postimg.cc/MKqNrP7Q/Doraemon-The-Movie-Nobita-and-the-birth-of-Japan.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20nobita%20and%20the%20Birthday%20of%20japan",
        "keywords": ["birth of japan", "birthday of japan", "janam japan", "janm japan", "japan", "japanese", "japan wali", "janam wali", "janm wali", "janam japan movie", "birth wali", "japan birth", "japan movie"]
    },
    {
        "title": "Doraemon Nobita and the Galaxy Super Express",
        "poster": "https://i.postimg.cc/XY6fQ25Z/Doraemon-The-Movie-Galaxy-Super-Express-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Galaxy%20Super%20Express%20Hindi",
        "keywords": ["galaxy super express", "galaxy express", "galaxy train", "super express doraemon", "galaxy wali movie", "train space movie", "space train", "galaxy wali doraemon", "super express wali", "galaxy express movie"]
    },
    {
        "title": "Doraemon: Nobita's Great Adventure to the South Seas",
        "poster": "https://i.postimg.cc/8zC06x5V/Nobita-Great-Adventure-to-the-South-Seas-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Great%20Adventure%20in%20the%20South%20Seas",
        "keywords": ["south seas", "south sea", "south see", "south c", "souths", "south", "great adventure", "great adventures", "grate adventure", "samundar", "samundar wali", "samundar ka", "samandar", "pirates", "samundari", "sea adventure", "samundar adventure", "doraemon south sea", "doraemon south seas"]
    },
    {
        "title": "Doraemon Nobita Aur Jadooi Tapu",
        "poster": "https://i.postimg.cc/yd8X0kZv/Doraemon-The-Movie-Nobita-Aur-Jadooi-Tapu-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Island%20of%20Miracle",
        "keywords": ["jadooi tapu", "jadoi tapu", "jadui tapu", "jadui island", "magic island", "jadui adventure", "jadoo tapu", "magic tapu", "jadui doraemon", "magic wali movie", "island magic", "tapu movie"]
    },
    {
        "title": "Doraemon Toofani Adventure",
        "poster": "https://i.postimg.cc/bYFLHHLb/Doraemon-Toofani-Adventure-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Windmasters",
        "keywords": ["toofani adventure", "tofani adventure", "tufani adventure", "tufan adventure", "storm adventure", "hawa adventure", "aandhi adventure", "toofan movie", "tufani movie", "storm wali movie"]
    },
    {
        "title": "Doraemon Nobita Bana Superhero",
        "poster": "https://i.postimg.cc/prbYFGHC/Doraemon-Nobita-Bana-Superhero-Hindi-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Parallel%20Visit%20to%20West",
        "keywords": ["bana superhero", "super hero", "superhero", "nobita superhero", "super hero movie", "hero movie", "nobita hero", "hero wala movie", "superhero wala movie"]
    },
    {
        "title": "Doraemon Nobita and the Kingdom of Robot Singham",
        "poster": "https://i.postimg.cc/j5fNHPj6/The-Movie-Nobita-and-the-Kingdom-of-Robot-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20And%20The%20Kingdom%20Of%20Robot%20Singham",
        "keywords": ["robot singham", "robot kingdom", "robo singham", "robo kingdom", "robot movie", "robot wali movie", "robot adventure", "robo adventure", "robot raj", "robot king", "robo king"]
    },
    {
        "title": "Doraemon Nobita Aur Birdopia Ka Sultan",
        "poster": "https://i.postimg.cc/hjVgbtRQ/Doraemon-The-Movie-Nobita-Aur-Birdopia-Ka-Sultan.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Birdopia%20Ka%20Sultan",
        "keywords": ["birdopia", "birdopia sultan", "bird sultan", "bird king", "bird land", "bird movie", "birds movie", "flying bird", "bird adventure", "pakshi sultan", "pakshi movie"]
    },
    {
        "title": "Doraemon Nobita in Gol Gol Golmaal (Spiral City)",
        "poster": "https://iili.io/KTEEtjI.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Spiral%20City",
        "keywords": ["spiral city", "gol gol golmaal", "golmaal", "gol gol", "gol city", "golmaal city", "round city", "gol gol movie", "gol ghumar", "ghumar city", "gol ghumne wali movie"]
    }
]

MOVIE_TITLES = [movie["title"] for movie in MOVIES_DATA]

# --- Flask App ---
app = Flask(__name__)
bot_application = None

# --- Initialize Bot Application ---
def init_bot():
    """Initialize the bot application."""
    global bot_application
    try:
        bot_application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        bot_application.add_handler(CommandHandler("start", start))
        bot_application.add_handler(CommandHandler("stats", stats))
        bot_application.add_handler(CommandHandler("broadcast", broadcast))
        bot_application.add_handler(CommandHandler("import", import_users))
        bot_application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_handler))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_search_handler))
        
        logger.info("✅ Bot application initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        return False

# --- Bot Handler Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handler."""
    user = update.effective_user
    user_id = user.id
    
    try:
        # Add user to database if not exists
        if not users_collection.find_one({"user_id": user_id}):
            users_collection.insert_one({
                "user_id": user_id, 
                "name": user.full_name, 
                "username": user.username
            })
            
            # Notify admin of new user
            if ADMIN_ID:
                admin_message = (
                    f"🔔 New User Alert! 🔔

"
                    f"Name: {user.full_name}
"
                    f"Username: @{user.username if user.username else 'N/A'}
"
                    f"Telegram ID: `{user_id}`"
                )
                await context.bot.send_message(
                    chat_id=ADMIN_ID, 
                    text=admin_message, 
                    parse_mode=ParseMode.MARKDOWN
                )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

    # Create keyboard
    keyboard = [[title] for title in MOVIE_TITLES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        "👋 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲𝘀 𝗕𝗼𝘁!* 🎬💙

"
        "🚀 𝗬𝗮𝗵𝗮𝗮𝗻 𝗮𝗮𝗽𝗸𝗼 𝗺𝗶𝗹𝘁𝗶 𝗵𝗮𝗶𝗻 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗸𝗶 𝘀𝗮𝗯𝘀𝗲 𝘇𝗮𝗯𝗮𝗿𝗱𝗮𝘀𝘁 𝗺𝗼𝘃𝗶𝗲𝘀, 𝗯𝗶𝗹𝗸𝘂𝗹 𝗲𝗮𝘀𝘆 𝗮𝘂𝗿 𝗳𝗮𝘀𝘁 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗸𝗲 𝘀𝗮𝗮𝘁𝗵।

"
        "✨ *𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:*
"
        "🔹 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗛𝗶𝗻𝗱𝗶 𝗗𝘂𝗯𝗯𝗲𝗱 𝗠𝗼𝘃𝗶𝗲𝘀 (𝗢𝗹𝗱 + 𝗟𝗮𝘁𝗲𝘀𝘁)
"
        "🔹 𝗠𝘂𝗹𝘁𝗶-𝗤𝘂𝗮𝗹𝗶𝘁𝘆 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝘀: 𝟭𝟬𝟴𝟬𝗽 | 𝟳𝟮𝟬𝗽 | 𝟯𝟲𝟬𝗽 🎥
"
        "🔹 𝗗𝗶𝗿𝗲𝗰𝘁 & 𝗙𝗮𝘀𝘁 𝗟𝗶𝗻𝗸𝘀 – 𝗻𝗼 𝘁𝗶𝗺𝗲 𝘄𝗮𝘀𝘁𝗲!
"
        "🔹 𝗥𝗲𝗴𝘂𝗹𝗮𝗿 𝗠𝗼𝘃𝗶𝗲 𝗨𝗽𝗱𝗮𝘁𝗲𝘀

"
        "👉 *𝗕𝗮𝘀 𝗺𝗼𝘃𝗶𝗲 𝗰𝗵𝗼𝗼𝘀𝗲 𝗸𝗶𝗷𝗶𝘆𝗲, 𝗮𝗽𝗻𝗶 𝗽𝗮𝘀𝗮𝗻𝗱 𝗸𝗶 𝗾𝘂𝗮𝗹𝗶𝘁𝘆 𝘀𝗲𝗹𝗲𝗰𝘁 𝗸𝗶𝗷𝗶𝘆𝗲 𝗮𝘂𝗿 𝗲𝗻𝗷𝗼𝘆 𝗸𝗶𝗷𝗶𝘆𝗲 𝗮𝗽𝗻𝗮 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲 𝗧𝗶𝗺𝗲!* 🍿💙

"
        "📢 𝗛𝗮𝗺𝗮𝗿𝗲 [𝗗𝗢𝗥𝗔𝗘𝗠𝗢𝗡 𝗠𝗢𝗩𝗜𝗘𝗦](https://t.me/doraemon_movies_hindi_dubbed) 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗸𝗼 𝗷𝗼𝗶𝗻 𝗸𝗮𝗿𝗻𝗮 𝗻𝗮 𝗯𝗵𝗼𝗼𝗹𝗲𝗻, 𝘁𝗮𝗮𝗸𝗶 𝗻𝗲𝘄 𝘂𝗽𝗱𝗮𝘁𝗲𝘀 𝗮𝗮𝗽𝗸𝗼 𝘀𝗮𝗯𝘀𝗲 𝗽𝗲𝗵𝗹𝗲 𝗺𝗶𝗹𝘀𝗮𝗸𝗲𝗻! 🚀

"
        "👇 *Neeche diye gaye menu se apni pasand ki movie select kijiye.*"
    )

    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup, 
        parse_mode=ParseMode.MARKDOWN, 
        disable_web_page_preview=True
    )

async def movie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle movie selection from keyboard."""
    movie_title = update.message.text
    movie_data = next((movie for movie in MOVIES_DATA if movie['title'] == movie_title), None)

    if movie_data:
        caption = f"🎬 **{movie_data['title']}**

📥 Download from the button below!"
        keyboard = [[InlineKeyboardButton("📥 Download Now", url=movie_data['link'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=movie_data['poster'],
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

async def keyword_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle keyword-based movie search."""
    user_message = update.message.text.lower()

    for movie in MOVIES_DATA:
        if any(keyword.lower() in user_message for keyword in movie.get("keywords", [])):
            caption = f"🎬 **{movie['title']}**

🔎 Mujhe lagta hai aap yeh movie dhoondh rahe the!"
            keyboard = [[InlineKeyboardButton("📥 Download Now", url=movie['link'])]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_photo(
                photo=movie['poster'],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats command (admin only)."""
    if str(update.effective_user.id) != ADMIN_ID:
        return
    
    try:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(
            f"📊 *Bot Statistics*

Total Unique Users: *{total_users}*", 
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(f"Stats fetch karte waqt error: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/broadcast command (admin only)."""
    if str(update.effective_user.id) != ADMIN_ID:
        return

    message_to_broadcast = " ".join(context.args)
    if not message_to_broadcast:
        await update.message.reply_text(
            "Broadcast karne ke liye message likhein. Example: `/broadcast Hello everyone!`"
        )
        return

    all_users = users_collection.find({}, {"user_id": 1})
    user_ids = [user["user_id"] for user in all_users]

    if not user_ids:
        await update.message.reply_text("Database mein broadcast karne ke liye koi user nahi hai.")
        return

    await update.message.reply_text(f"📢 Broadcast shuru ho raha hai {len(user_ids)} users ke liye...")
    success_count, fail_count = 0, 0

    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id, 
                text=message_to_broadcast, 
                parse_mode=ParseMode.MARKDOWN
            )
            success_count += 1
        except Exception:
            fail_count += 1
        await asyncio.sleep(0.1)  # Rate limiting

    await update.message.reply_text(
        f"✅ Broadcast Complete!

Successfully Sent: {success_count}
Failed to Send: {fail_count}"
    )

async def import_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/import command (admin only)."""
    if str(update.effective_user.id) != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Import karne ke liye User IDs provide karein. Example: `/import 12345 67890`"
        )
        return

    users_to_insert = []
    for user_id_str in context.args:
        try:
            users_to_insert.append({
                "user_id": int(user_id_str), 
                "name": "Imported User", 
                "username": "N/A"
            })
        except ValueError:
            pass

    added_count = 0
    if users_to_insert:
        try:
            result = users_collection.insert_many(users_to_insert, ordered=False)
            added_count = len(result.inserted_ids)
        except errors.BulkWriteError as bwe:
            added_count = bwe.details['nInserted']
        except Exception as e:
            await update.message.reply_text(f"Database mein daalte waqt error: {e}")
            return

    total_users = users_collection.count_documents({})
    await update.message.reply_text(
        f"✅ Import Complete!

Added: {added_count} new users.
"
        f"(Duplicates were ignored.)

📊 Total Users in DB now: {total_users}"
    )

# --- Flask Routes ---
@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        "status": "Bot is running!",
        "message": "Doraemon Movies Bot is alive and healthy."
    })

@app.route('/set_webhook')
def set_webhook():
    """Set up webhook for the bot."""
    if not WEBHOOK_URL:
        return jsonify({"error": "WEBHOOK_URL not configured"}), 400
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    response = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", {
        'url': webhook_url
    })
    
    if response.status_code == 200:
        logger.info(f"✅ Webhook set successfully: {webhook_url}")
        return jsonify({"message": f"Webhook set successfully: {webhook_url}"})
    else:
        logger.error(f"❌ Failed to set webhook: {response.text}")
        return jsonify({"error": "Failed to set webhook"}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates from Telegram."""
    if not bot_application:
        logger.error("Bot application not initialized")
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        update_data = request.get_json()
        
        # Create Update object and process it
        update = Update.de_json(update_data, bot_application.bot)
        
        # Process the update in a separate thread to avoid blocking Flask
        def process_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(bot_application.process_update(update))
            finally:
                loop.close()
        
        Thread(target=process_update).start()
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Processing failed"}), 500

@app.route('/webhook_info')
def webhook_info():
    """Get current webhook information."""
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
    return jsonify(response.json())

# --- Main Function ---
def main():
    """Main function to start the application."""
    logger.info("🚀 Starting Doraemon Movies Bot...")
    
    # Setup database
    if not setup_database():
        logger.error("❌ Database setup failed. Exiting...")
        return False
    
    # Initialize bot
    if not init_bot():
        logger.error("❌ Bot initialization failed. Exiting...")
        return False
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"✅ Starting Flask server on port {port}")
    
    # For production, use a proper WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()