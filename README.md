# Project Plutus

## Description
A Discord bot to facilitate auctions for KMTL. It allows users to create auction events, place bids, and manage auction processes seamlessly.

## Features
- **Auction Creation**: Users can create auction events with specific items, starting bids, and duration.
- **Bid Handling**: The bot handles bids, ensuring they meet the minimum increment and are placed within the auction duration.
- **Auction Timer**: A countdown for each auction, notifying participants as the auction nears its end.

## Deployment Instructions

To deploy the Project Plutus Discord bot, follow these steps:

1. **Set up a Discord bot account**:
   - Go to the Discord Developer Portal (https://discord.com/developers/applications).
   - Click on the "New Application" button and give it a name.
   - Go to the "Bot" tab and click on "Add Bot". Confirm the creation.
   - Save the token provided as you will need it to run your bot.

2. **Invite the bot to your server**:
   - In the Developer Portal, navigate to the "OAuth2" tab.
   - Under "Scopes", select "bot".
   - In the "Bot Permissions" section, select the permissions your bot will need.
   - Copy the generated URL and open it in your browser to invite the bot to your server.

3. **Set up the bot environment**:
   - Ensure you have Python installed on your system.
   - Install the required Python packages with `pip install -r requirements.txt`.
   - Create a `.env` file in the root directory and add your Discord bot token like so:
     ```
     DISCORD_TOKEN=your_bot_token_here
     ```

4. **Running the bot**:
   - Run the bot with `python bot.py` from the command line.

5. **Verify bot status**:
   - After running the bot, it should appear online in your Discord server.
   - Test the bot's functionality with the `$help` command to ensure it's working properly.

## Usage

### Auction Commands

- `$startauction <item> <starting_bid> <min_increment> <duration>`: Starts an auction with a specified item, starting bid, minimum increment, and duration. Example: `$startauction "Rare Painting" 1000 100 2h 30m`
  - Aliases: `$sa`, `$beginauction`, `$start`
  
- `$bid <bid_amount>`: Places a bid on the active auction with the given bid amount. Example: `$bid 1500`
  - Aliases: `$placebid`, `$b`
  
- `$closeauction <auction_id>`: Closes the auction with the given auction ID. This is typically used by the server staff to end an auction manually. Example: `$closeauction 1`
  - Aliases: `$ca`, `$endauction`, `$close`, `$end`
  
- `$ongoingauctions`: Lists all ongoing auctions in the server.
  - Aliases: `$currentauctions`, `$activeauctions`, `$active`, `$ongoing`, `$current`

### Help Command

- `$help`: Displays a list of available commands and their descriptions.

## Contributors
- [*Vessel9817*](https://github.com/Vessel9817)
- [*LazyMelon*](https://github.com/LazyCorpz)

## Notes

- Replace `$` with your server's command prefix if it is different.
- To use the auction commands, the user must have the appropriate permissions within the Discord server.
- Auction durations can be specified using weeks (w), days (d), hours (h), minutes (m), and seconds (s).
- Bids can be entered in a shorthand notation (e.g., 1k for 1000).
