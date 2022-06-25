"""
A simple, boiler plate main.py necessary to only run the bot and load the cogs (modules)
"""

from os import getenv, listdir

from disnake import Intents
from disnake.ext import commands
from dotenv import load_dotenv

from modules.teams import Teams
from modules.trivia import Trivia

"""
Add test_guilds = [guildID] as a parameter to commands.Bot if you
with to bypass global slash command registration while testing.

Example
-------
bot = commands.Bot(intents=intents, test_guilds=[1234567890])
"""

# Intialize bot and declare intents
intents = Intents.all()
bot = commands.Bot(intents=intents)


@bot.listen()
async def on_ready():
    print("------------------------------------------------------------------")
    print(f"{bot.user.name} is connected to Discord and listening for events.")


# load bot modules
bot.add_cog(Teams(bot))
bot.add_cog(Trivia(bot))


if __name__ == "__main__":
    load_dotenv()
    bot.run(getenv("TOKEN"))
