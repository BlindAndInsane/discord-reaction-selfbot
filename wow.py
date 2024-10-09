import discord
import json
import hashlib
import logging
import coloredlogs
import asyncio
import aiohttp

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.DEBUG)
coloredlogs.install(level='DEBUG', logger=logger, fmt='%(asctime)s %(levelname)s: %(message)s')

bot = discord.Client()
config = {}

REACTIONS = []

def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.info("Successfully loaded config from file")
            return data
    except Exception as e:
        logger.error(f"Failed to load config from file: {e}")
        return {}

async def load_reactions_from_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    data = json.loads(content)
                    logger.info("Successfully loaded reactions from URL")
                    return data.get("reactions", [])
                else:
                    logger.error(f"Failed to load reactions. HTTP status code: {response.status}")
                    return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from URL content: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to load reactions from URL: {e}")
        return []

def is_channel_monitored(guild_id, channel_id, user_id):
    if user_id in config.get("ignored_users", []):
        logger.debug(f"User {user_id} is globally ignored.")
        return False

    if channel_id in config.get("channels", []):
        logger.debug(f"Channel {channel_id} is in the global channels list.")
        return True

    for guild in config.get("guilds", []):
        if guild["guild_id"] == guild_id:
            if channel_id in guild.get("blacklisted_channel", []):
                logger.debug(f"Channel {channel_id} is blacklisted in guild {guild_id}.")
                return False
            return True

    logger.debug(f"Guild {guild_id} or channel {channel_id} is not configured to be monitored.")
    return False

@bot.event
async def on_ready():
    global REACTIONS
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')

    REACTIONS = await load_reactions_from_url('https://raw.githubusercontent.com/BlindAndInsane/discord-reaction-selfbot/main/reactions.json')
    if not REACTIONS:
        logger.warning("No reactions found in the JSON data!")

def get_reaction_index(message_id):
    msg_hash = int(hashlib.sha256(str(message_id).encode()).hexdigest(), 16)
    index = msg_hash % len(REACTIONS)
    logger.debug(f"Message ID {message_id} hashed to index {index}")
    return index

@bot.event
async def on_message(message):
    if not is_channel_monitored(message.guild.id, message.channel.id, message.author.id):
        logger.debug(f"Skipping message from user {message.author.id} in channel {message.channel.id} in guild {message.guild.id}.")
        return

    logger.info(f"Processing message from {message.author} in {message.guild.name}")
    index = get_reaction_index(message.id)
    selected_reaction = REACTIONS[index]

    for emoji in selected_reaction:
        try:
            await message.add_reaction(emoji)
            logger.debug(f"Added reaction {emoji} to message ID {message.id}")
        except Exception as e:
            logger.error(f"Failed to react with {emoji} on message ID {message.id}: {e}")

async def start_bot():
    global config
    config = load_config('config.json')
    
    if not config:
        logger.error("Config file is empty or failed to load. Exiting...")
        return
    
    token = input("Please enter your Discord bot token: ")
    
    logger.info(f"Starting the bot...")
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your bot token.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(start_bot())
