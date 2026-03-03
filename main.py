from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import re
import os

TOKEN = os.getenv("TOKEN")

# ---- CHANGE CURRENCY HERE IF NEEDED ----
CURRENCY = "$"

users = {}

def get_user(username):
    if username not in users:
        users[username] = {"total_bet": 0}
    return users[username]

# -------- PARSE GAME MESSAGE --------
async def parse_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text:
        return

    # Detect "Game started" even with emoji like ✅ Game started
    if "game started" in text.lower():
        try:
            # Extract Player 1 username
            p1_match = re.search(r"Player 1:\s*@?([A-Za-z0-9_]+)", text)

            # Extract Bet amount (supports $500 or 500)
            bet_match = re.search(r"Bet:\s*\$?\s*(\d+)", text)

            if not p1_match or not bet_match:
                print("Format didn't match")
                return

            p1 = p1_match.group(1)
            bet = int(bet_match.group(1))

            user1 = get_user(p1)
            user1["total_bet"] += bet

            await update.message.reply_text(
                f"{CURRENCY}{bet} bet recorded for @{p1} ✅"
            )

        except Exception as e:
            print("Error:", e)

# -------- INDIVIDUAL BET --------
async def indibet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /indibet username")
        return

    username = context.args[0].replace("@", "")

    if username in users:
        total = users[username]["total_bet"]
        await update.message.reply_text(f"@{username} Total Bet: {CURRENCY}{total}")
    else:
        await update.message.reply_text("No data found.")

# -------- TOTAL GROUP BET --------
async def totalbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = sum(user["total_bet"] for user in users.values())
    await update.message.reply_text(f"💰 Total Group Bets: {CURRENCY}{total}")

# -------- BOT START --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse_game))
app.add_handler(CommandHandler("indibet", indibet))
app.add_handler(CommandHandler("totalbet", totalbet))

print("Bot running...")
app.run_polling()
