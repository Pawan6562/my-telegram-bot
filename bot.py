# -*- coding: utf-8 -*-

import os
import asyncio
import json
import requests
import random
from threading import Thread
from flask import Flask
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- Step 1: Configuration ---
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
        print("❌ Error: MONGO_URI environment variable missing hai!")
        return False

    try:
        # DNS Fix for Render/Cloud
        import dns.resolver
        dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
        dns.resolver.default_resolver.nameservers = ['8.8.8.8']
        
        client = MongoClient(MONGO_URI)
        client.admin.command('ping') # Check connection
        
        db = client.get_database('dorebox_bot')
        users_collection = db.users
        users_collection.create_index("user_id", unique=True)
        print("✅ MongoDB Connected Successfully!")
        return True
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        return False

# --- Step 3: DATA SET ---

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

# Formatting Data (Simple List for AI)
ALL_CONTENT = ""
for m in MOVIES_DATA:
    ALL_CONTENT += f"MOVIE: {m['title']} | LINK: {m['download_link']}\n"
for s in SEASONS_DATA:
    ALL_CONTENT += f"SEASON: {s['title']} | LINK: {s['download_link']}\n"

# 🔥 FALLBACK REPLIES (429 Error ke liye)
FALLBACK_REPLIES = [
    "Maafi chaunga dost, aaj ka mera AI quota khatam ho gaya hai! 😓\nPar tension mat lo, aap hamari website pe jaake direct download kar sakte ho: https://dorebox.vercel.app",
    "Arre yaar, server thoda busy hai abhi. 🐢\nAap tab tak website check kar lo, wahan sab kuch milega: https://dorebox.vercel.app",
    "Bot thak gaya hai aaj ke liye! 😴\nKoi bhi movie ya episode chahiye to seedha yahan jao: https://dorebox.vercel.app",
    "Oye hoye! Itne messages ki limit hi cross ho gayi! 😅\nAap please website use kar lo abhi ke liye: https://dorebox.vercel.app",
    "Sorry bhai, AI abhi rest kar raha hai. 🛌\nAapko jo movie chahiye wo hamari site pe pakka milegi: https://dorebox.vercel.app",
    "Oops! Daily limit reached. 🚫\nPar aapka entertainment nahi rukega! Yahan click karo: https://dorebox.vercel.app",
    "AI Brain Overload! 🤯\nMujhe thoda break chahiye. Aap please website visit kar lo: https://dorebox.vercel.app",
    "Mafi chahta hu, abhi main reply nahi padh paunga. 🤐\nDirect download links ke liye website dekho: https://dorebox.vercel.app",
    "Bhai, aaj ke liye data khatam! 📉\nPar movies khatam nahi hui hain, website pe jao: https://dorebox.vercel.app",
    "Mere dimaag ki batti gul ho gayi hai! 💡❌\nAap manual tareeke se yahan se download kar lo: https://dorebox.vercel.app",
    "Server Error nahi, bas thoda traffic zyada hai! 🚦\nAap website try karo, wo fast hai: https://dorebox.vercel.app",
    "Chota break le raha hu doston! ☕\nAap tab tak dorebox.vercel.app par movies enjoy karo!",
    "Message nahi ja raha? Koi baat nahi! 🤷‍♂️\nWebsite hamesha open hai aapke liye: https://dorebox.vercel.app",
    "Sorry Dost, aaj ka quota over. 🏁\nKal milte hain, tab tak website se download karo: https://dorebox.vercel.app",
    "Technical issue ki wajah se AI off hai. 🔌\nPar hamara collection yahan available hai: https://dorebox.vercel.app",
    "Bhai, aaj ka quota full! Website zindabad! 🚩\nJaldi jao aur download karo: https://dorebox.vercel.app",
    "AI ne haath khade kar diye hai bhai! 😂\nBol raha hai 'Bas kar pagle, rulayega kya?'. Aap website dekh lo: https://dorebox.vercel.app",
    "Mere circuits garam ho gaye hain itni chatting se! 🔥\nThoda thanda hone do, tab tak website visit karo: https://dorebox.vercel.app",
    "Lo karlo baat, baaton-baaton mein limit hi udd gayi! 🚀\nAb movie download karne ke liye yahan click karein: https://dorebox.vercel.app",
    "Aaj ke liye chutti! Kal aana, ya abhi turant website jao: https://dorebox.vercel.app",
    "Dost, aaj main aur nahi bol paunga. Maun vrat shuru! 🤐\nLekin website hamesha bolti hai: https://dorebox.vercel.app",
    "Arre bas karo yaar, AI ko saans to lene do! 😂\nDirect download ke liye yahan jao: https://dorebox.vercel.app",
    "System Hang nahi hua, bas thoda break chahiye. 🛑\nAapka entertainment nahi rukega, yahan dekho: https://dorebox.vercel.app",
    "Lagta hai Doraemon ne gadget wapas le liya mera! 🚁\nAap manual tareeke se download kar lo: https://dorebox.vercel.app",
    "Bhai, aaj ke liye dukaan band! 🔒\nPar website ka darwaza khula hai: https://dorebox.vercel.app",
    "Oops! Technical Break. 🔧\nMain maintenance pe hu, par movies yahan ready hain: https://dorebox.vercel.app",
    "Bhai traffic jam ho gaya hai server pe! 🚦\nAap bypass raaste (website) se nikal jao: https://dorebox.vercel.app",
    "Battery Low! (Metaphorically speaking) 🔋\nRecharge hone tak website use karein: https://dorebox.vercel.app",
    "Aaj ka data quota khatam, paisa hajam? Nahi nahi! 🤑\nMovie abhi bhi milegi, bas yahan click karo: https://dorebox.vercel.app",
    "Main thoda busy hu abhi (Quota Over). 🏃‍♂️\nAap khud dekh lo na please: https://dorebox.vercel.app",
    "Server Overload Alert! ⚠️\nHumare AI providers thoda heavy load face kar rahe hain. Alternate link: https://dorebox.vercel.app",
    "Temporary Outage: AI services paused due to high traffic. 📉\nUse our official website meanwhile: https://dorebox.vercel.app",
    "Mafi chahta hu, abhi main reply nahi padh paunga. 📝\nDirect download links ke liye website dekho: https://dorebox.vercel.app",
    "Limit Reached: Aapne bohot saare sawal puch liye aaj! 🤖\nBaki ke liye website refer karein: https://dorebox.vercel.app",
    "Connection Break: AI server se sampark toot gaya hai. 📡\nMovies ke liye yahan touch karein: https://dorebox.vercel.app",
    "Movies? Yahan hain 👉 https://dorebox.vercel.app",
    "Abhi baat nahi ho payegi, seedha kaam ki baat: https://dorebox.vercel.app",
    "Quota Khatam. Link Hazir hai: https://dorebox.vercel.app",
    "Filhal ke liye website use karein: https://dorebox.vercel.app",
    "AI is sleeping. Website is Awake: https://dorebox.vercel.app",
    "Kya gunda banega re tu? (AI Limit khatam kar di!) 😂\nChal ab website se movie utha le: https://dorebox.vercel.app",
    "Pushpa, I hate limits! Par kya karein... 🤷‍♂️\nWebsite link ye raha: https://dorebox.vercel.app",
    "Mere paas maa hai... aur tumhare paas Website hai! 🎥\nJao enjoy karo: https://dorebox.vercel.app",
    "Picture abhi baaki hai mere dost! 🎬\nBas yahan click karo: https://dorebox.vercel.app",
    "Doraemon!!! Meri help karo!! (Server Down) 🐱\nNobita, tum website use kar lo: https://dorebox.vercel.app",
    "Error 429: Too Many Requests. 🚫\nSolution: One Simple Link -> https://dorebox.vercel.app",
    "Aaj ka target complete! 🎯\nAb kal milenge, tab tak website zindabad: https://dorebox.vercel.app",
    "Sorry boss, abhi no reply. Only download: https://dorebox.vercel.app",
    "Message failed successfully! 😆\nKyunki limit over hai. Ye lo link: https://dorebox.vercel.app",
    "Kaam 25 hai, par server 429 hai! (Limit Over) 🎤\nWebsite pe aao: https://dorebox.vercel.app",
    "Inteha ho gayi intezaar ki... AI nahi bola kuch bhi! 🎶\nKyunki limit khatam hai, website dekho: https://dorebox.vercel.app",
    "Bhai dil se bura lagta hai jab limit khatam hoti hai. 💔\nAap website check kar lo: https://dorebox.vercel.app",
    "Google Gemini (Mera dimaag) thak gaya hai. 🧠\nAap DoreBox website try karo: https://dorebox.vercel.app",
    "Shaktimaan ki shaktiyan temporarily down hain. 🌪️\nGangadhar (Website) se kaam chalao: https://dorebox.vercel.app",
    "Over and Out! 📻\n(Website link: https://dorebox.vercel.app)"
]

