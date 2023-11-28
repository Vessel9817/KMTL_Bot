import logging
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure logging to output to a file and the console with a specific format
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Define the intents for the bot (e.g., server messages, reactions)
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Create an instance of the bot with a specific command prefix and the defined intents
bot = commands.Bot(command_prefix='P.', intents=intents)

# Event listener for when the bot successfully connects to Discord
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')

# Function to load cogs asynchronously
async def load_cogs():
    # Load the auction cog
    await bot.load_extension('cogs.auction.auction')
    # Load the help cog
    await bot.load_extension('cogs.help')

# Main coroutine that loads the cogs and starts the bot
async def main():
    await load_cogs()
    await bot.start(TOKEN)

# Entry point for the script
if __name__ == '__main__':
    # Start the event loop and run the main coroutine
    asyncio.run(main())
