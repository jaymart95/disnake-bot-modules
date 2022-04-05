# disnake-bot-modules
 A collection of cogs build around Disnake Discord API wrapper (Current version 2.4)

 This collection is more or less just me practicing different bot types, while also attempting to make it easier to incorporate each module into your already running bots. It will be updated over time.



 ## Modules in Collection

 ### Trivia
 Using the free Open Trivia Database, this bot module is designed to ask your members trivia questions from a wide range of topics and varying difficulties.

 To setup this bot, you'll need the following packages:

Package | Pip command
---|---
disnake v2.4 | `pip install disnake==2.4.0`
python-dotenv v0.20 | `pip install python-dotenv==0.20.0`
SQLAlchemy v1.4.34 | `pip install sqlalchemy==1.4.34`
Tabulate v0.8.9 | `pip install tabulate==0.8.9`

Or you can use `pip install -r trivia_requirements.txt to get all of them at once.


One first run, when the cog is loaded it wil scrape the OpenTDB categories and load them into /data/categories.json. This will happen each time the bot is restarted, though the category list should rarely change, if ever.
A sqlite database will also be generated and tables built within _trivia/data/.  SQLite is fine for a single server bot, but if you wish to integrate your own database, it is up to you to make the code adjustments.