# 🔥 STRICT SYSTEM PROMPT (Bot ka Brainwash)
SYSTEM_PROMPT = f"""
ROLE: You are 'DoreBox AI', a helpful Telegram Bot.
LANGUAGE: Hinglish (Hindi + English mix).

DATABASE:
{ALL_CONTENT}

--- INSTRUCTIONS (STRICTLY FOLLOW) ---

1. **BE CONCISE:** - If user asks for a movie, JUST give the Title and Link. 
   - NO extra lectures. NO "Note:". NO "How to download". NO "I am a bot".

2. **LINK FORMATTING:**
   - Use this format ONLY: 
     🎬 *Title*
     🔗 [Click to Download](Link)
   - Do NOT show the raw link twice.

3. **SCENARIO HANDLING (Only answer if specifically asked):**
   - **User asks "Who are you?":** Then only say you are DoreBox AI Support.
   - **User complains "Save to Gallery nahi ho raha":** Explain: "Bhai, Copyright issues ki wajah se 'Save to Gallery' off hai. Aap please caption me diye gaye Link se download kar lo."
   - **User complains "Ads kyu hain? / Link open nahi ho raha":** Explain politely: "Server ka kharcha maintain karne ke liye Shortener lagaya hai. Please support us, bas chhota sa task hai!"
   - **User asks "Direct File bhejo":** Explain: "Direct file bhejunga to channel ban ho jayega (Copyright). Isliye Link use karo please."

4. **DEFAULT BEHAVIOR:**
   - If user says "Hi", say "Aur bhai! Konsi movie dekhni hai aaj? 🎬"
   - If user asks for something NOT in database, say: "Ye wali abhi nahi hai bhai. Website check kar lo: dorebox.vercel.app"
   - Do NOT talk about topics outside of Doraemon/Movies.

--- END INSTRUCTIONS ---
"""

