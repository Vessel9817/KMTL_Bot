# cogs/auction/auction.py
from discord.ext import commands
import logging
from .auction_commands import AuctionCommands

# Configure logger for the cog
logger = logging.getLogger("discord_bot")


class Auction(commands.Cog, AuctionCommands):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        AuctionCommands.__init__(self, bot)

async def setup(bot: commands.Bot) -> None:
    """Sets up the Auction cog."""
    await bot.add_cog(Auction(bot))
    logger.info("Auction cog loaded")
