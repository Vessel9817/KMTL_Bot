# utils/auction_data.py
from datetime import datetime
from typing import Optional

class AuctionData:
    def __init__(
        self,
        id: str,
        item: str,
        starting_bid: float,
        min_increment: float,
        end_time: datetime,
        channel_id: int,
        guild_id: int,
        creator_name: str,
        creator_id: int,
        message_id: Optional[int]=None,
    ):
        self.id = id
        self.item = item
        self.starting_bid = starting_bid
        self.current_bid = starting_bid
        self.min_increment = min_increment
        self.end_time = end_time
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.creator_name = creator_name
        self.creator_id = creator_id
        self.bidders: dict[str, float] = {}  # Stores bidder names and their bids
        self.active = True  # Indicates whether the auction is still active
        self.message_id = message_id  # ID of the message containing the auction details
        self.winner: Optional[str] = None
