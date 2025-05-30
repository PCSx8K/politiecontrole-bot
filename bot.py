from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
from flask import Flask, request
import os
import random
import asyncio
from dotenv import load_dotenv
load_dotenv(dotenv_path="python.env")

# ✅ Zet hier je bot token en webhook URL
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # bijv: https://politiecontrole-bot.onrender.com/webhook

# ✅ Groepslinks
CHANNEL_LINKS = {
    "FYI": {"name": "Politiecontrole FYI", "link": "https://t.me/PolitiecontroleFYI"},
    "Chatgroep": {"name": "Controles Chatgroep", "link": "https://t.me/ControlesChatGroep"},
    "Brugge": {"name": "Controles Brugge", "link": "https://t.me/ControlesBrugge"},
    "Westkust": {"name": "Controles Westkust", "link": "https://t.me/ControlesWestkust"},
    "Roeselare": {"name": "Controles Roeselare", "link": "https://t.me/ControlesRoeselare"},
    "Kortrijk": {"name": "Controles Kortrijk", "link": "https://t.me/ControlesKortrijk"},
    "Ieper": {"name": "Controles Ieper", "link": "https://t.me/ControlesIeper"},
    "Wallonie": {"name": "Controles Police HT", "link": "https://t.me/ControlesPoliceHT"},
    "OVL": {"name": "Controle OVL", "link": "https://t.me/ControleOVL"},
    "Antwerpen": {"name": "Controles Antwerpen Provincie", "link": "https://t.me/ControlesAntwProv"},
    "Brussels": {"name": "Controles Brussel", "link": "https://t.me/ControlesBXL"},
    "Limburg": {"name": "Controles Limburg", "link": "https://t.me/ControlesLimburg1"}
}

user_captcha = {}  # tijdelijk opslag voor antwoorden
app = Flask(__name__)  # voor webhook

# ✅ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    keyboard = [[InlineKeyboardButton("Verifieer mij", callback_data="captcha_start")]]
    await update.message.reply_text(
        f"Hallo {user},\n\nWelkom bij de verificatiebot van Politiecontrole.\n\n"
        "Klik op de knop hieronder om te bevestigen dat je een echte gebruiker bent.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ✅ CAPTCHA-generatie
async def captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    a, b = random.randint(1, 10), random.randint(1, 10)
    answer = a + b
    user_captcha[query.from_user.id] = answer

    options = [answer] + random.sample([i for i in range(2, 20) if i != answer], 3)
    random.shuffle(options)

    keyboard = [[InlineKeyboardButton(str(opt), callback_data=f"captcha_{opt}")] for opt in options]
    await query.edit_message_text(f"Beveiligingsvraag:\n\nWat is {a} + {b}?",
                                  reply_markup=InlineKeyboardMarkup(keyboard))

# ✅ CAPTCHA-afhandeling
async def captcha_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected = int(query.data.split("_")[1])
    correct = user_captcha.get(user_id)

    if selected == correct:
        keyboard = [
            [InlineKeyboardButton(info["name"], callback_data=f"group_{key}")]
            for key, info in CHANNEL_LINKS.items()
        ]
        await query.edit_message_text(
            "✅ Je bent geverifieerd.\n\nKies hieronder een groep om lid van te worden:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text("❌ Fout antwoord. Probeer opnieuw met /start.")

# ✅ Stuur groepslink + knop "Terug naar overzicht"
async def send_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data.split("_")[1]
    group = CHANNEL_LINKS.get(key)

    if group:
        keyboard = [[InlineKeyboardButton("🔙 Terug naar overzicht", callback_data="captcha_start")]]
        await query.edit_message_text(
            f"✅ Klik om lid te worden:\n{group['link']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text("❌ Groep niet gevonden.")

# ✅ Flask webhook handler
@app.route("/webhook", methods=["POST"])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), bot.bot)
    bot.create_task(bot.process_update(update))
    return "OK", 200

# ✅ Start Telegram bot (als webhook)
if __name__ == "__main__":
    from telegram.ext import Application

    appbuilder = ApplicationBuilder().token(BOT_TOKEN)
    bot = appbuilder.build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(captcha, pattern="^captcha_start$"))
    bot.add_handler(CallbackQueryHandler(captcha_response, pattern="^captcha_"))
    bot.add_handler(CallbackQueryHandler(send_group_link, pattern="^group_"))

    async def handle_webhook():
        from flask import request
        update = Update.de_json(request.get_json(force=True), bot.bot)
        await bot.process_update(update)
        return "ok"

    app.post("/webhook")(lambda: asyncio.run(handle_webhook()))

    bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )
