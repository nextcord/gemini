from nextcord.ext.commands import Cog, Context, command
from bot import Bot
import re
import os
import nextcord
from models.sphinxreader import SphinxObjectFileReader
from models import fuzzy
from typing import Dict, NamedTuple, Optional
from nextcord.ext import commands
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
    ui
)

HELP_CHANNEL_ID: int = 881965127031722004
HELP_LOGS_CHANNEL_ID: int = 883035085434142781
HELPER_ROLE_ID: int = 882192899519954944
CUSTOM_ID_PREFIX: str = "help:"

async def get_thread_author(channel: Thread) -> Member:
    history = channel.history(oldest_first = True, limit = 1)
    history_flat = await history.flatten()
    user = history_flat[0].mentions[0]
    return user


class HelpButton(ui.Button["HelpView"]):
    def __init__(self, help_type: str, *, style: ButtonStyle, custom_id: str):
        super().__init__(label = f"{help_type} help", style = style, custom_id = f"{CUSTOM_ID_PREFIX}{custom_id}")
        self._help_type = help_type

    async def create_help_thread(self, interaction: Interaction) -> None:
        channel_type = ChannelType.private_thread if interaction.guild.premium_tier >= 2 else ChannelType.public_thread
        thread = await interaction.channel.create_thread(
            name = f"{self._help_type} help ({interaction.user})",
            type = channel_type
        )

        await interaction.guild.get_channel(HELP_LOGS_CHANNEL_ID).send(
            content = f"Help thread for {self._help_type} created by {interaction.user.mention}: {thread.mention}!"
        )
        close_button_view = ThreadCloseView()
        close_button_view._thread_author = interaction.user

        type_to_colour: Dict[str, Colour] = {
            "Nextcord": Colour.red(),
            "Python": Colour.green()
        }

        em = Embed(
            title = f"{self._help_type} Help needed!",
            description = f"Alright now that we are all here to help, what do you need help with?",
            colour = type_to_colour.get(self._help_type, Colour.blurple())
        )
        em.set_footer(text = "You and the helpers can close this thread with the button")

        msg = await thread.send(
            content = f"<@&{HELPER_ROLE_ID}> | {interaction.user.mention}",
            embed = em,
            view = ThreadCloseView()
        )
        await msg.pin(reason = "First message in help thread with the close button.")

    async def callback(self, interaction: Interaction):
        if self.custom_id == f"{CUSTOM_ID_PREFIX}slashcmds":
            GIST_URL = "https://gist.github.com/TAG-Epic/68e05d98a89982bac827ad2c3a60c50a"
            ETA_WIKI = "https://en.wikipedia.org/wiki/Estimated_time_of_arrival"
            ETA_HYPER = f"[ETA]({ETA_WIKI} 'abbreviation for estimated time of arrival: the time you expect to arrive')"
            emb = Embed(
                title = "Slash Commands",
                colour = Colour.blurple(),
                description="Slash commands aren't in the main library yet. You can use discord-interactions w/ nextcord for now. "
                            f"To check on the progress (or contribute) see the pins of <#881191158531899392>. No {ETA_HYPER} for now.\n\n"
                            f"(PS: If you are using discord-interactions for slash, please add [this cog]({GIST_URL} 'gist.github.com') "
                            "(link). It restores the `on_socket_response` removed in d.py v2.)"
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return

        confirm_view = ConfirmView()

        def disable_all_buttons():
            for _item in confirm_view.children:
                _item.disabled = True

        confirm_content = "Are you really sure you want to make a help thread?"
        await interaction.response.send_message(content = confirm_content, ephemeral = True, view = confirm_view)
        await confirm_view.wait()
        if confirm_view.value is False or confirm_view.value is None:
            disable_all_buttons()
            content = "Ok, cancelled." if confirm_view.value is False else f"~~{confirm_content}~~ I guess not..."
            await interaction.edit_original_message(content = content, view = confirm_view)
        else:
            disable_all_buttons()
            await interaction.edit_original_message(content = "Created!", view = confirm_view)
            await self.create_help_thread(interaction)


class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self.add_item(HelpButton("Nextcord", style = ButtonStyle.red, custom_id = "nextcord"))
        self.add_item(HelpButton("Python", style = ButtonStyle.green, custom_id = "python"))
        self.add_item(HelpButton("Slash Commands", style = ButtonStyle.blurple, custom_id = "slashcmds"))


class ConfirmButton(ui.Button["ConfirmView"]):
    def __init__(self, label: str, style: ButtonStyle, *, custom_id: str):
        super().__init__(label = label, style = style, custom_id = f"{CUSTOM_ID_PREFIX}{custom_id}")

    async def callback(self, interaction: Interaction):
        self.view.value = True if self.custom_id == f"{CUSTOM_ID_PREFIX}confirm_button" else False
        self.view.stop()


class ConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout = 10.0)
        self.value = None
        self.add_item(ConfirmButton("Yes", ButtonStyle.green, custom_id = "confirm_button"))
        self.add_item(ConfirmButton("No", ButtonStyle.red, custom_id = "decline_button"))


