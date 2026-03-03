from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import re
import os

TOKEN = os.getenv("TOKEN")

users = {}

def get_user(username):
    if username not in users:
        users[username] = {"total_bet": 0}
    return users[username]

async def parse_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text.startswith("Game started"):
        try:
            p1 = re.search(r"Player 1:\s*@?(\w+)", text).group(1)
            bet = int(re.search(r"Bet:\s*(\d+)", text).group(1))

            user1 = get_user(p1)
            user1["total_bet"] += bet

            await update.message.reply_text(f"₹{bet} bet recorded for @{p1} ✅")

        except:
            pass

async def indibet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /indibet username")
        return

    username = context.args[0].replace("@","")

    if username in users:
        total = users[username]["total_bet"]
        await update.message.reply_text(f"@{username} Total Bet: ₹{total}")
    else:
        await update.message.reply_text("No data found.")

async def totalbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(user["total_bet"] for user in users.values())
    await update.message.reply_text(f"💰 Total Group Bets: ₹{total}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse_game))
app.add_handler(CommandHandler("indibet", indibet))
app.add_handler(CommandHandler("totalbet", totalbet))

print("Bot running...")
app.run_polling()
