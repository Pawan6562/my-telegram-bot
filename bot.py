import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

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
]

WELCOME_POSTER_URL = "https://iili.io/KxiipSV.png"

# ====================================================================
# START COMMAND: Sirf welcome message aur permanent keyboard bhejega
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_keyboard = [[KeyboardButton("🎬 All Movies")]]
    
    await update.message.reply_text(
        "👋 **Hello! Welcome to the Official DoreBox Bot.**\n\n"
        "Click the '🎬 All Movies' button below to see the list of all available movies.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False),
        parse_mode='Markdown'
    )

# ====================================================================
# MOVIE LIST DIKHANE WALA FUNCTION
# ====================================================================
async def show_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    for index, movie in enumerate(MOVIES_DATA):
        button = InlineKeyboardButton(movie["title"], callback_data=f'movie_{index}')
        keyboard.append([button])
    
    keyboard.append([InlineKeyboardButton("📣 Join My Channel", url="https://t.me/doraemon_all_movies_bycjh")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=WELCOME_POSTER_URL,
        caption="Please select a movie from the buttons below to get its download link instantly!",
        reply_markup=reply_markup
    )

# ====================================================================
# BUTTON HANDLER: Jab user kisi movie button par click karta hai
# ====================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    movie_index = int(query.data.split('_')[1])
    movie = MOVIES_DATA[movie_index]
    
    keyboard = [[InlineKeyboardButton("✅ Download / Watch Now ✅", url=movie["link"])]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.delete_message()

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=movie["poster"],
        caption=f"🎬 **{movie['title']}**\n\nClick the button below to download the movie.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ====================================================================
# MAIN FUNCTION (Isko nahi chhedna hai)
# ====================================================================
def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Regex('^🎬 All Movies$'), show_movie_list))
    
    print("DoreBox Bot (The Real Final Version) is running!")
    application.run_polling()

if __name__ == '__main__':
    if TOKEN is None:
        print("Error: TELEGRAM_TOKEN environment variable not set!")
    else:
        main()
