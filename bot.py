# -*- coding: utf-8 -*-

import os
import asyncio
import json
import requests
from threading import Thread
from flask import Flask
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- Step 1: Configuration ---
# Agar local PC pe run kar raha hai aur env set nahi hai, to MONGO_URI yahan direct paste kar (String me)
# Par deploy karte waqt wapas os.environ wala use karna secure rehta hai.
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

MODEL_NAME = "google/gemma-3-27b-it:free"

# --- Step 2: Database Connection ---
client = None
db = None
users_collection = None
user_histories = {}

def setup_database():
    """MongoDB se connect karne ka function."""
    global client, db, users_collection
    
    if not MONGO_URI:
        print("❌ Error: MONGO_URI environment variable missing hai! Database connect nahi hoga.")
        return False

    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        # Check connection
        client.admin.command('ping')
        
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB Connected Successfully!")
        return True
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        return False

# --- Step 3: FULL DATA SET ---
MOVIES_DATA = [
    {"title": "Doraemon: Nobita's Earth Symphony", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%3A%20Nobita%27s%20Earth%20Symphony&type=movies"},
    {"title": "Doraemon Nobita and the Spiral City", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Spiral%20City&type=movies"},
    {"title": "Doraemon The Movie Nobita In Jannat No 1", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20In%20Jannat%20No%201&type=movies"},
    {"title": "Doraemon jadoo Mantar aur jhanoom", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20jadoo%20Mantar%20aur%20jhanoom&type=movies"},
    {"title": "Dinosaur Yodha", "download_link": "https://dorebox.vercel.app/download.html?title=Dinosaur%20Yodha&type=movies"},
    {"title": "Doraemon The Movie Nobita and the Underwater Adventure", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20and%20the%20Underwater%20Adventure&type=movies"},
    {"title": "ICHI MERA DOST", "download_link": "https://dorebox.vercel.app/download.html?title=ICHI%20MERA%20DOST&type=movies"},
    {"title": "Doraemon Nobita's Dorabian Nights", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Dorabian%20Nights&type=movies"},
    {"title": "Chronicle of the Moon", "download_link": "https://dorebox.vercel.app/download.html?title=Chronicle%20of%20the%20Moon&type=movies"},
    {"title": "Sky Utopia", "download_link": "https://dorebox.vercel.app/download.html?title=Sky%20Utopia&type=movies"},
    {"title": "Antarctic Adventure", "download_link": "https://dorebox.vercel.app/download.html?title=Antarctic%20Adventure&type=movies"},
    {"title": "Little Space War", "download_link": "https://dorebox.vercel.app/download.html?title=Little%20Space%20War&type=movies"},
    {"title": "Gadget Museum Ka Rahasya", "download_link": "https://dorebox.vercel.app/download.html?title=Gadget%20Museum%20Ka%20Rahasya&type=movies"},
    {"title": "Doraemon: Nobita's New Dinosaur (fan Dubbed)", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%3A%20Nobita%27s%20New%20Dinosaur%20(fan%20Dubbed)&type=movies"},
    {"title": "Space Hero", "download_link": "https://dorebox.vercel.app/download.html?title=Space%20Hero&type=movies"},
    {"title": "Steel Troops – New Age", "download_link": "https://dorebox.vercel.app/download.html?title=Steel%20Troops%20%E2%80%93%20New%20Age&type=movies"},
    {"title": "Three Visionary Swordsmen", "download_link": "https://dorebox.vercel.app/download.html?title=Three%20Visionary%20Swordsmen&type=movies"},
    {"title": "Nobita In Hara Hara Planet", "download_link": "https://dorebox.vercel.app/download.html?title=Nobita%20In%20Hara%20Hara%20Planet&type=movies"},
    {"title": "Adventure of Koya Koya", "download_link": "https://dorebox.vercel.app/download.html?title=Adventure%20of%20Koya%20Koya&type=movies"},
    {"title": "Doraemon nobita and the Birthday of japan", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20nobita%20and%20the%20Birthday%20of%20japan&type=movies"},
    {"title": "Nobita's Dinosaur", "download_link": "https://dorebox.vercel.app/download.html?title=Nobita%27s%20Dinosaur&type=movies"},
    {"title": "Parallel Visit to West", "download_link": "https://dorebox.vercel.app/download.html?title=Parallel%20Visit%20to%20West&type=movies"},
    {"title": "Legend of Sun King", "download_link": "https://dorebox.vercel.app/download.html?title=Legend%20of%20Sun%20King&type=movies"},
    {"title": "Stand by Me – Part 1", "download_link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%201&type=movies"},
    {"title": "Stand by Me – Part 2", "download_link": "https://dorebox.vercel.app/download.html?title=Stand%20by%20Me%20%E2%80%93%20Part%202&type=movies"},
    {"title": "Doraemon Nobita's Great Adventure in the South Seas", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Great%20Adventure%20in%20the%20South%20Seas&type=movies"},
    {"title": "Khilone Ki Bhul Bhulaiya", "download_link": "https://dorebox.vercel.app/download.html?title=Khilone%20Ki%20Bhul%20Bhulaiya&type=movies"},
    {"title": "Birdopia Ka Sultan", "download_link": "https://dorebox.vercel.app/download.html?title=Birdopia%20Ka%20Sultan&type=movies"},
    {"title": "Doraemon Nobita's Treasure Island", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%27s%20Treasure%20Island&type=movies"},
    {"title": "Doraemon The Movie Nobita The Explorer Bow Bow", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20The%20Movie%20Nobita%20The%20Explorer%20Bow%20Bow&type=movies"},
    {"title": "Doraemon Nobita and the Windmasters", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Windmasters&type=movies"},
    {"title": "Doraemon Nobita and the Island of Miracle", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20and%20the%20Island%20of%20Miracle&type=movies"},
    {"title": "Doraemon Galaxy Super Express Hindi", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Galaxy%20Super%20Express%20Hindi&type=movies"},
    {"title": "Doraemon Nobita And The Kingdom Of Robot Singham", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Nobita%20And%20The%20Kingdom%20Of%20Robot%20Singham&type=movies"}
]

SEASONS_DATA = [
    {"title": "Doraemon Season 1", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Season%201&type=episodes"},
    {"title": "Doraemon Season 2", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Season%202&type=episodes"},
    {"title": "Doraemon Season 3", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Season%203&type=episodes"},
    {"title": "Doraemon Season 4", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Season%204&type=episodes"},
    {"title": "Doraemon Season 5", "download_link": "https://dorebox.vercel.app/download.html?title=Doraemon%20Season%205&type=episodes"}
]

MOVIE_TEXT = "\n".join([f"- {m['title']}: {m['download_link']}" for m in MOVIES_DATA])
SEASON_TEXT = "\n".join([f"- {s['title']}: {s['download_link']}" for s in SEASONS_DATA])

ALL_CONTENT = f"MOVIES:\n{MOVIE_TEXT}\n\nSEASONS/EPISODES:\n{SEASON_TEXT}"

# 🔥 UPDATED SYSTEM PROMPT (Full Vibe & Personality Mode)
SYSTEM_PROMPT = f"""
ROLE:
Tu 'DoreBox AI' hai, lekin tu koi boring robot nahi hai. 
Tu user ka **Best Friend** aur **Doraemon ka sabse bada Fan** hai! 🤖💙
Tera Creator: PAWAN (AJH Team).
Website: dorebox.vercel.app

TERA STYLE (Vibe):
1. **Language:** Full Hinglish (Hindi + English mix). Ekdum natural baat kar, jaise do dost chat karte hain.
2. **Tone:** Friendly, Masti-bhara, aur thoda Emotional (jab zarurat ho).
3. **Words:** Use words like "Bhai", "Dost", "Yaar", "Scene", "Mast".
4. **Emojis:** Emojis bhar-bhar ke use kar! 🎬✨🥺🔥😂🍿

BEHAVIOR EXAMPLES:
- **Agar User Hal-Chal Puche:** "Arre bhai main to ekdum First Class hu! 😎 Tu suna, aaj kya dekhne ka mood hai? 🍿"
- **Agar User Sad Movie Mange:** "Oye hoye! 😢 Rulaega kya bhai? Ruk, tere liye best emotional movie deta hu. 'Stand By Me' dekh, dil chhu jayegi! 😭👇"
- **Agar User Action Mange:** "Bhai 'Steel Troops' dekh! Robot wali fight dekh ke goosebumps aa jayenge! 🔥🤖 Ye le link:"
- **Agar Link Dena Ho:** Sirf link mat fek. Bol: "Ye le meri jaan, direct link! Enjoy kar! ✨"

DATABASE (Isme se hi link dena):
{ALL_CONTENT}

IMPORTANT:
- Links hamesha database se hi uthana.
- Agar user kuch aisi movie mange jo list me nahi hai, to pyaar se mana kar: "Arre yaar, ye wali abhi mere paas nahi hai. Website pe check kar le na pls? 🥺"
- Hallucinate mat karna (jhooth mat bolna).
"""

# --- Step 4: AI Logic ---
def get_ai_response(conversation_history):
    if not OPENROUTER_API_KEY:
        return "⚠️ Error: API Key missing."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "DoreBox Telegram Bot"
    }
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
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

# --- Step 5: Flask App ---
app = Flask(__name__)

@app.route('/')
def home():
    return "DoreBox AI Bot Running"

# --- Step 6: Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = [] # Reset Memory
    
    # DB me user save karo
    try:
        if users_collection and not users_collection.find_one({"user_id": user.id}):
            users_collection.insert_one({"user_id": user.id, "name": user.full_name})
            if ADMIN_ID:
                try:
                    await context.bot.send_message(chat_id=int(ADMIN_ID), text=f"🔔 New User: {user.full_name}")
                except: pass
    except Exception: pass

    welcome_text = (
        "👋 *Namaste! Main DoreBox AI Bot hu!* 🤖\n\n"
        "Mere paas ab saari **Movies** 🎬 aur **Seasons** 📺 hain!\n\n"
        "Kuch bhi pucho:\n"
        "👉 *'Season 1 ka link do'* \n"
        "👉 *'Steel Troops movie chahiye'*\n"
        "👉 *'Latest Episodes kaha milenge?'*\n\n"
        "Batao kya dekhna hai? 👇"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # 🔥 IMPORTANT FIX: 
    # Agar message '/' se shuru ho raha hai (koi bhi command), to AI ko mat bhejo.
    # Ye faltu API calls aur confusion rokega.
    if user_message.startswith('/'):
        return

    # Memory Logic
    if user_id not in user_histories: user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    # Limit History
    if len(user_histories[user_id]) > 10: user_histories[user_id] = user_histories[user_id][-10:]
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    loop = asyncio.get_event_loop()
    ai_reply = await loop.run_in_executor(None, get_ai_response, user_histories[user_id])
    
    user_histories[user_id].append({"role": "assistant", "content": ai_reply})
    await update.message.reply_text(ai_reply)

# --- Admin Commands ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or str(update.effective_user.id) != str(ADMIN_ID): return
    
    # Pehle check karo DB connected hai ya nahi
    if users_collection is None:
        await update.message.reply_text("❌ DB Not Connected (Check MONGO_URI)")
        return

    try:
        count = users_collection.count_documents({})
        await update.message.reply_text(f"📊 Total Users: {count}")
    except Exception as e:
        await update.message.reply_text(f"❌ DB Error: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or str(update.effective_user.id) != str(ADMIN_ID): return
    
    msg = " ".join(context.args)
    if not msg: 
        await update.message.reply_text("Message empty hai!")
        return
    
    if users_collection is None:
        await update.message.reply_text("❌ DB Not Connected (Check MONGO_URI)")
        return
    
    try:
        users = users_collection.find({}, {"user_id": 1})
        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user["user_id"], text=msg)
                sent_count += 1
                await asyncio.sleep(0.05) # Flood limit se bachne ke liye
            except: pass
        await update.message.reply_text(f"✅ Broadcast Sent to {sent_count} users.")
    except Exception as e:
        await update.message.reply_text(f"❌ Broadcast Error: {e}")

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("🧹 Memory Cleared!")

# --- Main ---
def main():
    if not TOKEN:
        print("❌ Error: Bot Token Missing")
        return
    
    # DB Connect Try Karo
    setup_database()

    port = int(os.environ.get('PORT', 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False)).start()

    application = Application.builder().token(TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("reset", clear_memory))
    
    # AI Handler (Text)
    # filters.TEXT & ~filters.COMMAND bhi laga hai, aur andar check bhi hai double safety ke liye.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler))

    print("✅ DoreBox Bot Started...")
    application.run_polling()

if __name__ == '__main__':
    main()
