# Made by @xchup
# Pyrogram File Sharing Bot
# Permanent Links + Media Auto Expiry + Broadcast System

import os
import time
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# ================= CONFIG =================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

FORCE_CHANNELS = [
    -1003599850450,
    -1001234567890
]

MEDIA_LIFETIME = 15 * 60  # 15 minutes

# ================= BOT =================

app = Client(
    "filesharebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# token -> message_id (permanent)
LINKS = {}

# user database (in memory)
USERS = set()

# ================= HELPERS =================

async def is_joined(user_id: int) -> bool:
    for ch in FORCE_CHANNELS:
        try:
            member = await app.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "owner"):
                return False
        except:
            return False
    return True


def join_buttons():
    buttons = []
    for i, ch in enumerate(FORCE_CHANNELS, start=1):
        buttons.append([
            InlineKeyboardButton(
                f"Channel {i}",
                url=f"https://t.me/c/{str(ch)[4:]}"
            )
        ])
    buttons.append([
        InlineKeyboardButton("📥 Get File", callback_data="get_file")
    ])
    return InlineKeyboardMarkup(buttons)


def expired_text(msg):
    if msg.video:
        return "📹 Video expired"
    if msg.document:
        return "📄 Document expired"
    if msg.photo:
        return "🖼 Image expired"
    if msg.audio:
        return "🎵 Audio expired"
    return "❌ Media expired"


async def auto_delete(chat_id, message):
    await asyncio.sleep(MEDIA_LIFETIME)
    try:
        await message.delete()
        await app.send_message(chat_id, expired_text(message))
    except:
        pass

# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):
    USERS.add(message.from_user.id)

    args = message.command

    if len(args) == 2:
        token = args[1]

        if token not in LINKS:
            await message.reply("❌ Invalid link.")
            return

        if not await is_joined(message.from_user.id):
            await message.reply(
                "🔒 Join all channels to get the file:",
                reply_markup=join_buttons()
            )
            return

        sent = await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=DB_CHANNEL_ID,
            message_id=LINKS[token]
        )

        asyncio.create_task(auto_delete(message.chat.id, sent))
        return

    await message.reply("👋 Welcome!")

# ================= CALLBACK =================

@app.on_callback_query(filters.regex("get_file"))
async def get_file(client, query):
    USERS.add(query.from_user.id)

    if not await is_joined(query.from_user.id):
        await query.answer("❌ Join all channels first!", show_alert=True)
        return

    token = query.message.text.split("start=")[-1].strip()

    if token not in LINKS:
        await query.answer("❌ Invalid link", show_alert=True)
        return

    sent = await client.copy_message(
        chat_id=query.message.chat.id,
        from_chat_id=DB_CHANNEL_ID,
        message_id=LINKS[token]
    )

    await query.message.delete()
    asyncio.create_task(auto_delete(query.message.chat.id, sent))
    await query.answer("📦 File sent!")

# ================= ADMIN LINK CREATION =================

@app.on_message(filters.private & filters.text & filters.user(ADMIN_ID))
async def admin_link(client, message):
    if "t.me/c/" not in message.text:
        return

    try:
        msg_id = int(message.text.split("/")[-1])
    except:
        await message.reply("❌ Invalid Telegram link.")
        return

    token = str(int(time.time() * 1000))
    LINKS[token] = msg_id

    me = await client.get_me()

    await message.reply(
        "✅ Permanent download link:\n\n"
        f"https://t.me/{me.username}?start={token}\n\n"
        "⏱ Media auto-expires after 15 minutes"
    )

# ================= BROADCAST SYSTEM =================

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        await message.reply(
            "❌ Reply to a message to broadcast.\n\n"
            "Usage:\n"
            "`/broadcast` (reply to text or media)",
            quote=True
        )
        return

    sent = 0
    failed = 0

    await message.reply("📢 Broadcast started...")

    for user_id in list(USERS):
        try:
            await message.reply_to_message.copy(user_id)
            sent += 1
        except:
            failed += 1

        await asyncio.sleep(0.05)  # avoid flood

    await message.reply(
        f"✅ Broadcast completed\n\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

# ================= DUMMY SERVER (RENDER FREE) =================

from flask import Flask
from threading import Thread

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is alive"

def run_web():
    web.run(host="0.0.0.0", port=10000)

Thread(target=run_web).start()

# ================= RUN =================

log.info("Bot started successfully")
app.run()


