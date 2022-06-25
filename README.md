# disnake-bot-modules
 A collection of cogs build around Disnake Discord API wrapper (Current version 2.4)

 This collection is more or less just me practicing different bot types, while also attempting to make it easier to incorporate each module into your already running bots. It will be updated over time.



 ## Modules in Collection

 ### Trivia
 Using the free Open Trivia Database, this bot module is designed to ask your members trivia questions from a wide range of topics and varying difficulties.

 To setup this module, you'll need the following packages:

Package | Pip command
---|---
disnake v2.5.1 | `pip install disnake==2.5.1`
python-dotenv v0.20 | `pip install python-dotenv==0.20.0`
SQLAlchemy v1.4.39 | `pip install sqlalchemy==1.4.39`
Tabulate v0.8.10 | `pip install tabulate==0.8.10`


One first run, when the cog is loaded it wil scrape the OpenTDB categories and load them into /data/categories.json. This will happen each time the bot is restarted, though the category list should rarely change, if ever.
A sqlite database will also be generated and tables built within modules/trivia/data/.  SQLite is fine for a single server bot, but if you wish to integrate your own database, it is up to you to make the code adjustments.



### Teams
Create custom team v team matches for your server with ease using just a `/play` command.  An embed is displayed that allows players to join/leave the queue. Embed is updated in real-time.  When ready use the [Play] button when you're ready.  The following events take place:
1. A category with a name of "Match {number}" is created with two voice channels, "Red Team" and "Blue Team"
2. A counter is added to the matches.json to keep up with how many active matches are happening in the server, only used for category names
3. Players are moved into their respective team's channel (if they are in voice)
4. If maps are provided, a random map is selected for the custom match.

Once finished with a match, the command user can click on the [Finished] button on the updated embed and any categories and channels created for that match will be deleted and the embed itself will be deleted.

Supports up to 10v10 matches.

*No extra dependencies are required.*

#### Notes: Players MUST be in a voice channel when queueing up, this is because they will be moved when everyone is ready to play


