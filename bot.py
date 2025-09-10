import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
from pymongo import MongoClient

# --- Flask App for UptimeRobot ---
# ... (Ye poora section waisa hi rahega, ismein koi change nahi)

# --- Secrets and Database Connection ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")

# MongoDB se connect karo
try:
    client = MongoClient(MONGO_URI)
    db = client.dorebox_bot # Database ka naam
    users_collection = db.users # Collection (table) ka naam
    print("MongoDB se successfully connect ho gaya.")
except Exception as e:
    print(f"MongoDB se connect nahi ho paaya. Error: {e}")
    users_collection = None

# ====================================================================
# DATABASE FUNCTIONS: Ab ye MongoDB use karenge
# ====================================================================
def is_new_user(user_id):
    """Check karta hai ki user database mein hai ya nahi."""
    if users_collection is None: return False # Agar DB connect nahi hua
    return users_collection.find_one({"user_id": user_id}) is None

def add_user_to_db(user_id):
    """Naye user ko database mein add karta hai."""
    if users_collection is None: return
    if is_new_user(user_id):
        users_collection.insert_one({"user_id": user_id})

def get_all_user_ids():
    """Database se saare user IDs nikaalta hai."""
    if users_collection is None: return []
    return [doc["user_id"] for doc in users_collection.find()]

# ====================================================================
# YAHAN AAPKI SAARI MOVIES KA DATA HAI
# ... (Ye poora section waisa hi rahega, ismein koi change nahi)
# ====================================================================

# ====================================================================
# START COMMAND: Ab ye MongoDB use karega
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    
    # Check karo ki user naya hai ya nahi
    if is_new_user(user_id):
        # Agar naya hai, to DB mein add karo aur Admin ko notification bhejo
        add_user_to_db(user_id)
        if ADMIN_ID:
            # ... (Admin notification wala code waisa hi rahega)
    
    # ... (User ko welcome message bhejne wala code waisa hi rahega)

# ====================================================================
# MOVIE HANDLER: Ismein koi change nahi hai
# ====================================================================
# ... (Ye poora section waisa hi rahega)

# ====================================================================
# ADMIN COMMANDS: Ab ye MongoDB use karenge
# ====================================================================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (Admin check wala code waisa hi rahega)
    
    # Database se saare users nikaalo
    user_ids = get_all_user_ids()
    await update.message.reply_text(f"Broadcast starting for {len(user_ids)} users...")
    
    # ... (Baaki broadcast ka logic waisa hi rahega)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (Admin check wala code waisa hi rahega)
    
    # Database se users ka count lo
    total_users = len(get_all_user_ids())
    await update.message.reply_text(f"📊 **Bot Statistics**\n\nTotal Unique Users: **{total_users}**", parse_mode='Markdown')

# ====================================================================
# MAIN FUNCTION
# ====================================================================
def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()

    # Zaroori library install karo
    # (Ye line Render par har baar chalegi to ensure pymongo is installed)
    os.system("pip install pymongo[srv]")

    # User handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text(MOVIE_TITLES), movie_handler))
    
    # Admin handlers
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))
    
    print("DoreBox Bot (with PERMANENT Memory) is running!")
    application.run_polling()

if __name__ == '__main__':
    if TOKEN is None or ADMIN_ID is None or MONGO_URI is None:
        print("Error: Zaroori environment variables (TOKEN, ADMIN_ID, MONGO_URI) set nahi hain!")
    else:
        main()
