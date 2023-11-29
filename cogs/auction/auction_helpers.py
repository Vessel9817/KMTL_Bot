# cogs/auction/auction_helpers.py

import discord
from discord.ext import commands
from utils.auction_data import AuctionData
from utils.utilities import format_time_remaining
from datetime import datetime
from typing import Optional, Tuple
import logging
import asyncio

logger = logging.getLogger("discord_bot")


class AuctionHelpers:
    def __init__(self, bot):
        self.bot = bot

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
        if not isinstance(auction.end_time, datetime):
            logger.error(
                f"Invalid end_time for auction {auction.id}: {auction.end_time}"
            )
            return 0
        remaining_time = (auction.end_time - datetime.now()).total_seconds()
        return max(remaining_time, 0)

    def _determine_winner(self, auction: AuctionData) -> Tuple[str, discord.Color]:
        """Determine the winner of the auction."""
        if auction.bidders:
            winner, winning_bid = max(auction.bidders.items(), key=lambda bid: bid[1])
            auction.winner = winner
            return (
                f"The auction for {auction.item} is won by {winner} with a bid of {self.format_amount(winning_bid)}!",
                discord.Color.green(),
            )
        return (
            f"The auction for {auction.item} has ended with no bids.",
            discord.Color.red(),
        )

    async def _announce_winner(
        self,
        channel_id: int,
        item: str,
        announcement: str,
        color: discord.Color,
        auction_id: str,
    ):
        """Announce the auction winner in the specified channel."""
        channel = self.bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title=f"Auction Ended: {item}", description=announcement, color=color
            )
            embed.set_footer(text=f"Auction ID: {auction_id}")
            await channel.send(embed=embed)
        else:
            logger.error(f"Channel {channel_id} not found for auction announcement.")

    def _remove_auction(self, ctx: commands.Context):
        """Remove an auction from the active auctions list."""
        auction_key = self._get_auction_key(ctx)
        self.auctions.pop(auction_key, None)

    def _get_ongoing_auctions(self, guild_id: int) -> list:
        """Compile a list of formatted strings representing ongoing auctions."""
        ongoing_auctions = []
        # Iterate over all auction keys and auction objects
        for auction_key, auction in self.auctions.items():
            # Check if the auction key's guild part (first element of the tuple) matches the provided guild_id
            if auction_key[0] == guild_id and auction.active:
                remaining_seconds = self._get_remaining_time(auction)
                if auction.bidders:
                    highest_bidder, highest_bid = max(
                    auction.bidders.items(), key=lambda bid: bid[1]
                    )
                auction_info = (
                    f"Auction ID: {auction.id}\n"
                    f"Item: {auction.item}\n"
                    f"Current Bid: {self.format_amount(highest_bid)} by {highest_bidder} \n" #TODO: Make a variable to keep track of highest bidder
                )
                ongoing_auctions.append(auction_info)

        return ongoing_auctions

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
        embed = discord.Embed(
            title="Error", description=message, color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    def _build_auction_embed(self, auction: AuctionData) -> discord.Embed:
        """Build an embed for auction start and updates."""
        remaining_seconds = self._get_remaining_time(auction)
        formatted_time = format_time_remaining(remaining_seconds)

        # Build the auction description including the current highest bid
        description = (
            f"**Item:** {auction.item}\n"
            f"**Starting Bid:** {self.format_amount(auction.starting_bid)}\n"
            f"**Minimum Increment:** {self.format_amount(auction.min_increment)}\n"
        )

        # Add current highest bid information if there are bids
        if auction.bidders:
            highest_bidder, highest_bid = max(
                auction.bidders.items(), key=lambda bid: bid[1]
            )
            description += f"**Highest Bid:** {self.format_amount(highest_bid)} by {highest_bidder}\n"
        if auction.active:
            description += f"**Time Remaining:** {formatted_time}"
        else:
            description += f"**Auction Ended**\n"
            description += f"**Winner:** {auction.winner}\n"

        # Choose color based on whether it's a start or update
        embed_color = discord.Color.green() if auction.active else discord.Color.blue()

        embed = discord.Embed(
            title=f"Auction: {auction.item}", description=description, color=embed_color
        )
        embed.set_footer(text=f"Auction ID: {auction.id}")

        return embed

    async def update_auction_embed(self, auction: AuctionData):
        """Update the auction embed with the current information."""
        # Create a new embed with updated information
        updated_embed = self._build_auction_embed(auction)

        if auction.message_id:
            try:
                channel = self.bot.get_channel(auction.channel_id)
                auction_message = await channel.fetch_message(auction.message_id)
                await auction_message.edit(embed=updated_embed)
            except discord.NotFound:
                logger.error(
                    f"Auction message with ID {auction.message_id} could not be found."
                )
            except discord.Forbidden:
                logger.error(
                    f"Bot does not have permissions to edit the auction message with ID {auction.message_id}."
                )

    def parse_amount(self, amount_str: str) -> float:
        """
        Parses a bid amount string into a float.
        Accepts formats like '1k', '1m', '1b', '1t', etc., and their uppercase equivalents,
        including decimal values like '1.5m'.
        Returns None if the format is incorrect.
        """
        shorthand_multipliers = {
            "k": 1_000,
            "m": 1_000_000,
            "b": 1_000_000_000,
            "t": 1_000_000_000_000,
        }

        if amount_str[-1].lower() in shorthand_multipliers:
            try:
                number_part = float(amount_str[:-1])
                multiplier = shorthand_multipliers[amount_str[-1].lower()]
                return number_part * multiplier
            except ValueError:
                return None
        else:
            try:
                return float(amount_str)
            except ValueError:
                return None

    def format_amount(self, amount: float) -> str:
        """
        Formats a numeric amount into a shorthand notation with dynamic precision.
        Examples:
        - 1500 -> '1.5k'
        - 2500000 -> '2.5m'
        - 123456789 -> '123.456789m'
        - 1200000 -> '1.2m'
        """
        units = ["", "K", "M", "B", "T"]
        idx = 0

        while amount >= 1000 and idx < len(units) - 1:
            amount /= 1000.0
            idx += 1

        # Determine the number of decimal places needed
        if amount - int(amount) == 0:
            # No decimal part
            formatted_amount = f"{int(amount)}"
        else:
            # Keep all significant digits in the decimal part
            decimal_part = str(amount).split(".")[1]
            # Count non-zero digits in the decimal part for precision
            non_zero_digits = len(decimal_part.rstrip("0"))
            formatted_amount = f"{amount:.{non_zero_digits}f}".rstrip("0").rstrip(".")

        return formatted_amount + units[idx]

    async def _validate_bid_and_increment(self, ctx, starting_bid, min_increment):
        if starting_bid is None:
            await ctx.send(
                "Invalid starting bid format. Please enter a number or use formats like '1k', '1m', etc."
            )
            return False
        if min_increment is None:
            await ctx.send(
                "Invalid min increment format. Please enter a number or use formats like '1k', '1m', etc."
            )
            return False
        return True

    async def _validate_guild_and_auction_limits(self, ctx):
        if not self._is_in_guild_context(ctx):
            await self._send_error_message(
                ctx, "This command can only be used in a server."
            )
            return False
        if self._has_max_auctions(ctx.guild.id):
            await self._send_error_message(
                ctx,
                "The maximum number of concurrent auctions for this server has been reached.",
            )
            return False
        if self._is_auction_active(ctx):
            await self._send_error_message(
                ctx, "There is already an ongoing auction in this channel."
            )
            return False
        return True

    async def _validate_duration(self, ctx, duration):
        if duration is None or duration.total_seconds() < self.MIN_AUCTION_DURATION:
            await self._send_error_message(
                ctx,
                "Invalid or too short duration format. Please use formats like '1d 2h 30m'.",
            )
            return False
        return True

    def _create_auction_data(
        self, auction_id, item, starting_bid, min_increment, end_time, ctx
    ):
        return AuctionData(
            id=auction_id,
            item=item,
            starting_bid=starting_bid,
            min_increment=min_increment,
            end_time=end_time,
            channel_id=ctx.channel.id,
            guild_id=ctx.guild.id,
            creator_name=ctx.author.display_name,
            creator_id=ctx.author.id,
        )

    async def _validate_guild_context_and_auction(self, ctx):
        if not self._is_in_guild_context(ctx):
            await self._send_error_message(
                ctx, "This command can only be used in a server."
            )
            return False

        auction = self._get_auction(ctx)
        if not auction:
            await self._send_error_message(
                ctx, "There is no ongoing auction in this channel."
            )
            return False
        return True

    def _validate_bid(self, auction, bid_amount):
        return auction and self._is_valid_bid(auction, bid_amount)

    def _cancel_auction_timer(self, auction_id):
        auction_timer = self.auction_timers.get(auction_id)
        if auction_timer and not auction_timer.done():
            auction_timer.cancel()
            del self.auction_timers[auction_id]

    async def _wait_for_auction_end(self, auction):
        while self._get_remaining_time(auction) > 0:
            remaining_time = self._get_remaining_time(auction)
            await asyncio.sleep(remaining_time)

    async def _validate_close_auction_permissions(self, ctx, auction):
        if (
            ctx.author.id != auction.creator_id
            and not ctx.author.guild_permissions.manage_channels
        ):
            await self._send_error_message(
                ctx, "You do not have permission to close this auction."
            )
            return False
        return True

    async def _handle_command_not_found(self, ctx, error):
        logger.info(f"Command not found: {ctx.message.content}")

    async def _handle_missing_required_argument(self, ctx, error):
        await ctx.send(f"Missing a required argument: {error.param.name}")
        await ctx.send_help(ctx.command)

    async def _handle_bad_argument(self, ctx, error):
        await ctx.send("One or more arguments are invalid. Please check your input.")
        await ctx.send_help(ctx.command)

    async def _handle_command_on_cooldown(self, ctx, error):
        await ctx.send(
            f"This command is on cooldown. Try again after {error.retry_after:.2f} seconds."
        )
