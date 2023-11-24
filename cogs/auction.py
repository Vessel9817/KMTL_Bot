import discord
from discord.ext import commands
from utils.auction_data import AuctionData
from utils.utilities import parse_duration, format_time_remaining
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple

# Configure logger for the cog
logger = logging.getLogger("discord_bot")


class Auction(commands.Cog):
    MAX_AUCTIONS_PER_GUILD = 10  # Limit the number of concurrent auctions per guild

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auctions = {}  # Dictionary to store auction data per guild and channel
        self.next_auction_id = 1  # Initialize a simple auction ID counter

    @commands.command(name="startauction", aliases=["sa", "beginauction", "start"])
    async def start_auction(
        self,
        ctx: commands.Context,
        item: str,
        starting_bid: float,
        min_increment: float,
        *duration_parts: str,
    ):
        """Starts a new auction with the provided item, starting bid, minimum increment, and duration."""
        logger.info(f"{ctx.author} invoked the start_auction command")

        if not self._is_in_guild_context(ctx):
            await _send_error_message(
                ctx, "This command can only be used in a server."
            )
            return

        guild_id = ctx.guild.id
        self.auctions.setdefault(guild_id, {})

        if self._has_max_auctions(guild_id):
            await self._send_error_message(
                ctx,
                "The maximum number of concurrent auctions for this server has been reached. Please wait for an ongoing auction to end before starting a new one.",
            )
            return

        if self._is_auction_active(ctx):
            await self._send_error_message(
                ctx, "There is already an ongoing auction in this channel."
            )
            return

        duration = parse_duration(" ".join(duration_parts))
        if duration is None:
            await self._send_error_message(
                ctx, "Invalid duration format. Please use formats like '1d 2h 30m'."
            )
            return

        end_time = datetime.now() + duration
        auction_id = self._generate_auction_id()

        new_auction = AuctionData(
            id=auction_id,
            item=item,
            starting_bid=starting_bid,
            min_increment=min_increment,
            end_time=end_time,
            channel_id=ctx.channel.id,
            guild_id=guild_id,
            creator_name=ctx.author.display_name,
            creator_id=ctx.author.id,
        )
        self._set_auction(ctx, new_auction)

        logger.info(
            f"Auction started for {item} in guild {ctx.guild.name} (ID: {guild_id})"
        )
        embed = self._build_auction_started_embed(new_auction)
        await ctx.send(embed=embed)

        self.bot.loop.create_task(self.close_auction(ctx, auction_id, ctx.guild.id))

    @commands.command(name="bid", aliases=["placebid", "b"])
    async def place_bid(
        self, ctx: commands.Context, auction_id: str, bid_amount: float
    ):
        """Places a bid on an active auction with the given auction ID and bid amount."""
        logger.info(f"{ctx.author} placed a bid of {bid_amount}")

        if not self._is_in_guild_context(ctx):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a server.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        auction = self._get_auction(ctx)
        if not auction:
            embed = discord.Embed(
                title="Error",
                description="Auction ID not found in this server.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        if not self._is_valid_bid(auction, bid_amount):
            embed = discord.Embed(
                title="Error",
                description=f"Your bid must be at least {auction.min_increment} higher than the current bid of {auction.current_bid}.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        # Update the auction with the new bid
        auction.current_bid = bid_amount
        auction.bidders[ctx.author.display_name] = bid_amount

        logger.info(f"Bid placed on auction {auction_id} by {ctx.author.display_name}")
        embed = discord.Embed(
            title="Bid Placed Successfully",
            description=f"Current highest bid: {bid_amount} by {ctx.author.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Auction ID: {auction_id}")
        await ctx.send(embed=embed)

    async def close_auction(
        self, ctx, auction_id: str, guild_id: int, manual: bool = False
    ):
        """Closes the auction identified by the auction ID, either manually or automatically after the set duration."""
        logger.info(f"Attempting to close auction {auction_id} in guild {guild_id}")
        auction = self._get_auction(ctx)
        if not auction:
            logger.error(f"Auction {auction_id} not found in guild {guild_id}.")
            return

        # Wait until the auction duration ends unless manually closing
        if not manual:
            remaining_time = self._get_remaining_time(auction)
            await asyncio.sleep(remaining_time)

        if not self._is_auction_active(ctx):
            return

        announcement, color = self._determine_winner(auction)
        await self._announce_winner(
            auction.channel_id, auction.item, announcement, color
        )

        # Remove the auction after closure
        self._remove_auction(ctx=ctx)

    @commands.command(name="closeauction", aliases=["ca", "endauction", "close", "end"])
    @commands.has_permissions(manage_channels=True)
    async def manual_close_auction(self, ctx: commands.Context, auction_id: str):
        """Allows server staff to manually close an auction before its set duration ends."""
        logger.info(f"{ctx.author} invoked the manual_close_auction command")

        if not self._is_in_guild_context(ctx):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a server.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        await self.close_auction(ctx, auction_id, ctx.guild.id, manual=True)
        embed = discord.Embed(
            title="Auction Closed",
            description=f"Auction {auction_id} has been closed manually.",
            color=discord.Color.orange(),
        )
        await ctx.send(embed=embed)
        logger.info(
            f"Auction {auction_id} closed manually by {ctx.author.display_name}"
        )

    @commands.command(
        name="ongoingauctions",
        aliases=["currentauctions", "activeauctions", "active", "ongoing", "current"],
    )
    async def check_ongoing_auctions(self, ctx: commands.Context):
        """Lists all ongoing auctions in the server."""
        if not self._is_in_guild_context(ctx):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a server.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        ongoing_auctions = self._get_ongoing_auctions(ctx.guild.id)
        if not ongoing_auctions:
            embed = discord.Embed(
                title="No Ongoing Auctions",
                description="There are no ongoing auctions in this server.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Ongoing Auctions",
            description="\n\n".join(ongoing_auctions),
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        # Ignore errors that have already been handled locally
        if getattr(ctx, "handled", False):
            return

        # Handle specific types of command errors
        if isinstance(error, commands.CommandNotFound):
            # Log the error without sending a message to the channel
            logger.info(f"Command not found: {ctx.message.content}")
        elif isinstance(error, commands.MissingRequiredArgument):
            # Let the user know the correct format of the command
            await ctx.send(f"Missing a required argument: {error.param.name}")
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.BadArgument):
            # Let the user know the correct format of the command
            await ctx.send(
                "One or more arguments are invalid. Please check your input."
            )
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.CommandOnCooldown):
            # Let the user know that they're on cooldown
            await ctx.send(
                f"This command is on cooldown. Try again after {error.retry_after:.2f} seconds."
            )
        else:
            # Log any other command errors
            logger.error(f"An unexpected error occurred: {error}")

    # Helper functions begin here

    def _is_in_guild_context(self, ctx: commands.Context) -> bool:
        """Check if the command is invoked in a guild (server) context."""
        return ctx.guild is not None

    def _has_max_auctions(self, guild_id: int) -> bool:
        """Check if the guild has reached the maximum number of concurrent auctions."""
        return len(self.auctions.get(guild_id, {})) >= self.MAX_AUCTIONS_PER_GUILD

    def _get_auction(self, ctx: commands.Context) -> Optional[AuctionData]:
        """Retrieve an auction by its channel within a specific guild."""
        auction_key = self._get_auction_key(ctx)
        return self.auctions.get(auction_key)

    def _is_valid_bid(self, auction: AuctionData, bid_amount: float) -> bool:
        """Check if the bid amount is valid for the auction."""
        return (
            bid_amount > auction.current_bid
            and (bid_amount - auction.current_bid) >= auction.min_increment
        )

    def _get_remaining_time(self, auction: AuctionData) -> float:
        """Calculate the remaining time for an auction."""
        # Make sure auction.end_time is a datetime object
        if isinstance(auction.end_time, str):
            # If it's a string, parse it into a datetime object
            auction.end_time = datetime.strptime(
                auction.end_time, "%Y-%m-%d %H:%M:%S"
            )  # Adjust the format if necessary
        remaining_time = (auction.end_time - datetime.now()).total_seconds()
        return max(remaining_time, 0)

    def _determine_winner(self, auction: AuctionData) -> Tuple[str, discord.Color]:
        """Determine the winner of the auction."""
        if auction.bidders:
            winner, winning_bid = max(auction.bidders.items(), key=lambda bid: bid[1])
            return (
                f"The auction for {auction.item} is won by {winner} with a bid of {winning_bid}!",
                discord.Color.green(),
            )
        return (
            f"The auction for {auction.item} has ended with no bids.",
            discord.Color.red(),
        )

    async def _announce_winner(
        self, channel_id: int, item: str, announcement: str, color: discord.Color
    ):
        """Announce the auction winner in the specified channel."""
        channel = self.bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title=f"Auction Ended: {item}", description=announcement, color=color
            )
            await channel.send(embed=embed)
        else:
            logger.error(f"Channel {channel_id} not found for auction announcement.")

    def _remove_auction(self, ctx: commands.Context):
        """Remove an auction from the active auctions list."""
        auction_key = self._get_auction_key(ctx)
        self.auctions.pop(auction_key, None)

    def _get_ongoing_auctions(self, guild_id: int) -> list:
        """Compile a list of formatted strings representing ongoing auctions."""
        return [
            f"Auction ID: {auction_id}\n"
            f"Item: {auction.item}\n"
            f"Current Bid: {auction.current_bid}\n"
            f"Time Remaining: {format_time_remaining(auction.end_time)}"
            for auction_id, auction in self.auctions.get(guild_id, {}).items()
        ]

    def _generate_auction_id(self) -> str:
        """Generate a new auction ID and increment the counter."""
        auction_id = self.next_auction_id
        self.next_auction_id += 1
        return str(auction_id)

    def _get_auction_key(self, ctx: commands.Context) -> tuple:
        """Generate a key for the auctions dictionary based on the guild and channel."""
        return (ctx.guild.id, ctx.channel.id)

    def _is_auction_active(self, ctx: commands.Context) -> bool:
        """Check if there is an active auction in the current channel."""
        auction_key = self._get_auction_key(ctx)
        return auction_key in self.auctions

    def _set_auction(self, ctx: commands.Context, auction_data: AuctionData):
        """Store an auction in the auctions dictionary."""
        auction_key = self._get_auction_key(ctx)
        self.auctions[auction_key] = auction_data
        
    async def _send_error_message(self, ctx: commands.Context, message: str):
        """Send an error message embedded in the Discord channel."""
        embed = discord.Embed(title="Error", description=message, color=discord.Color.red())
        await ctx.send(embed=embed)
    
    def _build_auction_started_embed(self, auction: AuctionData) -> discord.Embed:
        """Build an embed for when an auction starts."""
        embed = discord.Embed(
            title="Auction Started!",
            description=(
                f"**Item:** {auction.item}\n"
                f"**Starting Bid:** {auction.starting_bid}\n"
                f"**Minimum Increment:** {auction.min_increment}\n"
                f"**Ends At:** {auction.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Auction ID: {auction.id}")
        return embed


async def setup(bot: commands.Bot):
    """Sets up the Auction cog."""
    await bot.add_cog(Auction(bot))
    logger.info("Auction cog loaded")
