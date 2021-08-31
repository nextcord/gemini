from os import getenv
from traceback import format_exc
from typing import Optional

from asyncpg import Pool, create_pool
from loguru import logger
from nextcord import Intents
from nextcord.ext.commands import Bot as _BotBase
from nextcord.ext.commands import Context


class Bot(_BotBase):
    """A subclass of nextcord.ext.commands.Bot"""

    db: Pool

    def __init__(self) -> None:
        intents = Intents()
        intents.members = True

        super().__init__(
            command_prefix="!",
            help_command=None,
            case_insensitive=True,
        )

    def load_extensions(self, *exts: str) -> None:
        """Load a set of extensions."""

        failed = 0

        for ext in exts:
            ext = f"src.cogs.{ext}"

            try:
                self.load_extension(ext)
                logger.info(f"Extension {ext} loaded successfully.")
            except Exception as e:
                logger.error(
                    f"Extension {ext} raised an error while being loaded: {e}\n{format_exc()}"
                )
                failed += 1

        logger.info(
            f"Extension loading has been completed. ({len(exts)} total, {failed} failed)"
        )

    async def _db_init(self) -> None:
        logger.info("Connecting to Postgres...")
        self.db = await create_pool(dsn=getenv("DATABASE_ADDR"))  # type: ignore

        with open("./src/data/0001-init.sql") as f:  # TODO: Improve database
            await self.db.execute(f.read())  # type: ignore

        logger.info("Database connected.")

    async def start(self, *args, **kwargs) -> None:
        await self._db_init()

        await super().start(*args, **kwargs)