class ThreadCloseView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self._thread_author: Optional[Member] = None

    async def _get_thread_author(self, channel: Thread) -> None:
        self._thread_author = await get_thread_author(channel)

    @ui.button(label = "Close", style = ButtonStyle.red, custom_id = f"{CUSTOM_ID_PREFIX}thread_close")
    async def thread_close_button(self, button: Button, interaction: Interaction):
        if not self._thread_author:
            await self._get_thread_author(interaction.channel)  # type: ignore

        await interaction.channel.send(
            content = "This thread has now been closed. "
                      "Please create another thread if you wish to ask another question."
        )
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.channel.edit(locked = True, archived = True)
        await interaction.guild.get_channel(HELP_LOGS_CHANNEL_ID).send(
            content = f"Help thread {interaction.channel.name} (created by {self._thread_author.name}) has been closed."
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not self._thread_author:
            await self._get_thread_author(interaction.channel)  # type: ignore

        # because we aren't assigning the persistent view to a message_id.
        if not isinstance(interaction.channel, Thread) or interaction.channel.parent_id != HELP_CHANNEL_ID:
            return False

        return interaction.user.id == self._thread_author.id or interaction.user.get_role(HELPER_ROLE_ID)


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
            async with self.bot.session.get(page + '/objects.inv') as resp:
                if resp.status != 200:
                    raise RuntimeError('Cannot build rtfm lookup table, try again later.')

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, ctx, key, obj):
        page_types = {
            'python': 'https://docs.python.org/3',
            'master': 'https://nextcord.readthedocs.io/en/latest',
        }

        if obj is None:
            await ctx.send(page_types[key])
            return

        if not hasattr(self, '_rtfm_cache'):
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        obj = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)
        obj = re.sub(r'^(?:nextcord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)

        if key.startswith('master'):
            # point the abc.Messageable types properly:
            q = obj.lower()
            for name in dir(nextcord.abc.Messageable):
                if name[0] == '_':
                    continue
                if q == name:
                    obj = f'abc.Messageable.{name}'
                    break

        cache = list(self._rtfm_cache[key].items())

        def transform(tup):
            return tup[0]

        matches = fuzzy.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        e = nextcord.Embed(colour=nextcord.Colour.blurple())
        if len(matches) == 0:
            return await ctx.send('Could not find anything. Sorry.')

        e.description = '\n'.join(f'[`{key}`]({url})' for key, url in matches)
        ref = ctx.message.reference
        refer = None
        if ref and isinstance(ref.resolved, nextcord.Message):
            refer = ref.resolved.to_reference()
        await ctx.send(embed=e, reference=refer)

    @commands.command(name="rtfm", help="nextcord documentation search", aliases=["rtfd"], invoke_without_command=True)
    async def rtfm_group(self, ctx: commands.Context, *, obj: str = None):
        await self.do_rtfm(ctx, "master", obj)

    #@rtfm_group.command(name="python", aliases=["py"])
    #async def rtfm_python_cmd(self, ctx: commands.Context, *, obj: str = None):
        #await self.do_rtfm(ctx, "python", obj)

    @commands.command(help="delete cache of rtfm (owner only)", aliases=["purge-rtfm", "delrtfm"])
    @commands.is_owner()
    async def rtfmcache(self, ctx: commands.Context):
        del self._rtfm_cache
        embed = nextcord.Embed(title="Purged rtfm cache.", color=nextcord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="vincentworks")
    async def vincentworks(self, message, ctx: Context):
        await message.channel.send("Vincent's Cog Has been loaded!")

    @commands.command(name="help")
    async def help(self, message):
        await message.channel.send("Vincent's Cog Has been loaded!")

    @commands.command(name="tag")
    async def tag(self, message):
        await message.channel.send("||Coming Soon||")

        async def create_views(self):
            if getattr(self.bot, "help_view_set", False) is False:
                self.bot.help_view_set = True
            self.bot.add_view(HelpView())
            self.bot.add_view(ThreadCloseView())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == HELP_CHANNEL_ID and message.type is MessageType.thread_created:
            await message.delete(delay = 5)
        if isinstance(message.channel, Thread) and \
                message.channel.parent_id == HELP_CHANNEL_ID and \
                message.type is MessageType.pins_add:
            await message.delete(delay = 10)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: ThreadMember):
        thread = member.thread
        if thread.parent_id != HELP_CHANNEL_ID:
            return

        thread_author = await get_thread_author(thread)
        if member.id != thread_author.id:
            return

        FakeContext = NamedTuple("FakeContext", [("channel", Thread), ("author", Member), ("guild", Guild)])

        # _self represents the cog. Thanks Epic#6666
        async def fake_send(_self, *args, **kwargs):
            return await thread.send(*args, **kwargs)

        FakeContext.send = fake_send
        await self.close(FakeContext(thread, thread_author, thread.guild))

    @commands.command()
    @commands.is_owner()
    async def help_menu(self, ctx):
        await ctx.send("Click a button to create a help thread!", view = HelpView())

    @commands.command()
    async def close(self, ctx):
        if not isinstance(ctx.channel, Thread) or ctx.channel.parent_id != HELP_CHANNEL_ID:
            return

        thread_author = await get_thread_author(ctx.channel)
        if thread_author.id == ctx.author.id or ctx.author.get_role(HELPER_ROLE_ID):
            await ctx.send(
                "This thread has now been closed. Please create another thread if you wish to ask another question.")
            await ctx.channel.edit(locked = True, archived = True)
            await ctx.guild.get_channel(HELP_LOGS_CHANNEL_ID).send(
                f"Help thread {ctx.channel.name} (created by {thread_author.name}) has been closed.")


def setup(bot: Bot) -> None:
    """Setting Up My Cog"""

    bot.add_cog(vincentrps(bot))