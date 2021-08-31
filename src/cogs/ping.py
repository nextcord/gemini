from time import time
from typing import Coroutine

from nextcord import Embed
from nextcord.ext.commands import Cog, Context, command

from src import Bot


class Ping(Cog):
    """A cog for a simple ping command."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @staticmethod
    async def timed(coro: Coroutine) -> tuple:
        """Time the execution of a coroutine."""

        start = time()
        result = await coro
        end = time()

        return (result, f"{(end - start) * 1000:.2f}ms")

    @command(name="ping")
    async def ping(self, ctx: Context) -> None:
        """Get the bot's websocket and HTTP ping."""

        send = await self.timed(ctx.send("Testing ping..."))
        msg = send[0]
        edit = await self.timed(msg.edit(content="Testing editing..."))
        delete = await self.timed(msg.delete())

        results = Embed(
            colour=0x87ceeb,
            title="Gemini Ping",
            description=(
                f"🌐 WebSocket latency: {self.bot.latency * 1000:.2f}ms\n"
                f"▶️ Message Send: {send[1]}\n"
                f"🔄 Message Edit: {edit[1]}\n"
                f"🚫 Message Delete: {delete[1]}"
            ),
        )

        await ctx.reply(embed=results)


def setup(bot: Bot) -> None:
    """Set up the ping cog."""

    bot.add_cog(Ping(bot))
