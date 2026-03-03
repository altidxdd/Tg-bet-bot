from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import re
import os
import sqlite3

TOKEN = os.getenv("TOKEN")

CURRENCY = "$"
ALLOWED_USER_ID = 1196029909

conn = sqlite3.connect("bets.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    total_bet INTEGER DEFAULT 0
)
""")
conn.commit()

def add_bet(username, amount):
    cursor.execute("SELECT total_bet FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            "UPDATE users SET total_bet = total_bet + ? WHERE username = ?",
            (amount, username)
        )
    else:
        cursor.execute(
            "INSERT INTO users (username, total_bet) VALUES (?, ?)",
            (username, amount)
        )

    conn.commit()

def get_user_bet(username):
    cursor.execute("SELECT total_bet FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_all_users():
    cursor.execute("SELECT username, total_bet FROM users ORDER BY total_bet DESC")
    return cursor.fetchall()

def reset_all():
    cursor.execute("DELETE FROM users")
    conn.commit()

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return any(admin.user.id == update.effective_user.id for admin in admins)

async def parse_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.effective_user.id != ALLOWED_USER_ID:
        return

    text = update.message.text

    if "game started" in text.lower():
        p1_match = re.search(r"Player 1:\s*@?([A-Za-z0-9_]+)", text)
        bet_match = re.search(r"Bet:\s*\$?\s*(\d+)", text)

        if not p1_match or not bet_match:
            return

        username = p1_match.group(1)
        bet = int(bet_match.group(1))

        add_bet(username, bet)

        await update.message.reply_text(
            f"{CURRENCY}{bet} bet recorded for @{username} ✅"
        )

async def indibet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /indibet username")
        return

    username = context.args[0].replace("@", "")
    total = get_user_bet(username)

    if total > 0:
        await update.message.reply_text(f"@{username} Total Bet: {CURRENCY}{total}")
    else:
        await update.message.reply_text("No data found.")

async def mybet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    username = update.effective_user.username
    total = get_user_bet(username)

    if total > 0:
        await update.message.reply_text(f"@{username} Your Total Bet: {CURRENCY}{total}")
    else:
        await update.message.reply_text("No data found.")

async def totalbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    users = get_all_users()
    total = sum(user[1] for user in users)

    await update.message.reply_text(f"💰 Total Group Bets: {CURRENCY}{total}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    users = get_all_users()

    if not users:
        await update.message.reply_text("No data yet.")
        return

    message = "🏆 Leaderboard:\n\n"
    for i, (username, total) in enumerate(users[:10], start=1):
        message += f"{i}. @{username} - {CURRENCY}{total}\n"

    await update.message.reply_text(message)

async def resetall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    reset_all()
    await update.message.reply_text("✅ All data reset.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    await update.message.reply_text("""
Commands:
/indibet username
/mybet
/totalbet
/leaderboard
/resetall
/help
""")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse_game))
app.add_handler(CommandHandler("indibet", indibet))
app.add_handler(CommandHandler("mybet", mybet))
app.add_handler(CommandHandler("totalbet", totalbet))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("resetall", resetall))
app.add_handler(CommandHandler("help", help_command))

print("Bot running...")
app.run_polling()
