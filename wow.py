import discord
import json
import random
import aiohttp
import hashlib
import asyncio
import logging
import coloredlogs

intents = discord.Intents.default()
intents.messages = True

bot = discord.Client(intents=intents)

REACTION_URL = 'https://raw.githubusercontent.com/BlindAndInsane/discord-reaction-selfbot/refs/heads/main/reaction.json'

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.DEBUG)
coloredlogs.install(level='DEBUG', logger=logger, fmt='%(asctime)s %(levelname)s: %(message)s')

async def load_reactions_from_url(url):
    logger.info(f"Fetching reactions from {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("Successfully loaded reactions from URL")
                return data.get("reactions", [])
            else:
                logger.error(f"Failed to fetch reactions, status code: {response.status}")
                return []

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    global REACTIONS
    REACTIONS = await load_reactions_from_url(REACTION_URL)
    if REACTIONS:
        logger.debug(f'Reactions loaded: {REACTIONS}')
    else:
        logger.warning("No reactions found in the JSON data!")

def get_reaction_index(message):
    msg_hash = int(hashlib.sha256(str(message.id).encode()).hexdigest(), 16)
    index = msg_hash % len(REACTIONS)
    logger.debug(f"Message ID {message.id} hashed to index {index}")
    return index

@bot.event
async def on_message(message):
    if message.guild.id == bot.guild_id and REACTIONS:
        logger.info(f"Processing message from {message.author} in {message.guild.name}")
        index = get_reaction_index(message)
        selected_reaction = REACTIONS[index]
        for emoji in selected_reaction:
            try:
                await message.add_reaction(emoji)
                logger.debug(f"Added reaction {emoji} to message ID {message.id}")
            except Exception as e:
                logger.error(f"Failed to react with {emoji} on message ID {message.id}: {e}")

async def main():
    token = input("Please enter your Discord bot token: ")
    server_id_input = input("Please enter your server ID: ")

    try:
        bot.guild_id = int(server_id_input)
        logger.info(f"Starting the bot for server ID {bot.guild_id}...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your bot token.")
    except ValueError:
        logger.error("Invalid server ID format. Please enter a valid server ID.")

if __name__ == "__main__":
    asyncio.run(main())
