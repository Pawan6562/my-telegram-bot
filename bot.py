import os
from threading import Thread
from flask import Flask
import telegram
from telegram.ext import Application, CommandHandler

# --- Flask App for UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    # Render provides the PORT environment variable.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------

# Get the token from environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Start command handler
async def start(update, context):
    await update.message.reply_text('Hello! Main Render se host kiya gaya bot hoon aur main sota nahi hoon!')

# Main function to run the bot
def main():
    # Start the Flask web server in a background thread
    keep_alive()

    # Create the Telegram Bot Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
        
    print("Bot is running...")
        
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    # Check if the token is available
    if TOKEN is None:
        print("Error: TELEGRAM_TOKEN environment variable not set!")
    else:
        main()
