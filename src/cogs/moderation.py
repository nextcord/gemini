from typing import Union

from nextcord import Member, DiscordException, Embed
from nextcord.ext.commands import Cog, Context, command

from src import Bot
from src.models.infraction import Infraction, InfractionType
from src.helpers.checks import STAFF, is_staff


class Moderation(Cog):
    """A cog for manual moderation commands."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def create_infraction(self, ctx: Context, member: Member, type: int, reason: str) -> bool:
        if not reason:
            await ctx.send(":x: You must provide a reason for moderation actions.")
            return False

        if STAFF in member._roles:
            await ctx.reply("You cannot infract staff members.")
            return False

        infraction = await Infraction.new(self.bot.db, member, ctx.author, type, reason)  # type: ignore
        await ctx.reply(content="Infraction created!", embed=infraction.embed)

        return True

    @staticmethod
    async def try_dm(member: Member, message: str) -> bool:
        try:
            await member.send(message)
        except DiscordException:
            return False
        return True

    @command(name="note")
    @is_staff()
    async def note(self, ctx: Context, member: Member, *, reason: str) -> None:
        """Create a note on a user."""

        await self.create_infraction(ctx, member, InfractionType.NOTE, reason)

    @command(name="warn")
    @is_staff()
    async def warn(self, ctx: Context, member: Member, *, reason: str) -> None:
        """Warn a user."""

        if not await self.create_infraction(ctx, member, InfractionType.WARN, reason):
            return

        await self.try_dm(member, f"You have been warned in nextcord: {reason}")

    @command(name="kick")
    @is_staff()
    async def kick(self, ctx: Context, member: Member, *, reason: str) -> None:
        """Kick a user."""

        if not await self.create_infraction(ctx, member, InfractionType.KICK, reason):
            return

        await self.try_dm(member, f"You have been kicked from nextcord: {reason}")
        await member.kick(reason=reason)

    @command(name="ban")
    @is_staff()
    async def ban(self, ctx: Context, member: Member, *, reason: str) -> None:
        """Ban a user."""

        if not await self.create_infraction(ctx, member, InfractionType.BAN, reason):
            return

        await self.try_dm(member, f"You have been banned from nextcord: {reason}")
        await member.ban(reason=reason)

    @command(name="unban")
    @is_staff()
    async def unban(self, ctx: Context, member: int) -> None:
        """Unban a user."""

        try:
            user = await self.bot.fetch_user(member)
        except DiscordException:
            await ctx.reply("API Error: Invalid user.")
            return

        await ctx.guild.unban(user)  # type: ignore
        await ctx.reply("Member has been unbanned.")

    @command(name="cases")
    @is_staff()
    async def cases(self, ctx: Context, member: Union[Member, int]) -> None:
        """Get cases for a user."""

        if isinstance(member, Member):
            member = member.id

        cases = await Infraction.find_member_infractions(self.bot.db, member)

        if not cases:
            await ctx.reply("No cases were found for that user.")
            return

        content = "\n".join([case.short for case in cases])

        embed = Embed(
            title=f"Cases for {member}",
            description=content,
            colour=0x87CEEB,
        )

        await ctx.reply(embed=embed)

    @command(name="case")
    @is_staff()
    async def case(self, ctx: Context, id: int) -> None:
        """Get details about a specific case."""

        case = await Infraction.find_infraction(self.bot.db, id)

        if not case:
            await ctx.reply("There is no case with that ID.")
            return

        await ctx.reply(embed=case.embed)


def setup(bot: Bot) -> None:
    """Set up the moderation cog."""

    bot.add_cog(Moderation(bot))
