# Made by @xchup
import telebot
import os
import re
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ===== FORCE JOIN CHANNELS =====
FORCE_CHANNELS = [
    "@Letsucks",
    "@USRxMEE"
]

bot = telebot.TeleBot(BOT_TOKEN)
LINK_RE = re.compile(r"t.me/c/\d+/(\d+)")

USERS_FILE = "users.json"

# ===== INIT USERS DB =====
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

def load_users():
    return json.load(open(USERS_FILE))

def save_users(users):
    json.dump(users, open(USERS_FILE, "w"), indent=2)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# ===== FORCE JOIN CHECK =====
def is_joined(user_id):
    for ch in FORCE_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_buttons():
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in FORCE_CHANNELS:
        kb.add(
            InlineKeyboardButton(
                f"Join {ch}",
                url=f"https://t.me/{ch[1:]}"
            )
        )
    kb.add(
        InlineKeyboardButton("✅ Joined", callback_data="recheck")
    )
    return kb

@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck(call):
    if is_joined(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            "✅ Verified!\nNow open the download link again."
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Join all channels first!",
            show_alert=True
        )

# ===== START / DOWNLOAD =====
@bot.message_handler(commands=["start"])
def start(msg):
    add_user(msg.from_user.id)  # 👈 SAVE USER

    args = msg.text.split()
    if len(args) == 2:
        if not is_joined(msg.from_user.id):
            bot.send_message(
                msg.chat.id,
                "🔒 You must join all channels to get the file:",
                reply_markup=join_buttons()
            )
            return

        message_id = int(args[1])
        bot.copy_message(
            chat_id=msg.chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=message_id
        )
    else:
        bot.reply_to(msg, "👋 Welcome!")

# ===== ADMIN-ONLY LINK CREATION =====
@bot.message_handler(func=lambda m: True)
def admin_actions(msg):
    add_user(msg.from_user.id)  # also save admin

    # ---- BROADCAST ----
    if msg.from_user.id == ADMIN_ID and msg.text.startswith("/broadcast"):
        text = msg.text.replace("/broadcast", "").strip()

        if not text:
            bot.reply_to(msg, "❌ Usage:\n/broadcast Your message")
            return

        users = load_users()
        sent = 0

        for uid in users:
            try:
                bot.send_message(uid, text)
                sent += 1
            except:
                pass

        bot.reply_to(msg, f"✅ Broadcast sent to {sent} users.")
        return

    # ---- LINK CREATION ----
    if msg.from_user.id != ADMIN_ID:
        return

    match = LINK_RE.search(msg.text)
    if not match:
        return

    msg_id = match.group(1)
    bot.reply_to(
        msg,
        f"✅ Download link:\n\n"
        f"https://t.me/{bot.get_me().username}?start={msg_id}"
    )

bot.infinity_polling()
