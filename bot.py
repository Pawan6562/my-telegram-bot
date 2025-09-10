import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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

# Secrets se Token aur Admin ID lena
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

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
# START COMMAND: Ab ye Admin ko notification bhi bhejega
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # --- ADMIN NOTIFICATION PART ---
    if ADMIN_ID:
        try:
            # User ki details nikaalo
            user_id = user.id
            first_name = user.first_name
            username = f"@{user.username}" if user.username else "N/A"
            
            # Admin ko bhejne ke liye message banao
            admin_message = (
                f"🔔 **New User Alert!** 🔔\n\n"
                f"**Name:** {first_name}\n"
                f"**Username:** {username}\n"
                f"**Telegram ID:** `{user_id}`"
            )
            # Admin ko message bhejo
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='Markdown')
        except Exception as e:
            print(f"Admin ko notification bhejte waqt error aaya: {e}")
    # -----------------------------

    # User ko welcome message aur menu bhejo
    keyboard = []
    for i in range(0, len(MOVIE_TITLES), 2):
        row = [KeyboardButton(MOVIE_TITLES[i])]
        if i + 1 < len(MOVIE_TITLES):
            row.append(KeyboardButton(MOVIE_TITLES[i+1]))
        keyboard.append(row)

    welcome_text = """
👋 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲𝘀 𝗕𝗼𝘁! 🎬💙

🚀 𝗬𝗮𝗵𝗮𝗮𝗻 𝗮𝗮𝗽𝗸𝗼 𝗺𝗶𝗹𝘁𝗶 𝗵𝗮𝗶𝗻 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗸𝗶 𝘀𝗮𝗯𝘀𝗲 𝘇𝗮𝗯𝗮𝗿𝗱𝗮𝘀𝘁 𝗺𝗼𝘃𝗶𝗲𝘀, 𝗯𝗶𝗹𝗸𝘂𝗹 𝗲𝗮𝘀𝘆 𝗮𝘂𝗿 𝗳𝗮𝘀𝘁 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗸𝗲 𝘀𝗮𝗮𝘁𝗵।

✨ 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:
🔹 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗛𝗶𝗻𝗱𝗶 𝗗𝘂𝗯𝗯𝗲𝗱 𝗠𝗼𝘃𝗶𝗲𝘀 (𝗢𝗹𝗱 + 𝗟𝗮𝘁𝗲𝘀𝘁)
🔹 𝗠𝘂𝗹𝘁𝗶-𝗤𝘂𝗮𝗹𝗶𝘁𝘆 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝘀: 𝟭𝟬𝟴𝟬𝗽 | 𝟳𝟮𝟬𝗽 | 𝟯𝟲𝟬𝗽 🎥
🔹 𝗗𝗶𝗿𝗲𝗰𝘁 & 𝗙𝗮𝘀𝘁 𝗟𝗶𝗻𝗸𝘀 – 𝗻𝗼 𝘁𝗶𝗺𝗲 𝘄𝗮𝘀𝘁𝗲!
🔹 𝗥𝗲𝗴𝘂𝗹𝗮𝗿 𝗠𝗼𝘃𝗶𝗲 𝗨𝗽𝗱𝗮𝘁𝗲𝘀

👉 𝗕𝗮𝘀 𝗺𝗼𝘃𝗶𝗲 𝗰𝗵𝗼𝗼𝘀𝗲 𝗸𝗶𝗷𝗶𝘆𝗲, 𝗮𝗽𝗻𝗶 𝗽𝗮𝘀𝗮𝗻𝗱 𝗸𝗶 𝗾𝘂𝗮𝗹𝗶𝘁𝘆 𝘀𝗲𝗹𝗲𝗰𝘁 𝗸𝗶𝗷𝗶𝘆𝗲 𝗮𝘂𝗿 𝗲𝗻𝗷𝗼𝘆 𝗸𝗶𝗷𝗶𝘆𝗲 𝗮𝗽𝗻𝗮 𝗗𝗼𝗿𝗮𝗲𝗺𝗼𝗻 𝗠𝗼𝘃𝗶𝗲 𝗧𝗶𝗺𝗲! 🍿💙

📢 𝗛𝗮𝗺𝗮𝗿𝗲 [𝗗𝗢𝗥𝗔𝗘𝗠𝗢𝗡 𝗠𝗢𝗩𝗜𝗘𝗦](https://t.me/doraemon_all_movies_bycjh) 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗸𝗼 𝗷𝗼𝗶𝗻 𝗸𝗮𝗿𝗻𝗮 𝗻𝗮 𝗯𝗵𝗼𝗼𝗹𝗲𝗻, 𝘁𝗮𝗮𝗸𝗶 𝗻𝗲𝘄 𝘂𝗽𝗱𝗮𝘁𝗲𝘀 𝗮𝗮𝗽𝗸𝗼 𝘀𝗮𝗯𝘀𝗲 𝗽𝗲𝗵𝗹𝗲 𝗺𝗶𝗹𝘀𝗮𝗸𝗲𝗻! 🚀

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
# MAIN FUNCTION (Isko nahi chhedna hai)
# ====================================================================
def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_handler))
    print("DoreBox Bot (with Admin Notifications) is running!")
    application.run_polling()

if __name__ == '__main__':
    if TOKEN is None or ADMIN_ID is None:
        print("Error: TELEGRAM_TOKEN ya ADMIN_ID environment variable set nahi hai!")
    else:
        main()
