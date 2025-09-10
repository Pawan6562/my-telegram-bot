import os
import asyncio
from threading import Thread
from flask import Flask
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- Flask App for UptimeRobot ---
app = Flask('')
@app.route('/')
def home():
    return "I'm alive!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------

# --- Environment Variables ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")

# --- Database Setup ---
client = None
db = None
users_collection = None

def setup_database():
    global client, db, users_collection
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        # Create a unique index on user_id to prevent duplicates at the database level
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB se successfully connect ho gaya!")
        return True
    except Exception as e:
        print(f"❌ MongoDB se connect nahi ho paaya. Error: {e}")
        return False

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
    user_id = user.id
    
    try:
        if not users_collection.find_one({"user_id": user_id}):
            users_collection.insert_one({"user_id": user_id, "name": user.full_name, "username": user.username})
            if ADMIN_ID:
                admin_message = (
                    f"🔔 New User Alert! 🔔\n\n"
                    f"Name: {user.full_name}\n"
                    f"Username: @{user.username if user.username else 'N/A'}\n"
                    f"Telegram ID: `{user_id}`"
                )
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Start command mein user check karte waqt error: {e}")

    keyboard = [[title] for title in MOVIE_TITLES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        "👋 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲𝘀 𝗕𝗼𝘁!* 🎬💙\n\n"
        "🚀 𝗬𝗮𝗵𝗮𝗮𝗻 𝗮𝗮𝗽𝗸𝗼 𝗺𝗶𝗹𝘁𝗶 𝗵𝗮𝗶𝗻 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗸𝗶 𝘀𝗮𝗯𝘀𝗲 𝘇𝗮𝗯𝗮𝗿𝗱𝗮𝘀𝘁 𝗺𝗼𝘃𝗶𝗲𝘀, 𝗯𝗶𝗹𝗸𝘂𝗹 𝗲𝗮𝘀𝘆 𝗮𝘂𝗿 𝗳𝗮𝘀𝘁 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗸𝗲 𝘀𝗮𝗮𝘁𝗵।\n\n"
        "✨ *𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:*\n"
        "🔹 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗛𝗶𝗻𝗱𝗶 𝗗𝘂𝗯𝗯𝗲𝗱 𝗠𝗼𝘃𝗶𝗲𝘀 (𝗢𝗹𝗱 + 𝗟𝗮𝘁𝗲𝘀𝘁)\n"
        "🔹 𝗠𝘂𝗹𝘁𝗶-𝗤𝘂𝗮𝗹𝗶𝘁𝘆 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝘀: 𝟭𝟬𝟴𝟬𝗽 | 𝟳𝟮𝟬𝗽 | 𝟯𝟲𝟬𝗽 🎥\n"
        "🔹 𝗗𝗶𝗿𝗲𝗰𝘁 & 𝗙𝗮𝘀𝘁 𝗟𝗶𝗻𝗸𝘀 – 𝗻𝗼 𝘁𝗶𝗺𝗲 𝘄𝗮𝘀𝘁𝗲!\n"
        "🔹 𝗥𝗲𝗴𝘂𝗹𝗮𝗿 𝗠𝗼𝘃𝗶𝗲 𝗨𝗽𝗱𝗮𝘁𝗲𝘀\n\n"
        "👉 *𝗕𝗮𝘀 𝗺𝗼𝘃𝗶𝗲 𝗰𝗵𝗼𝗼𝘀𝗲 𝗸𝗶𝗷𝗶𝘆𝗲, 𝗮𝗽𝗻𝗶 𝗽𝗮𝘀𝗮𝗻𝗱 𝗸𝗶 𝗾𝘂𝗮𝗹𝗶𝘁𝘆 𝘀𝗲𝗹𝗲𝗰𝘁 𝗸𝗶𝗷𝗶𝘆𝗲 𝗮𝘂𝗿 𝗲𝗻𝗷𝗼𝘆 𝗸𝗶𝗷𝗶𝘆𝗲 𝗮𝗽𝗻𝗮 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲 𝗧𝗶𝗺𝗲!* 🍿💙\n\n"
        "📢 𝗛𝗮𝗺𝗮𝗿𝗲 [𝗗𝗢𝗥𝗔𝗘𝗠𝗢𝗡 𝗠𝗢𝗩𝗜𝗘𝗦](https://t.me/doraemon_movies_hindi_dubbed) 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗸𝗼 𝗷𝗼𝗶𝗻 𝗸𝗮𝗿𝗻𝗮 𝗻𝗮 𝗯𝗵𝗼𝗼𝗹𝗲𝗻, 𝘁𝗮𝗮𝗸𝗶 𝗻𝗲𝘄 𝘂𝗽𝗱𝗮𝘁𝗲𝘀 𝗮𝗮𝗽𝗸𝗼 𝘀𝗮𝗯𝘀𝗲 𝗽𝗲𝗵𝗹𝗲 𝗺𝗶𝗹𝘀𝗮𝗸𝗲𝗻! 🚀\n\n"
        "👇 *Neeche diye gaye menu se apni pasand ki movie select kijiye.*"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def movie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_title = update.message.text
    movie_data = MOVIE_DICT.get(movie_title)
    if movie_data:
        caption = f"🎬 **{movie_data['title']}**\n\n📥 Download from the button below!"
        # The faulty line is removed from here
        await update.message.reply_photo(
            photo=movie_data['poster'],
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )

# --- Admin Commands ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return
    try:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(f"📊 *Bot Statistics*\n\nTotal Unique Users: *{total_users}*", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Stats fetch karte waqt error: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return
    
    message_to_broadcast = " ".join(context.args)
    if not message_to_broadcast:
        await update.message.reply_text("Broadcast karne ke liye message likhein. Example: `/broadcast Hello everyone!`")
        return

    all_users = users_collection.find({}, {"user_id": 1})
    user_ids = [user["user_id"] for user in all_users]
    
    if not user_ids:
        await update.message.reply_text("Database mein broadcast karne ke liye koi user nahi hai.")
        return

    await update.message.reply_text(f"📢 Broadcast shuru ho raha hai {len(user_ids)} users ke liye...")
    
    success_count = 0
    fail_count = 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_broadcast, parse_mode=ParseMode.MARKDOWN)
            success_count += 1
        except Exception:
            fail_count += 1
        await asyncio.sleep(0.1)

    await update.message.reply_text(f"✅ Broadcast Complete!\n\nSuccessfully Sent: {success_count}\nFailed to Send: {fail_count}")

async def import_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Import karne ke liye User IDs provide karein. Example: `/import 12345 67890`")
        return

    users_to_insert = []
    for user_id_str in context.args:
        try:
            user_id = int(user_id_str)
            users_to_insert.append({"user_id": user_id, "name": "Imported User", "username": "N/A"})
        except ValueError:
            pass
    
    added_count = 0
    if users_to_insert:
        try:
            # This is the "dumb" part. It just tries to insert.
            # The unique index in the DB will handle duplicates automatically.
            users_collection.insert_many(users_to_insert, ordered=False)
        except errors.BulkWriteError as bwe:
            # This error happens when there are duplicates, which is OK.
            # We count the successful inserts.
            added_count = bwe.details['nInserted']
        except Exception as e:
            await update.message.reply_text(f"Database mein daalte waqt error: {e}")
            return
    
    # If there were no duplicates, insert_many doesn't raise an error.
    # So we need to get the count of what we tried to insert.
    if added_count == 0 and users_to_insert:
        added_count = len(users_to_insert)

    total_users = users_collection.count_documents({})
    await update.message.reply_text(
        f"✅ Import Complete!\n\n"
        f"Added: {added_count} new users.\n"
        f"(Duplicates were automatically ignored by the database.)\n\n"
        f"📊 Total Users in DB now: {total_users}"
    )

# --- Main Function ---
def main():
    keep_alive()
    
    if not setup_database():
        print("Database setup fail ho gaya. Bot band ho raha hai.")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("import", import_users))
    application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_handler))
    
    print("DoreBox Bot (The REAL, REAL, Dumb Import Version) is running!")
    application.run_polling()

if __name__ == '__main__':
    if not all([TOKEN, ADMIN_ID, MONGO_URI]):
        print("Error: Zaroori environment variables (TOKEN, ADMIN_ID, MONGO_URI) set nahi hain!")
    else:
        main()
