# auction_helpers.py

import discord
from discord.ext import commands
from utils.auction_data import AuctionData
from utils.utilities import parse_duration, format_time_remaining
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple

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