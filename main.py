from flask import Flask, request
from pyrogram import Client
import os

from bot_handlers import register

app = Flask(__name__)

pyro = Client(
    "filesharebot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

register(pyro)

@app.route("/webhook", methods=["POST"])
def webhook():
    pyro.process_update(request.get_json())
    return "OK", 200

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    pyro.start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
