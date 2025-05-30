import logging
import sqlite3
import random
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NAME, LEVEL, INTERESTS, GOALS = range(4)

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        name TEXT,
        username TEXT,
        level TEXT,
        interests TEXT,
        goals TEXT
    )
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! What's your name?")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("What is your English level? (A2, B1, B2, C1)")
    return LEVEL

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["level"] = update.message.text.upper()
    await update.message.reply_text("What are your interests?")
    return INTERESTS

async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["interests"] = update.message.text
    await update.message.reply_text("What are your goals for speaking practice?")
    return GOALS

async def goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["goals"] = update.message.text
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, name, username, level, interests, goals)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        context.user_data["name"],
        user.username,
        context.user_data["level"],
        context.user_data["interests"],
        context.user_data["goals"]
    ))
    conn.commit()
    await update.message.reply_text("You're registered! You'll get a partner every week 😊")
    return ConversationHandler.END

async def match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Matching users...")
    match_users(context.application)
    await update.message.reply_text("Matches sent!")

def match_users(app):
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    random.shuffle(all_users)
    paired = set()
    for i in range(len(all_users)):
        for j in range(i+1, len(all_users)):
            user1 = all_users[i]
            user2 = all_users[j]
            if user1[1] in paired or user2[1] in paired:
                continue
            if user1[4] == user2[4]:
                try:
                    app.bot.send_message(chat_id=user1[1], text=f"Your speaking partner this week is {user2[2]} (@{user2[3]}).")
                    app.bot.send_message(chat_id=user2[1], text=f"Your speaking partner this week is {user1[2]} (@{user1[3]}).")
                    paired.add(user1[1])
                    paired.add(user2[1])
                except Exception as e:
                    logger.warning(f"Error sending message: {e}")
                break

scheduler = BackgroundScheduler()

def weekly_match():
    from telegram.ext import ApplicationBuilder
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    match_users(app)

scheduler.add_job(weekly_match, trigger="interval", weeks=1)
scheduler.start()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Canceled.")
    return ConversationHandler.END

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, level)],
        INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, interests)],
        GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("match", match_command))

print("Bot started...")
app.run_polling()