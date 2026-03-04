from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import re
import os
import sqlite3

TOKEN = os.getenv("TOKEN")
CURRENCY = "$"
ALLOWED_USER_ID = 1196029909

# ===== DATABASE =====
conn = sqlite3.connect("bets.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, total_bet REAL DEFAULT 0)")
conn.commit()

def add_bet(username, amount):
    cursor.execute("SELECT total_bet FROM users WHERE username=?", (username,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE users SET total_bet = total_bet + ? WHERE username=?", (amount, username))
    else:
        cursor.execute("INSERT INTO users (username, total_bet) VALUES (?,?)", (username, amount))

    conn.commit()

def get_user_bet(username):
    cursor.execute("SELECT total_bet FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_all_users():
    cursor.execute("SELECT username, total_bet FROM users ORDER BY total_bet DESC")
    return cursor.fetchall()

def reset_all_data():
    cursor.execute("DELETE FROM users")
    conn.commit()

# ===== PARSE GAME MESSAGE =====
async def parse_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text or ""

    # Only accept messages from the game bot
    if update.effective_user.id != 1196029909:
        return

    # Must contain Game started
    if "game started" not in text.lower():
        return

    # Find bet amount
    bet_match = re.search(r"Bet:\s*\$?([0-9]+(\.[0-9]+)?)", text)

    if not bet_match:
        return

    amount = float(bet_match.group(1))

    # Try to find Player 1 name (optional)
    p1_match = re.search(r"Player 1:\s*(.*)", text)

    if p1_match:
        username = p1_match.group(1).strip()
        if username == "":
            username = "Unknown"
    else:
        username = "Unknown"

    add_bet(username, amount)

    await update.message.reply_text(
        f"💰 Bet recorded: ${amount:.2f}"
    )

# ===== COMMANDS =====
async def totalbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT SUM(total_bet) FROM users")
    total = cursor.fetchone()[0] or 0
    await update.message.reply_text(f"💰 Total Bets: {CURRENCY}{total:.2f}")

async def indibet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /indibet username")
        return

    username = context.args[0].replace("@", "")
    total = get_user_bet(username)

    if total > 0:
        await update.message.reply_text(f"{username} Total Bet: {CURRENCY}{total:.2f}")
    else:
        await update.message.reply_text("No data found.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    if not users:
        await update.message.reply_text("No data yet.")
        return

    message = "🏆 Leaderboard:\n\n"
    for i, (username, total) in enumerate(users[:10], start=1):
        message += f"{i}. {username} - {CURRENCY}{total:.2f}\n"

    await update.message.reply_text(message)

async def resetall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_all_data()
    await update.message.reply_text("✅ All data reset.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/totalbet - Show total group bets\n"
        "/indibet username - Show individual bet\n"
        "/leaderboard - Show top bettors\n"
        "/resetall - Reset all data\n"
        "/help - Show commands"
    )

# ===== START BOT =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse_game))
app.add_handler(CommandHandler("totalbet", totalbet))
app.add_handler(CommandHandler("indibet", indibet))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("resetall", resetall))
app.add_handler(CommandHandler("help", help_command))

print("Bot running...")
app.run_polling()
