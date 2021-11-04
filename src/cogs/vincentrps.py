from nextcord.ext.commands import Context
from bot import Bot
import re
import os
import nextcord
from models.sphinxreader import SphinxObjectFileReader
from models import fuzzy
from typing import Dict, NamedTuple, Optional
from nextcord.ext import commands
from models.backupnames import backup
from nextcord import (
    Button,
    ButtonStyle,
    ChannelType,
    Colour,
    Embed,
    Guild,
    Interaction,
    Member,
    MessageType,
    Thread,
    ThreadMember,
    ui,
)

class vincentrps(commands.Cog):
    """A cog for any features i decide to add"""

    """Credits:
    Robodanny 
    Previous
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    def parse_object_inv(self, stream: SphinxObjectFileReader, url: str) -> Dict:
        result = {}
        inv_version = stream.readline().rstrip()

        if inv_version != "# Sphinx inventory version 2":
            raise RuntimeError("Invalid objects.inv file version.")

        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]  # not needed

        line = stream.readline()
        if "zlib" not in line:
            raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

        entry_regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result:
                continue

            if directive == "std:doc":
                subdirective = "label"

            if location.endswith("$"):
                location = location[:-1] + name

            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""

            if projname == "nextcord":
                key = key.replace("nextcord.ext.commands.", "").replace("nextcord.", "")

            result[f"{prefix}{key}"] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            sub = cache[key] = {}
            async with self.bot.session.get(page + "/objects.inv") as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        "Cannot build rtfm lookup table, try again later."
                    )

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, ctx, key, obj):
        page_types = {
            "python": "https://docs.python.org/3",
            "master": "https://nextcord.readthedocs.io/en/latest",
        }

        if obj is None:
            await ctx.send(page_types[key])
            return

        if not hasattr(self, "_rtfm_cache"):
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        obj = re.sub(r"^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)", r"\1", obj)
        obj = re.sub(r"^(?:nextcord\.(?:ext\.)?)?(?:commands\.)?(.+)", r"\1", obj)

        if key.startswith("master"):
            # point the abc.Messageable types properly:
            q = obj.lower()
            for name in dir(nextcord.abc.Messageable):
                if name[0] == "_":
                    continue
                if q == name:
                    obj = f"abc.Messageable.{name}"
                    break

        cache = list(self._rtfm_cache[key].items())

        def transform(tup):
            return tup[0]

        matches = fuzzy.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        e = nextcord.Embed(colour=nextcord.Colour.blurple())
        if len(matches) == 0:
            return await ctx.send("Could not find anything. Sorry.")

        e.description = "\n".join(f"[`{key}`]({url})" for key, url in matches)
        ref = ctx.message.reference
        refer = None
        if ref and isinstance(ref.resolved, nextcord.Message):
            refer = ref.resolved.to_reference()
        await ctx.send(embed=e, reference=refer)

    @commands.command(
        name="rtfm",
        help="nextcord documentation search",
        aliases=["rtfd"],
        invoke_without_command=True,
    )
    async def rtfm_group(self, ctx: commands.Context, *, obj: str = None):
        await self.do_rtfm(ctx, "master", obj)

    # @rtfm_group.command(name="python", aliases=["py"])
    # async def rtfm_python_cmd(self, ctx: commands.Context, *, obj: str = None):
    # await self.do_rtfm(ctx, "python", obj)

    @commands.command(
        help="delete cache of rtfm (owner only)", aliases=["purge-rtfm", "delrtfm"]
    )
    @commands.is_owner()
    async def rtfmcache(self, ctx: commands.Context):
        del self._rtfm_cache
        embed = nextcord.Embed(
            title="Purged rtfm cache.", color=nextcord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="vincentworks")
    async def vincentworks(self, message, ctx: Context):
        await message.channel.send("Vincent's Cog Has been loaded!")

    @commands.command(name="help")
    async def help(self, message):
        await message.channel.send("**Coming Soon**")

    @commands.command(name="tag")
    async def tag(self, message):
        await message.channel.send("||Coming Soon||")

    @commands.command()
    async def temp(self, message):
        pass
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens For A Message In The Available Help Channels Category"""
        pass

    @commands.command(name="close")
    async def close(self, message):
        """Closes A Thread"""
        pass

def setup(bot: Bot) -> None:
    """Setting Up My Cog"""

    bot.add_cog(vincentrps(bot))
