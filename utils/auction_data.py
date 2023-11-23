class AuctionData:
    def __init__(self, item, starting_bid, min_increment, end_time, channel_id, guild_id, owner_name, owner_id):
        self.item = item
        self.starting_bid = starting_bid
        self.current_bid = starting_bid
        self.min_increment = min_increment
        self.end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.bidders = {}  # Stores bidder names and their bids
        self.active = True  # Indicates whether the auction is still active