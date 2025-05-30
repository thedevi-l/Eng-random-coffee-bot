import logging
import random
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)

NAME, LEVEL, INTERESTS, GOALS = range(4)
users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Привет! Как тебя зовут?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    keyboard = [
        [KeyboardButton("A1"), KeyboardButton("A2")],
        [KeyboardButton("B1"), KeyboardButton("B2")],
        [KeyboardButton("C1")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выбери свой уровень английского:", reply_markup=markup)
    return LEVEL

async def get_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["level"] = update.message.text.upper()
    await update.message.reply_text("Какие у тебя интересы?")
    return INTERESTS

async def get_interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["interests"] = update.message.text
    await update.message.reply_text("Какие у тебя цели в изучении английского?")
    return GOALS

async def get_goals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["goals"] = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or "нет username"

    users[user_id] = {
        "name": context.user_data["name"],
        "username": username,
        "level": context.user_data["level"],
        "interests": context.user_data["interests"],
        "goals": context.user_data["goals"]
    }

    await update.message.reply_text(
        f"Спасибо, {context.user_data['name']}! Мы свяжем тебя с партнёром каждую неделю. "
        f"Или ты можешь написать /match для ручного подбора."
    )
    return ConversationHandler.END

async def match_users(context: ContextTypes.DEFAULT_TYPE):
    if not users:
        return
    levels = {}
    for uid, info in users.items():
        level = info["level"]
        levels.setdefault(level, []).append(uid)

    for level, ids in levels.items():
        random.shuffle(ids)
        for i in range(0, len(ids) - 1, 2):
            user1 = users[ids[i]]
            user2 = users[ids[i + 1]]
            try:
                await context.bot.send_message(
                    chat_id=ids[i],
                    text=f"Твой партнёр на этой неделе: {user2['name']} (@{user2['username']})"
                )
                await context.bot.send_message(
                    chat_id=ids[i + 1],
                    text=f"Твой партнёр на этой неделе: {user1['name']} (@{user1['username']})"
                )
            except Exception as e:
                logging.warning(f"Ошибка отправки сообщения: {e}")

async def manual_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await match_users(context)
    await update.message.reply_text("Пары вручную сгенерированы и разосланы!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(match_users(app.bot)), "interval", weeks=1)
    scheduler.start()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_level)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_interests)],
            GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goals)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("match", manual_match))

    print("✅ Бот запущен...")
    app.run_polling()
