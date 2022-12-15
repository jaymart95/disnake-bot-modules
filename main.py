"""
A simple boilerplate bot main module to create a bot and load
the available cogs.

More for my testing and not really for your use
"""

import asyncio
import os
import sys

import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from loguru import logger

load_dotenv(".env", override=True)


INTENTS = disnake.Intents.all()
TOKEN = os.getenv("TOKEN")


class MyBot(commands.InteractionBot):
    """base bot instance"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    async def on_ready(self) -> None:
        print("Ready")

    def load_extensions(self, path: str) -> None:

        for module in os.listdir(path):
            name, ext = os.path.splitext(module)

            if "__" in name or ext != ".py":
                continue

            extension = f"cogs.{name}"

            super().load_extension(extension)
            logger.info(f"Cog loaded: {extension}")


async def main() -> None:
    """Constructs bot, load extensions, and starts bot"""

    bot = MyBot(intents=INTENTS, reload=True)

    try:
        bot.load_extensions("cogs/")
    except Exception:
        await bot.close()
        raise

    logger.info("Starting bot")
    await bot.start(TOKEN or "")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
