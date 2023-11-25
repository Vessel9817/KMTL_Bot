# utils/auction_data.py
class AuctionData:
    def __init__(
        self,
        id,
        item,
        starting_bid,
        min_increment,
        end_time,
        channel_id,
        guild_id,
        creator_name,
        creator_id,
        message_id=None,
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
        self.bidders = {}  # Stores bidder names and their bids
        self.active = True  # Indicates whether the auction is still active
        self.message_id = message_id  # ID of the message containing the auction details
        self.remaining_time_str = (
            None  # String representation of the time remaining in the auction
        )
        self.winner = None
