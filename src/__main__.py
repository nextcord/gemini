from os import getenv
import os
from dotenv import load_dotenv
from loguru import logger

from bot import Bot
TOKEN = os.getenv("BOT_TOKEN")

def main() -> None:
    """Run the bot."""

    if not getenv("USING_DOCKER"):
        load_dotenv()

    bot = Bot()
    bot.load_extensions(
        "ping",
        "moderation",
        "vincentrps",
    )

    logger.info("Starting bot...")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()