'''
A simple, boiler plate main.py necessary to only run the bot and load the cogs (modules)
'''

from os import getenv, listdir, path

from disnake import Intents
from disnake.ext import commands
from dotenv import load_dotenv

'''
Add test_guilds = [guildID] as a parameter to commands.Bot if you
with to bypass global slash command registration while testing.

Example
-------
bot = commands.Bot(intents=intents, test_guilds=[1234567890])
'''

# Intialize bot and declare intents
intents = Intents.all()
bot = commands.Bot(intents=intents)



@bot.listen()
async def on_ready():
    print('------------------------------------------------------------------')
    print(f'{bot.user.name} is connected to Discord and listening for events.')



def load_cogs(bot):
    '''load cogs (.py) files location in /cogs'''
    for file in listdir('./cogs'):
        if file.endswith('.py'):
            bot.load_extension(f'cogs.{file[:-3]}')



if __name__ == '__main__':
    load_cogs(bot)
    load_dotenv()
    bot.run(getenv('TOKEN'))
