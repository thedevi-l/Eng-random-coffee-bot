# Random Coffee Telegram Bot

This bot automatically matches English language learners every week for conversation based on their level and interests.

## Features

- User registration with name, interests, and English level.
- Matches users weekly with similar profiles.
- Manual matching using /match command.
- Stores user data in SQLite (`users.db`).
- Automatically runs once a week.

## Getting Started

1. Clone this repo or download the ZIP.
2. Set up a `.env` file or set `BOT_TOKEN` as an environment variable.
3. Run the bot:

```bash
pip install -r requirements.txt
python bot.py
```

Ensure your bot token is available in the environment.

## Deployment

You can run this bot on:

- Replit (add BOT_TOKEN in Secrets).
- Railway.app (add a background worker).
- VPS (run `screen` or `pm2` to keep it alive).

