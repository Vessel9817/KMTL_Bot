# cogs/help.py
import discord
from discord.ext import commands
import logging
from typing import Any

logger = logging.getLogger("discord_bot")


class CustomHelp(commands.HelpCommand):
    def __init__(self, command_prefix: str, **options: Any) -> None:
        super().__init__(**options)
        self.command_prefix = command_prefix

    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        help_embed = discord.Embed(title="Auction Bot Commands", color=0x00FF00)
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                help_embed.add_field(
                    name=cog_name, value="\n".join(command_signatures), inline=False
                )

        await channel.send(embed=help_embed)

    async def send_command_help(self, command):
        channel = self.get_destination()
        help_embed = discord.Embed(
            title=self.get_command_signature(command),
            description=command.help,
            color=0x00FF00,
        )
        await channel.send(embed=help_embed)

    def get_command_signature(self, command):
        aliases = " | ".join(command.aliases)
        signature = "%s%s %s" % (
            self.command_prefix,
            command.qualified_name,
            command.signature,
        )
        return signature + (f' \n(Aliases: {aliases})\n' if aliases else '')


async def setup(bot):
    bot.help_command = CustomHelp(bot.command_prefix)
    logger.info("Help cog loaded")
