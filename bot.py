import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

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
# Future mein nayi movie add karne ke liye, bas is list mein ek aur line add kar dena.
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

# ====================================================================
# START COMMAND: User ko welcome karta hai aur movie list dikhata hai
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Har movie ke liye ek button banate hain
    keyboard = []
    for index, movie in enumerate(MOVIES_DATA):
        # Har button ka data 'movie_0', 'movie_1', etc. hoga
        button = InlineKeyboardButton(movie["title"], callback_data=f'movie_{index}')
        keyboard.append([button])
    
    # Aakhri mein Channel ka button daal dete hain
    keyboard.append([InlineKeyboardButton("📣 Join My Channel", url="https://t.me/doraemon_all_movies_bycjh")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 **Hello! Welcome to Doraemon Movies Bot.**\n\n"
        "Please select a movie from the list below to get the download link.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ====================================================================
# BUTTON HANDLER: Jab user kisi movie button par click karta hai
# ====================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Button ka data 'movie_0', 'movie_1', etc. se movie ka index nikalte hain
    movie_index = int(query.data.split('_')[1])
    
    # Sahi movie ka data list se uthate hain
    movie = MOVIES_DATA[movie_index]
    
    # Movie ke liye keyboard (download button) banate hain
    keyboard = [[InlineKeyboardButton("✅ Download / Watch Now ✅", url=movie["link"])]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Poster ke saath message bhejte hain
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
    
    print("Doraemon Movies Bot is running with all the data!")
    application.run_polling()

if __name__ == '__main__':
    if TOKEN is None:
        print("Error: TELEGRAM_TOKEN environment variable not set!")
    else:
        main()
