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
# STEP 1: APNI SAARI MOVIES AUR LINKS YAHAN DAALO
# ====================================================================
# Har movie ke liye ek unique 'callback_data' (jaise 'movie_1') aur uske links ka message.
# Aap jitni chahein utni movies add kar sakte hain.

MOVIE_DATABASE = {
    "movie_1": """
*Nobita's Dinosaur* 🦖

*First Page : 1080p*
👉 [Download/Watch Link](https://apni-website.com/link1)

*Second Page : 720p*
👉 [Download/Watch Link](https://apni-website.com/link2)

*Third Page : 480p*
👉 [Download/Watch Link](https://apni-website.com/link3)

*NOTE: USE VLC PLAYER IF THE VIDEO DOESN'T PLAY*
""",
    "movie_2": """
*Doraemon and Adventure of Koya Koya Planet* 🪐

*First Page : 1080p*
👉 [Download/Watch Link](https://apni-website.com/link4)

*Second Page : 720p*
👉 [Download/Watch Link](https://apni-website.com/link5)
""",
    "movie_3": """
*Nobita The Explorer Bow! Bow!* 🗺️

*Download Link*
👉 [Click Here to Watch/Download](https://apni-website.com/link6)
""",
    # YAHAN AUR MOVIES ADD KARTE JAO...
    # "movie_4": "Movie 4 ka message yahan likho",
}

# ====================================================================
# STEP 2: START COMMAND PAR BUTTONS DIKHAO
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Ye saari movies ke buttons banata hai
    keyboard = [
        [InlineKeyboardButton("Nobita's Dinosaur 🦖", callback_data='movie_1')],
        [InlineKeyboardButton("Koya Koya Planet 🪐", callback_data='movie_2')],
        [InlineKeyboardButton("Nobita The Explorer Bow! Bow! 🗺️", callback_data='movie_3')],
        # JAISE-JAISE UPAR MOVIE ADD KARO, WAISE-WAISE YAHAN BUTTON ADD KARO
        # [InlineKeyboardButton("Movie 4 ka Naam", callback_data='movie_4')],
        [InlineKeyboardButton("📣 Join My Channel", url="https://t.me/doraemon_all_movies_bycjh")] # Aapke channel ka link
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("👋 Hello! Welcome to Doraemon Movies Bot.\n\nPlease select a movie from the list below:", reply_markup=reply_markup)

# ====================================================================
# STEP 3: BUTTON CLICK PAR SAHI LINK BHEJO
# ====================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # User ne jo button dabaya, uska data (jaise 'movie_1') lo
    movie_key = query.data
    
    # Database se us movie ka message nikalo
    message_text = MOVIE_DATABASE.get(movie_key, "Sorry, movie not found!")

    # Message ko edit karke movie links dikha do
    await query.edit_message_text(
        text=message_text,
        parse_mode='Markdown', # Hum links ke liye Markdown use kar rahe hain
        disable_web_page_preview=True # Taaki link ka bada sa preview na aaye
    )

# ====================================================================
# MAIN FUNCTION (Isko nahi chhedna hai)
# ====================================================================
def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Doraemon Movies Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    if TOKEN is None:
        print("Error: TELEGRAM_TOKEN environment variable not set!")
    else:
        main()
