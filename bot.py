import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import requests
from threading import Thread
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TOKEN:
    logger.error("TELEGRAM_TOKEN not found!")
    exit(1)

# Movie data for your bot
MOVIES_DATA = [
    {
        "title": "Doraemon Nobita ke Teen Dristi Sheershiyon Wale Talwarbaaz",
        "poster": "https://i.postimg.cc/RZ82qxJ3/Doraemon-The-Movie-Nobita-s-Three-Magical-Swordsmen.png",
        "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen",
        "keywords": ["three", "3", "teen", "visionary", "drishti", "swordsmen", "talwar"]
    },
    {
        "title": "Doraemon Jadoo Mantar Aur Jahnoom", 
        "poster": "https://i.postimg.cc/Z5t0TfkP/Doraemon-The-Movie-Jadoo-Mantar-Aur-Jahnoom-by-cjh.jpg",
        "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom",
        "keywords": ["jadoo", "magic", "mantar", "jahnoom", "hell"]
    },
    {
        "title": "Doraemon Dinosaur Yoddha",
        "poster": "https://i.postimg.cc/3w83qTtr/Doraemon-The-Movie-Dinosaur-Yoddhha-Hindi-Tamil-Telugu-Download-FHD-990x557.jpg", 
        "link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha",
        "keywords": ["dinosaur", "dino", "yodha", "warrior"]
    },
    {
        "title": "Stand by Me Doraemon",
        "poster": "https://i.postimg.cc/vmkLDN1X/Doraemon-The-Movie-Stand-by-Me-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201", 
        "keywords": ["stand by me", "3d", "emotional"]
    },
    {
        "title": "Stand by Me Doraemon 2",
        "poster": "https://i.postimg.cc/y8wkR4PJ/Doraemon-The-Movie-Stand-by-Me-2-by-cjh.png",
        "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202",
        "keywords": ["stand by me 2", "part 2", "sequel"]
    }
]

MOVIE_TITLES = [movie["title"] for movie in MOVIES_DATA]

# Flask app for webhook
app = Flask(__name__)

# Bot application
bot_application = None

def init_bot():
    """Initialize bot application."""
    global bot_application
    try:
        bot_application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        bot_application.add_handler(CommandHandler("start", start_command))
        bot_application.add_handler(CommandHandler("help", help_command))
        bot_application.add_handler(CommandHandler("stats", stats_command))
        bot_application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_selected))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movies))
        
        logger.info("✅ Bot application initialized!")
        return True
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        return False

# Bot command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    # Send admin notification for new users
    if ADMIN_ID and str(user.id) != ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 New user started bot!