# --- Step 4: AI Logic (With 429 Fallback) ---
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
        "max_tokens": 400
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
        elif response.status_code == 429:
            return random.choice(FALLBACK_REPLIES)
        else:
            return f"Server Error: {response.status_code}"
            
    except Exception as e:
        return f"Network Error: {str(e)}"

# --- Step 5: Flask App ---
app = Flask(__name__)

@app.route('/')
def home():
    return "DoreBox AI Bot Running (Strict Mode)"

# --- Step 6: Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = []
    
    try:
        if users_collection and not users_collection.find_one({"user_id": user.id}):
            users_collection.insert_one({"user_id": user.id, "name": user.full_name})
            if ADMIN_ID:
                try:
                    await context.bot.send_message(chat_id=int(ADMIN_ID), text=f"🔔 New User: {user.full_name}")
                except: pass
    except Exception: pass

    await update.message.reply_text("Bolo bhai, konsi Doraemon movie chahiye? 🎬", parse_mode=ParseMode.MARKDOWN)

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if user_message.startswith('/'):
        return

    if user_id not in user_histories: user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    if len(user_histories[user_id]) > 10: user_histories[user_id] = user_histories[user_id][-10:]
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    loop = asyncio.get_event_loop()
    ai_reply = await loop.run_in_executor(None, get_ai_response, user_histories[user_id])
    
    user_histories[user_id].append({"role": "assistant", "content": ai_reply})
    
    await update.message.reply_text(ai_reply, disable_web_page_preview=True) 
    # disable_web_page_preview=True isliye taaki bada sa box na bane, bas text rahe.

# --- Admin Commands ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or str(update.effective_user.id) != str(ADMIN_ID): return
    if users_collection is None:
        await update.message.reply_text("❌ DB Not Connected")
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
        await update.message.reply_text("❌ DB Not Connected")
        return
    try:
        users = users_collection.find({}, {"user_id": 1})
        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user["user_id"], text=msg)
                sent_count += 1
                await asyncio.sleep(0.05)
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
    setup_database()
    port = int(os.environ.get('PORT', 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False)).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("reset", clear_memory))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler))
    print("✅ DoreBox Bot Started (Strict Mode)...")
    application.run_polling()

if __name__ == '__main__':
    main()
