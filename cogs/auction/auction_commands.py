# cogs/auction/auction_commands.py
import discord
from discord.ext import commands, tasks
from utils.auction_data import AuctionData
from utils.utilities import parse_duration, format_time_remaining
import logging
import asyncio
from datetime import datetime


logger = logging.getLogger("discord_bot")


class AuctionCommands:
    def __init__(self, bot):
        self.bot = bot
        self.auction_timers = {}  # Dictionary to keep track of auction tasks

    @commands.command(name="startauction", aliases=["sa", "beginauction", "start"], help = "Starts an auction with the given item, starting bid, minimum increment, and duration.")
    async def start_auction(
        self,
        ctx: commands.Context,
        item: str,
        starting_bid_str: str,
        min_increment_str: str,
        *duration_parts: str,
    ):
        """Starts a new auction with the provided item, starting bid, minimum increment, and duration."""
        logger.info(f"{ctx.author} invoked the start_auction command")

        # Parse starting bid and min increment
        starting_bid = self.parse_amount(starting_bid_str)
        min_increment = self.parse_amount(min_increment_str)

        # Validate starting bid and min increment
        if not await self._validate_bid_and_increment(ctx, starting_bid, min_increment):
            return

        # Check for guild context and max auctions
        if not await self._validate_guild_and_auction_limits(ctx):
            return

        # Parse and validate duration
        duration = parse_duration(" ".join(duration_parts))
        if not await self._validate_duration(ctx, duration):
            return

        end_time = datetime.now() + duration
        auction_id = self._generate_auction_id()

        new_auction = self._create_auction_data(
            auction_id, item, starting_bid, min_increment, end_time, ctx
        )

        auction_message = await ctx.send(embed=self._build_auction_embed(new_auction))
        new_auction.message_id = auction_message.id

        self._set_auction(ctx, new_auction)
        logger.info(
            f"Auction started for {item} in guild {ctx.guild.name} (ID: {ctx.guild.id})"
        )

        self.bot.loop.create_task(self.close_auction(ctx, auction_id, ctx.guild.id))
        auction_timer = asyncio.create_task(self.run_timer(ctx, new_auction))
        self.auction_timers[new_auction.id] = auction_timer

    @commands.command(name="bid", aliases=["placebid", "b"], help = "Places a bid on the active auction with the given bid amount.")
    async def place_bid(self, ctx: commands.Context, bid_amount_str: str):
        """Places a bid on an active auction with the given auction ID and bid amount."""
        logger.info(f"{ctx.author} attempted to bid with {bid_amount_str}")

        bid_amount = self.parse_amount(bid_amount_str)
        if bid_amount is None:
            embed = discord.Embed(
                title="Error",
                description="Invalid bid format. Please enter a number or use formats like '1k', '1m', etc.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        if not await self._validate_guild_context_and_auction(ctx):
            return

        auction = self._get_auction(ctx)
        if not self._validate_bid(auction, bid_amount):
            embed = discord.Embed(
                title="Error",
                description=f"Your bid must be at least {self.format_amount(auction.min_increment)} higher than the current bid of {self.format_amount(auction.current_bid)}.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        auction.current_bid = bid_amount
        auction.bidders[ctx.author.display_name] = bid_amount
        await self.update_auction_embed(auction)

        logger.info(f"Bid placed on auction {auction.id} by {ctx.author.display_name}")
        if self.BID_EMOJI_TOGGLE:
            await ctx.message.add_reaction("✅")
        else:
            embed = discord.Embed(
                title="Bid Placed Successfully",
                description=f"Current highest bid: {bid_amount_str} by {ctx.author.display_name}",
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Auction ID: {auction.id}")
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

        self._cancel_auction_timer(auction_id)
        if not manual:
            await self._wait_for_auction_end(auction)

        if not self._is_auction_active(ctx):
            return

        announcement, color = self._determine_winner(auction)
        await self._announce_winner(
            auction.channel_id, auction.item, announcement, color
        )
        auction.active = False
        await self.update_auction_embed(auction)
        self._remove_auction(ctx)

    @commands.command(name="closeauction", aliases=["ca", "endauction", "close", "end"], help = "Closes the auction with the given auction ID.")
    async def manual_close_auction(self, ctx: commands.Context, auction_id: str):
        """Allows server staff to manually close an auction before its set duration ends."""
        logger.info(f"{ctx.author} invoked the manual_close_auction command")

        if not await self._validate_guild_context_and_auction(ctx):
            return

        auction = self._get_auction(ctx)
        if not auction:
            await self._send_error_message(ctx, f"Auction {auction_id} not found.")
            return

        if not await self._validate_close_auction_permissions(ctx, auction):
            return

        await self.close_auction(ctx, auction_id, ctx.guild.id, manual=True)
        closed_by = ctx.author.display_name

        await ctx.send(
            embed=discord.Embed(
                title="Auction Closed",
                description=f"Auction {auction_id} has been closed manually by {closed_by}.",
                color=discord.Color.orange(),
            )
        )
        logger.info(
            f"Auction {auction_id} closed manually by {ctx.author.display_name}"
        )

    @commands.command(
        name="ongoingauctions",
        aliases=["currentauctions", "activeauctions", "active", "ongoing", "current"],
        help = "Lists all ongoing auctions in the server.",
    )
    async def check_ongoing_auctions(self, ctx: commands.Context):
        """Lists all ongoing auctions in the server."""
        if not self._is_in_guild_context(ctx):
            await self._send_error_message(
                ctx, "This command can only be used in a server."
            )
            return

        ongoing_auctions = self._get_ongoing_auctions(ctx.guild.id)
        if not ongoing_auctions:
            await self._send_error_message(
                ctx, "There are no ongoing auctions in this server."
            )
            return

        await ctx.send(
            embed=discord.Embed(
                title="Ongoing Auctions",
                description="\n\n".join(ongoing_auctions),
                color=discord.Color.blue(),
            )
        )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if getattr(ctx, "handled", False):
            return

        error_handlers = {
            commands.CommandNotFound: self._handle_command_not_found,
            commands.MissingRequiredArgument: self._handle_missing_required_argument,
            commands.BadArgument: self._handle_bad_argument,
            commands.CommandOnCooldown: self._handle_command_on_cooldown,
        }

        for error_type, handler in error_handlers.items():
            if isinstance(error, error_type):
                await handler(ctx, error)
                return

        logger.error(f"An unexpected error occurred: {error}")

    async def run_timer(self, ctx, auction):
        if not self._get_auction(ctx):
            return
        while self._get_remaining_time(auction) > 0:
            remaining_seconds = self._get_remaining_time(auction)

            await self.update_auction_embed(auction)

            # Use match case to adjust the interval
            match remaining_seconds:
                case seconds if seconds > 604800:  # More than a week remains
                    await asyncio.sleep(86400)  # Wait for 1 day before updating again
                case seconds if seconds > 86400:  # More than a day remains
                    await asyncio.sleep(3600)  # Wait for 1 hour before updating again
                case _:  # Less than a day remains
                    await asyncio.sleep(60)  # Wait for 60 seconds before updating again