Name: {user.full_name}
Username: @{user.username or 'N/A'}
ID: `{user.id}`",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    # Create keyboard with movie titles
    keyboard = []
    for movie in MOVIES_DATA:
        keyboard.append([movie["title"]])
    
    # Add utility buttons
    keyboard.append(["🔍 Search Movies", "ℹ️ Help"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_message = (
        f"👋 *Welcome {user.first_name}!* 🎬

"
        "🤖 *Doraemon Movies Bot*

"
        "🎯 यहाँ आपको मिलेंगी सबसे बेहतरीन Doraemon movies!

"
        "✨ *Features:*
"
        "🔸 Hindi Dubbed Movies
"
        "🔸 High Quality Downloads
" 
        "🔸 Direct Download Links
"
        "🔸 Fast & Free

"
        "📱 *How to use:*
"
        "• Select movie from keyboard
"
        "• Or type movie name to search
"
        "• Click download button

"
        "👇 *Choose a movie from the menu below:*"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 *Doraemon Movies Bot Help*

"
        "📖 *Commands:*
"
        "• `/start` - Start the bot
"
        "• `/help` - Show this help
"
        "• `/stats` - Bot statistics (Admin only)

"
        "🎬 *How to download movies:*
"
        "1️⃣ Select movie from keyboard menu
"
        "2️⃣ Or type movie name to search
"
        "3️⃣ Click the download button
"
        "4️⃣ Enjoy your movie!

"
        "🔍 *Search Tips:*
"
        "• Type keywords like 'jadoo', 'dinosaur', 'stand'
"
        "• Movie names work too
"
        "• Search is case-insensitive

"
        "❓ *Need help?* Contact admin!"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command (admin only)."""
    if not ADMIN_ID or str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ This command is for admin only!")
        return
    
    stats_text = (
        "📊 *Bot Statistics*

"
        f"🎬 Total Movies: *{len(MOVIES_DATA)}*
"
        f"🤖 Bot Status: *Online*
"
        f"⚡ Server Status: *Running*

"
        "📈 *Available Movies:*
"
    )
    
    for i, movie in enumerate(MOVIES_DATA, 1):
        stats_text += f"{i}. {movie['title']}
"
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

async def movie_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle movie selection from keyboard."""
    selected_title = update.message.text
    
    # Find the selected movie
    movie = None
    for m in MOVIES_DATA:
        if m["title"] == selected_title:
            movie = m
            break
    
    if not movie:
        await update.message.reply_text("❌ Movie not found! Please try again.")
        return
    
    # Create download button
    keyboard = [[InlineKeyboardButton("📥 Download Now", url=movie["link"])]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = (
        f"🎬 **{movie['title']}**

"
        "📱 *Click the button below to download*
"
        "⚡ *Direct & Fast Download*
"
        "🎭 *Hindi Dubbed*

"
        "🔗 *Multiple quality options available on download page*"
    )
    
    try:
        await update.message.reply_photo(
            photo=movie["poster"],
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        # Fallback if photo fails
        await update.message.reply_text(
            f"{caption}

🖼️ [View Poster]({movie['poster']})",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=False
        )

async def search_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for movie search."""
    query = update.message.text.lower()
    
    # Handle special commands
    if "search" in query or "🔍" in query:
        search_help = (
            "🔍 *Movie Search Help*

"
            "Type any of these to find movies:
"
            "• Movie name (e.g., 'Stand by Me')
"
            "• Keywords (e.g., 'jadoo', 'dinosaur')
"
            "• Character names

"
            "💡 *Examples:*
"
            "• `three swordsmen`
"
            "• `magic mantar`
" 
            "• `stand by me`
"
            "• `dinosaur`

"
            "Try typing one of these!"
        )
        await update.message.reply_text(search_help, parse_mode=ParseMode.MARKDOWN)
        return
    
    if "help" in query or "ℹ️" in query:
        await help_command(update, context)
        return
    
    # Search for movies
    found_movies = []
    for movie in MOVIES_DATA:
        # Check title
        if query in movie["title"].lower():
            found_movies.append(movie)
            continue
        
        # Check keywords
        for keyword in movie["keywords"]:
            if keyword.lower() in query or query in keyword.lower():
                found_movies.append(movie)
                break
    
    if not found_movies:
        not_found_msg = (
            "😔 *No movies found!*

"
            "🔍 *Search suggestions:*
"
            "• Try different keywords
"
            "• Check spelling
"
            "• Use simpler terms

"
            "📝 *Available movies:*
"
        )
        
        for movie in MOVIES_DATA:
            not_found_msg += f"• {movie['title']}
"
        
        not_found_msg += "
💡 *Or use the keyboard menu below!*"
        
        await update.message.reply_text(not_found_msg, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Send found movies
    if len(found_movies) == 1:
        # If only one movie found, send it directly
        movie = found_movies[0]
        keyboard = [[InlineKeyboardButton("📥 Download Now", url=movie["link"])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        caption = f"🎯 *Found it!*

🎬 **{movie['title']}**

📥 Click below to download!"
        
        try:
            await update.message.reply_photo(
                photo=movie["poster"],
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            await update.message.reply_text(
                f"{caption}

🖼️ [View Poster]({movie['poster']})",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        # Multiple movies found
        result_msg = f"🎯 *Found {len(found_movies)} movies:*

"
        
        for i, movie in enumerate(found_movies, 1):
            result_msg += f"{i}. {movie['title']}
"
        
        result_msg += "
💡 *Tap any movie title from the keyboard to download!*"
        
        await update.message.reply_text(result_msg, parse_mode=ParseMode.MARKDOWN)

# Flask routes
@app.route('/')
def home():
    """Simple home page."""
    return """
    <html>
    <head><title>Doraemon Movies Bot</title></head>
    <body style="font-family: Arial; background: #111; color: white; text-align: center; padding: 50px;">
        <h1>🤖 Doraemon Movies Bot</h1>
        <p>Telegram bot is running successfully!</p>
        <p>Start the bot on Telegram to download movies.</p>
        <hr>
        <p><strong>Bot Status:</strong> ✅ Online</p>
        <p><strong>Total Movies:</strong> """ + str(len(MOVIES_DATA)) + """</p>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook."""
    if not bot_application:
        logger.error("Bot application not initialized")
        return jsonify({"error": "Bot not ready"}), 500
    
    try:
        # Get update from Telegram
        update_data = request.get_json()
        logger.info(f"Received update: {update_data}")
        
        # Create Update object
        update = Update.de_json(update_data, bot_application.bot)
        
        # Process update in separate thread
        def process_update():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot_application.process_update(update))
                loop.close()
            except Exception as e:
                logger.error(f"Error processing update: {e}")
        
        thread = Thread(target=process_update, daemon=True)
        thread.start()
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook')
def set_webhook():
    """Set webhook URL."""
    if not WEBHOOK_URL:
        return jsonify({"error": "WEBHOOK_URL not configured"}), 400
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            json={"url": webhook_url}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Webhook set successfully: {webhook_url}")
                return jsonify({
                    "success": True,
                    "message": f"Webhook set successfully: {webhook_url}",
                    "response": result
                })
            else:
                logger.error(f"❌ Telegram API error: {result}")
                return jsonify({"error": f"Telegram error: {result.get('description')}"}), 400
        else:
            logger.error(f"❌ HTTP error: {response.status_code}")
            return jsonify({"error": f"HTTP error: {response.status_code}"}), 400
            
    except Exception as e:
        logger.error(f"❌ Exception setting webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "bot_initialized": bot_application is not None,
        "total_movies": len(MOVIES_DATA),
        "webhook_url": WEBHOOK_URL
    })

# Main function
def main():
    """Start the application."""
    logger.info("🚀 Starting Doraemon Movies Telegram Bot...")
    
    # Initialize bot
    if not init_bot():
        logger.error("❌ Failed to initialize bot")
        return
    
    # Start Flask server
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"✅ Starting Flask server on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()