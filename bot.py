import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio

# --- Flask App for UptimeRobot (Isko nahi chhedna hai) ---
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
# ---------------------------------------------------------

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
USER_FILE = "user_ids.txt" # Hamari "Guest Book" file ka naam

# ====================================================================
# GUEST BOOK FUNCTIONS: User ID ko save aur check karne ke liye
# ====================================================================
def load_user_ids():
    """File se saare user IDs load karta hai."""
    if not os.path.exists(USER_FILE):
        return set()
    with open(USER_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_user_id(user_id):
    """Naye user ki ID ko file mein save karta hai."""
    with open(USER_FILE, "a") as f:
        f.write(str(user_id) + "\n")

# ====================================================================
# YAHAN AAPKI SAARI MOVIES KA DATA HAI
# ====================================================================
MOVIES_DATA = [
    {"title": "Jadoo Mantar aur Jhanoom", "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom"},
    {"title": "Dinosaur Yodha", "poster": "https://i.postimg.cc/3w83qTtr/Doraemon-The-Movie-Dinosaur-Yoddhha-Hindi-Tamil-Telugu-Download-FHD-990x557.jpg", "link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha"},
    {"title": "Underwater Adventure", "poster": "https://i.postimg.cc/yYLjw5Pn/Doraemon-The-Movie-Nobita.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20and%20the%20Underwater%20Adventure"},
    {"title": "ICHI MERA DOST", "poster": "https://i.postimg.cc/xjpCppDL/Doraemon-The-Movie-Nobita-in-Ichi-Mera-Dost-Hindi.png", "link": "https://dorebox.vercel.app/download.html?title=ICHI%20MERA%20DOST"},
    {"title": "Nobita's Dorabian Nights", "poster": "https://iili.io/KqRfWdv.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Dorabian%20Nights"},
    {"title": "Chronicle of the Moon", "poster": "https://i.postimg.cc/BbmtZs0X/m3.jpg", "link": "https://dorebox.vercel.app/download.html?title=Chronicle%20of%20the%20Moon"},
    {"title": "Sky Utopia", "poster": "https://i.postimg.cc/Nf3QTNXq/doraemon-movie-nobitas-sky-utopia-in-hindi.jpg", "link": "https://dorebox.vercel.app/download.html?title=Sky%20Utopia"},
    {"title": "Antarctic Adventure", "poster": "https://iili.io/Kx9Qifn.jpg", "link": "https://dorebox.vercel.app/download.html?title=Antarctic%20Adventure"},
    {"title": "Steel Troops – New Age", "poster": "https://i.postimg.cc/43C9KJr0/Doraemon-The-Movie-Nobita-and-the-Steel-Troops.jpg", "link": "https://dorebox.vercel.app/download.html?title=Steel%20Troops%20%E2%80%93%20New%20Age"},
    {"title": "Stand by Me – Part 2", "poster": "https://i.postimg.cc/y8wkR4PJ/Doraemon-The-Movie-Stand-by-Me-2-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202"},
    {"title": "Nobita's Treasure Island", "poster": "https://i.postimg.cc/t46rgZ36/Doraemon-the-Nobita-s-Treasure-Island-by-cjh.jpg", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Treasure%20Island"},
    {"title": "The Explorer Bow Bow", "poster": "https://i.postimg.cc/HxY336f0/The-Movie-Nobita-The-Explorer-Bow-Bow-by-cjh.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20The%20Explorer%20Bow%20Bow"},
    {"title": "Doraemon The Movie Nobita In Jannat No 1", "poster": "https://iili.io/KzFgEog.png", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20In%20Jannat%20No%201"},
]

MOVIE_TITLES = [movie['title'] for movie in MOVIES_DATA]

# ====================================================================
# START COMMAND: Ab ye smart ho gaya hai
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id_str = str(user.id)
    known_user_ids = load_user_ids()
    
    if user_id_str not in known_user_ids:
        if ADMIN_ID:
            try:
                first_name = user.first_name
                username = f"@{user.username}" if user.username else "N/A"
                admin_message = (
                    f"🔔 **New User Alert!** 🔔\n\n"
                    f"**Name:** {first_name}\n"
                    f"**Username:** {username}\n"
                    f"**Telegram ID:** `{user_id_str}`"
                )
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='Markdown')
                save_user_id(user_id_str)
            except Exception as e:
                print(f"Admin ko notification bhejte waqt error aaya: {e}")

    keyboard = []
    for i in range(0, len(MOVIE_TITLES), 2):
        row = [KeyboardButton(MOVIE_TITLES[i])]
        if i + 1 < len(MOVIE_TITLES):
            row.append(KeyboardButton(MOVIE_TITLES[i+1]))
        keyboard.append(row)

    welcome_text = """
👋 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲𝘀 𝗕𝗼𝘁! 🎬💙
... (Aapka poora welcome message yahan aayega) ...
👇 *Neeche diye gaye menu se apni pasand ki movie select kijiye.*
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ====================================================================
# MOVIE HANDLER: Ismein koi change nahi hai
# ====================================================================
async def movie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    movie_title = update.message.text
    selected_movie = None
    for movie in MOVIES_DATA:
        if movie['title'] == movie_title:
            selected_movie = movie
            break
    if selected_movie:
        keyboard = [[InlineKeyboardButton("✅ Download / Watch Now ✅", url=selected_movie["link"])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=selected_movie["poster"],
            caption=f"🎬 **{selected_movie['title']}**\n\nClick the button below to download the movie.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Please select a valid movie from the menu below.")

# ====================================================================
# ADMIN COMMANDS: Sirf Admin ke liye
# ====================================================================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # Pehle check karo ki command Admin bhej raha hai ya nahi
    if str(user.id) != ADMIN_ID:
        await update.message.reply_text("Sorry, this is an admin-only command.")
        return

    # Command se message ko alag karo
    # Example: /broadcast Hello everyone -> message_to_send = "Hello everyone"
    message_to_send = " ".join(context.args)
    if not message_to_send:
        await update.message.reply_text("Please provide a message to broadcast. \nExample: `/broadcast New movie added!`", parse_mode='Markdown')
        return

    # Saare users ko message bhejna shuru karo
    user_ids = load_user_ids()
    await update.message.reply_text(f"Broadcast starting for {len(user_ids)} users...")
    
    success_count = 0
    failure_count = 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_send, parse_mode='Markdown')
            success_count += 1
        except Exception as e:
            failure_count += 1
            print(f"ID {user_id} ko message nahi bhej paaye. Error: {e}")
        await asyncio.sleep(0.1) # Thoda sa delay

    # Admin ko final report bhejo
    await update.message.reply_text(
        f"**Broadcast Complete!**\n\n"
        f"✅ Sent to: {success_count} users\n"
        f"❌ Failed for: {failure_count} users"
    , parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # Check karo ki command Admin bhej raha hai ya nahi
    if str(user.id) != ADMIN_ID:
        await update.message.reply_text("Sorry, this is an admin-only command.")
        return
    
    user_ids = load_user_ids()
    await update.message.reply_text(f"📊 **Bot Statistics**\n\nTotal Unique Users: **{len(user_ids)}**", parse_mode='Markdown')

# ====================================================================
# MAIN FUNCTION
# ====================================================================
def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()

    # User handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_handler))
    
    # Admin handlers
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))
    
    print("DoreBox Bot (with Broadcast Feature) is running!")
    application.run_polling()

if __name__ == '__main__':
    if TOKEN is None or ADMIN_ID is None:
        print("Error: TELEGRAM_TOKEN ya ADMIN_ID environment variable set nahi hai!")
    else:
        main()
