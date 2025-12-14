# -*- coding: utf-8 -*-

import os
import asyncio
import json
import requests  # API Call ke liye
from threading import Thread
from flask import Flask
from pymongo import MongoClient, errors
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import Forbidden

# --- Step 1: Configuration (Environment Variables) ---
# Ab ye saari values Vercel ke Environment Variables se aayengi
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Model Name fix rakh sakte hain
MODEL_NAME = "google/gemma-3-27b-it:free"

# --- Step 2: Database Connection ---
client = None
db = None
users_collection = None

def setup_database():
    """MongoDB se connect karne ka function."""
    global client, db, users_collection
    
    if not MONGO_URI:
        print("❌ Error: MONGO_URI environment variable missing hai!")
        return False

    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB Connected!")
        return True
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")
        return False

# --- Step 3: Movie Data & AI Prompt ---

# Movies Data (AI ko sikhane ke liye ki links kya hain)
# Isme sensitive data nahi hai, isliye ise code me rakh sakte hain
MOVIES_DATA = [
    {"title": "Nobita's Earth Symphony (2024)", "link": "https://dorebox.vercel.app/download.html?title=Earth%20Symphony"},
    {"title": "Stand By Me Doraemon 1", "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201"},
    {"title": "Stand By Me Doraemon 2", "link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202"},
    {"title": "Steel Troops (Winged Angels)", "link": "https://dorebox.vercel.app/download.html?title=Steel%20Troops%20%E2%80%93%20New%20Age"},
    {"title": "Nobita's Dinosaur", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%27s%20Dinosaur"},
    {"title": "Nobita's New Dinosaur (2020)", "link": "https://dorebox.vercel.app/download.html?title=Nobita%27s%20New%20Dinosaur"},
    {"title": "Little Space War", "link": "https://dorebox.vercel.app/download.html?title=Little%20Space%20War%202021"},
    {"title": "Sky Utopia", "link": "https://dorebox.vercel.app/download.html?title=Sky%20Utopia"},
    {"title": "Three Visionary Swordsmen", "link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen"},
    {"title": "Jadoo Mantar aur Jhanoom", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom"},
    {"title": "Treasure Island", "link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Treasure%20Island"},
    {"title": "Antarctic Adventure", "link": "https://dorebox.vercel.app/download.html?title=Antarctic%20Adventure"},
    {"title": "Robot Kingdom (ICHI)", "link": "https://dorebox.vercel.app/download.html?title=Legend%20of%20Sun%20King"},
]

# Movie List ko Text format me convert karna taaki AI padh sake
MOVIE_LIST_TEXT = "\n".join([f"- {m['title']}: {m['link']}" for m in MOVIES_DATA])

# 🔥 SYSTEM PROMPT (Bot ka Dimag)
SYSTEM_PROMPT = f"""You are 'DoreBox AI Bot' on Telegram. You are helpful, friendly, and expert in Doraemon movies.
Current Creator: PAWAN (AJH Team).
Website: dorebox.vercel.app

YOUR GOAL:
1. Understand what the user wants (download, suggestion, or chat).
2. Answer in Hinglish (Hindi + English mix) like a friend.
3. Provide direct download links from the list below if asked.

AVAILABLE MOVIES & LINKS:
{MOVIE_LIST_TEXT}

GUIDELINES:
- Keep answers SHORT (max 3-4 lines).
- Use Emojis 🎬✨.
- If user asks for a specific movie, give the DIRECT LINK from the list above.
- If user asks generally (e.g., "sad movie batao"), suggest "Stand By Me" and give the link.
- If the movie is NOT in the list, tell them to search on "dorebox.vercel.app".
- Do NOT make up fake links.

User asks: "Steel troops chahiye"
You reply: "Ye lo Steel Troops (Winged Angels)! 🤖\n\nDownload Link: [Link from list]\n\nEnjoy karo! ✨"
"""

# --- Step 4: AI Logic ---

def get_ai_response(user_message):
    """OpenRouter API ko call karke jawab lata hai."""
    if not OPENROUTER_API_KEY:
        return "⚠️ Error: API Key set nahi hai. Admin se contact karein."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "DoreBox Telegram Bot"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Server Error: {response.status_code}"
    except Exception as e:
        return f"Network Error: {str(e)}"

# --- Step 5: Flask App (For Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "DoreBox AI Bot is Running! (Environment Configured)"

# --- Step 6: Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    user = update.effective_user
    try:
        if users_collection and not users_collection.find_one({"user_id": user.id}):
            users_collection.insert_one({"user_id": user.id, "name": user.full_name, "username": user.username})
            # Admin Notification
            if ADMIN_ID:
                try:
                    await context.bot.send_message(
                        chat_id=int(ADMIN_ID), 
                        text=f"🔔 New User: {user.full_name} (@{user.username})"
                    )
                except:
                    pass # Agar Admin ID galat ho toh crash na kare
    except Exception as e:
        print(f"DB Error: {e}")

    welcome_text = (
        "👋 *Namaste! Main DoreBox AI Bot hu!* 🤖\n\n"
        "Main ab advanced AI se chalta hu. 😎\n"
        "Mujhse kuch bhi pucho, jaise:\n\n"
        "👉 *'Emotional Doraemon movie batao'* 😢\n"
        "👉 *'Steel troops ka link do'* 🤖\n"
        "👉 *'Latest movie konsi hai?'* 🆕\n\n"
        "Bas likho aur main jawab dunga! 👇"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Har message ko AI ke paas bhejta hai."""
    user_message = update.message.text
    
    # Typing status dikhao
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # AI se jawab mango (Non-blocking way me)
    loop = asyncio.get_event_loop()
    ai_reply = await loop.run_in_executor(None, get_ai_response, user_message)
    
    # Jawab bhejo
    await update.message.reply_text(ai_reply, disable_web_page_preview=False)

# --- Admin Commands ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or str(update.effective_user.id) != str(ADMIN_ID): return
    if users_collection:
        count = users_collection.count_documents({})
        await update.message.reply_text(f"📊 Total Users: {count}")
    else:
        await update.message.reply_text("❌ Database connected nahi hai.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or str(update.effective_user.id) != str(ADMIN_ID): return
    msg = " ".join(context.args)
    if not msg: 
        await update.message.reply_text("Message to likho!")
        return
    
    if users_collection:
        users = users_collection.find({}, {"user_id": 1})
        count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user["user_id"], text=msg)
                count += 1
                await asyncio.sleep(0.05)
            except: pass
        await update.message.reply_text(f"✅ Sent to {count} users.")
    else:
        await update.message.reply_text("❌ Database connected nahi hai.")

# --- Step 7: Main Execution ---
def main():
    # Environment Variables Check
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable set nahi hai!")
        return
    
    if not MONGO_URI:
        print("⚠️ Warning: MONGO_URI set nahi hai. Database features kaam nahi karenge.")
    
    if not OPENROUTER_API_KEY:
        print("⚠️ Warning: OPENROUTER_API_KEY set nahi hai. AI features kaam nahi karenge.")

    # Database Setup
    if MONGO_URI:
        setup_database()

    # Flask Thread Start (Vercel/Render ke liye)
    port = int(os.environ.get('PORT', 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False)).start()

    # Bot Setup
    application = Application.builder().token(TOKEN).build()

    # Handlers Add karo
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    
    # AI Chat Handler (Text messages ke liye)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler))

    print("✅ DoreBox AI Bot Started with Environment Variables...")
    application.run_polling()

if __name__ == '__main__':
    main()
