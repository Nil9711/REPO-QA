import asyncio
import logging
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
from listeners.helpers import chunk_message

# Suppress discord.py logs (only show errors)
logging.getLogger("discord").setLevel(logging.ERROR)

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

        print(f"[Q] {message.author}: {question}")

        # Send initial "Thinking..." message
        thinking_msg = await message.reply("Thinking...", mention_author=False)

        # Track elapsed time
        elapsed = 0
        done = False

        async def update_thinking():
            nonlocal elapsed
            while not done:
                await asyncio.sleep(10)
                if not done:
                    elapsed += 10
                    print(f"[...] Still processing ({elapsed}s)")
                    try:
                        await thinking_msg.edit(content=f"Thinking... ({elapsed}s)")
                    except:
                        pass

        # Start the thinking updater
        updater_task = asyncio.create_task(update_thinking())

        try:
            # Run blocking call in thread to prevent heartbeat issues
            answer = await asyncio.to_thread(ask_question, INDEX_DIR, question)
            done = True
            updater_task.cancel()

            # Split into chunks if needed
            chunks = chunk_message(answer)
            print(f"[OK] Done, sending {len(chunks)} message(s)")

            # Edit first message with first chunk
            await thinking_msg.edit(content=chunks[0])

            # Send remaining chunks as follow-up messages
            for chunk in chunks[1:]:
                await message.channel.send(chunk)

        except Exception as e:
            done = True
            updater_task.cancel()
            print(f"[ERR] {e}")
            await thinking_msg.edit(content=f"Error: {e}")


if not TOKEN:
    raise SystemExit("DISCORD_BOT_TOKEN not set. Check your .env file.")

client.run(TOKEN)
