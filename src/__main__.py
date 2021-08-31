from os import getenv

from dotenv import load_dotenv
from loguru import logger

from . import Bot


def main() -> None:
    """Run the bot."""

    if not getenv("USING_DOCKER"):
        load_dotenv()

    bot = Bot()
    bot.load_extensions(
        "ping",
    )

    logger.info("Starting bot...")
    bot.run(getenv("BOT_TOKEN"))


if __name__ == "__main__":
    main()
