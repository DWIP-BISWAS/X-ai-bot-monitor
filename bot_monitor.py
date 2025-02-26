import os
import time
import logging
import requests
from flask import Flask, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Environment Variables from Railway
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
PORT = int(os.getenv("PORT", 5000))

# Statistics
message_count = 0
last_active_time = 0
error_log_file = "bot_errors.log"

# Logging
logging.basicConfig(filename=error_log_file, level=logging.ERROR)

# Flask API
app = Flask(__name__)

# Telegram Bot
async def start(update, context):
    await update.message.reply_text("Monitor is active.")

async def count_messages(update, context):
    global message_count, last_active_time
    message_count += 1
    last_active_time = time.time()

async def get_status(update, context):
    now = time.time()
    active_status = "Chatting now" if (now - last_active_time) < 10 else "Inactive"
    await update.message.reply_text(f"Monitor Status:\n- Messages: {message_count}\n- Status: {active_status}")

async def error_callback(update, context):
    logging.error(f"Error: {context.error}")
    if TOKEN and ADMIN_CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": ADMIN_CHAT_ID, "text": f"Monitor Error: {context.error}"})

# Telegram Handlers
app_bot = Application.builder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("status", get_status))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages))
app_bot.add_error_handler(error_callback)

# Flask Endpoints
@app.route('/status', methods=['GET'])
def api_status():
    now = time.time()
    active_status = "Chatting now" if (now - last_active_time) < 10 else "Inactive"
    return jsonify({"messages_received": message_count, "status": active_status})

@app.route('/errors', methods=['GET'])
def api_errors():
    if os.path.exists(error_log_file):
        with open(error_log_file, "r") as file:
            errors = file.readlines()
        return jsonify({"errors": errors[-5:]})
    return jsonify({"errors": []})

# Start Bot
async def run_bot():
    await app_bot.run_polling()

# Run Flask and Bot together
if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    app_bot.run_polling()
