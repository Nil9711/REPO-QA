import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import discord
from prompts.ask import main as ask_question

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
INDEX_DIR = os.environ.get("INDEX_DIR", "./indexes/bots-client-api")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if client.user in message.mentions:
        # Remove the bot mention from the question
        question = message.content.replace(f"<@{client.user.id}>", "").strip()
        if not question:
            await message.reply("Please ask a question!", mention_author=False)
            return

        await message.channel.typing()
        try:
            answer = ask_question(INDEX_DIR, question)
            # Discord has a 2000 char limit, truncate if needed
            if len(answer) > 1900:
                answer = answer[:1900] + "...\n(truncated)"
            await message.reply(answer, mention_author=False)
        except Exception as e:
            await message.reply(f"Error: {e}", mention_author=False)

if not TOKEN:
    raise SystemExit("DISCORD_BOT_TOKEN not set. Check your .env file.")

client.run(TOKEN)