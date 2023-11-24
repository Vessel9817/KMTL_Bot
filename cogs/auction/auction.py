from discord.ext import commands, tasks
import logging
from .auction_helpers import AuctionHelpers
from .auction_commands import AuctionCommands
from datetime import datetime
import discord

# Configure logger for the cog
logger = logging.getLogger("discord_bot")


class Auction(commands.Cog, AuctionCommands, AuctionHelpers):
    MAX_AUCTIONS_PER_GUILD = 10  # Limit the number of concurrent auctions per guild

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auctions = {}
        self.next_auction_id = 1
        AuctionCommands.__init__(self, bot)
        AuctionHelpers.__init__(self, bot)


async def setup(bot: commands.Bot):
    """Sets up the Auction cog."""
    await bot.add_cog(Auction(bot))
    logger.info("Auction cog loaded")
