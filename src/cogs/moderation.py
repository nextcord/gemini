from typing import Union

from nextcord import Member, DiscordException, Embed
from nextcord.ext.commands import Cog, Context, command

from bot import Bot

# from models.infraction import Infraction, InfractionType
# from helpers.checks import STAFF, is_staff


class Moderation(Cog):
    """A cog for manual moderation commands."""

    pass
    # def __init__(self, bot: Bot) -> None:
    # self.bot = bot


def setup(bot: Bot) -> None:
    """Set up the moderation cog."""

    bot.add_cog(Moderation(bot))
