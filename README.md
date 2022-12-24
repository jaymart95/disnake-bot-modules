 # Disnake - Cog examples

 A collection of cogs built around Disnake Discord API wrapper (Current version 2.7)


 Basically, I created this repo to have a way to implement ideas that I have, when I have them.  It helps me keep in practice while I'm still learning, even when I don't have a bot or other project to work on. And provides at the very least some referential material for someone looking to implement similar features in their own bots.

 The idea here is to be able to just load any of the cog modules directly into a bot using the Disnake library with very minimal effort.  Any other Python libs based around discord.py should be able to use these as well with a bit of tweaking (but I don't plan to test and confirm this)



 ### Upcoming Modules
Module ideas I have noted and will eventually work on adding.  

- Ticket module using new forum threads and simple json file for persistence | [Planned] 
- Ticket module using regular threads | [Planned]
- Basic mod module | [Planned] 

&nbsp;




### Modules
*Be sure to read the module directly as each has more details and config instructions (if applicable) in a docstring at the top*

Name<br>(Version) | Description | Requirements
--- | --- | ---
[help.py](https://raw.githubusercontent.com/dlchamp/disnake-bot-modules/main/cogs/help.py)<br>(0.1.0) | This module adds a `/help` command to your bot that will construct an embed to display commands and their descriptions split by type (Admin, slash, user, or message app commands) You can also specify a command to view detailed info about it | No special requirements
[matchmaker.py](https://raw.githubusercontent.com/dlchamp/disnake-bot-modules/main/cogs/matchmaker.py)<br>(0.2.0) | A simple team generator module.  Use the `/matchmaker` command to generate an embed where users can join/leave queue. Once the command user is ready, it will automatically split the members up into 2 even teams | No special requirements
[invite_tracker.py](https://raw.githubusercontent.com/dlchamp/disnake-bot-modules/main/cogs/invite_tracker.py)<br>(0.1.2) | Adds the ability to track who invited who by keeping up with guild's active invites. When a new user joins, a welcome message is sent to the configured channel or system channel, or first text channel the bot has permission to view and send messages in showing who joined, and who's invite was used | No special requirements
[simplepoll.py](https://raw.githubusercontent.com/dlchamp/disnake-bot-modules/main/cogs/simplepoll.py)<br>(0.3.0) | Adds a `/poll` command that will allow users to create polls with up to 25 options. Give it a title and/or description, and set how long the poll should be active.  Each new vote will update the embed with a pie chart showing the votes, count, and percentage.  At the end it will display which option won and with how many votes.  If a tie, it will display all options that tied and the votes they were tied with | Requires [matplotlib==3.6.2](https://pypi.org/project/matplotlib/)
[giveaway.py](https://raw.githubusercontent.com/dlchamp/disnake-bot-modules/main/cogs/giveaway.py)<br>(0.1.0) | Adds a `/giveaway` command that will send an embed to the channel with giveaway info.  Users can join with a simple button click.  When the giveaway has ended, users will not be able to join, but the command user will be able to randomly select a winner with the click of a button and the embed will be updated with the member who won | No special requirements
[admin.py](https://raw.githubusercontent.com/dlchamp/disnake-bot-modules/main/cogs/admin.py)<br>(0.1.0) | A super basic Moderation cog.  By default these command are only viewable by members with the Administrator permissions.  This can be altered using the guild > integration tab where you can whitelist other roles or members. These commands also require that both the bot and member have necessary permissions to use any specific command.  | No special requirements