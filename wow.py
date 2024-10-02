import discord
import json
import hashlib
import logging
import coloredlogs
import asyncio

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.DEBUG)
coloredlogs.install(level='DEBUG', logger=logger, fmt='%(asctime)s %(levelname)s: %(message)s')

bot = discord.Client()
guild_id = None
REACTIONS = []

def load_reactions(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.info("Successfully loaded reactions from file")
            return data.get("reactions", [])
    except Exception as e:
        logger.error(f"Failed to load reactions from file: {e}")
        return []

@bot.event
async def on_ready():
    global REACTIONS
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    REACTIONS = load_reactions('reactions.json')
    if not REACTIONS:
        logger.warning("No reactions found in the JSON data!")

def get_reaction_index(message_id):
    msg_hash = int(hashlib.sha256(str(message_id).encode()).hexdigest(), 16)
    index = msg_hash % len(REACTIONS)
    logger.debug(f"Message ID {message_id} hashed to index {index}")
    return index

@bot.event
async def on_message(message):
    global guild_id
    if message.guild.id != guild_id:
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
    global guild_id
    token = input("Please enter your Discord user token: ")
    guild_id = int(input("Please enter your server ID: "))
    
    logger.info(f"Starting the bot for server ID {guild_id}...")
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your user token.")
    except ValueError:
        logger.error("Invalid server ID format. Please enter a valid server ID.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(start_bot())
