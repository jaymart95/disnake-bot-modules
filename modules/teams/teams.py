from random import choice
from math import ceil
from json import dump, load
from os import path, makedirs

from disnake import (
    ApplicationCommandInteraction,
    MessageInteraction,
    ButtonStyle,
)
from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Embed
from disnake.ui import View, button, Button

# set path to this file's location for relative pathing to json
abs_path = path.dirname(path.realpath(__file__))


def create_json():
    if not path.exists(f"{abs_path}/data"):
        makedirs(f"{abs_path}/data", exist_ok=True)
        with open(f"{abs_path}/data/matches.json", "w+") as file:
            dump({}, file)
        print("Created file: matches.json")


def load_matches_json():
    with open(f"{abs_path}/data/matches.json") as file:
        return load(file)


def dump_matches_json(data):
    with open(f"{abs_path}/data/matches.json", "w") as file:
        dump(data, file)


def active_matches(guild_id: int):
    """returns the count of active matches for the guild"""
    data = load_matches_json()
    if guild_id in data.keys():
        return data[guild_id]
    return 0


def add_match(guild_id: int):
    """adds a match to the guild's match count"""
    data = load_matches_json()
    if guild_id in data.keys():
        data[guild_id] += 1
    else:
        data[guild_id] = 1


def remove_match(guild_id: int):
    """Removes a match from the guilds match count"""
    data = load_matches_json()
    if guild_id in data.keys():
        data[guild_id] -= 1


class MatchButtons(View):
    """Adds buttons to the '/play' command embed for allowing users to
    join/leave the queue"""

    def __init__(self, author, maps):
        super().__init__(timeout=None)
        self.queue = [author]
        self.author = author
        self.maps = maps

    @button(label="Join Queue", style=ButtonStyle.primary)
    async def join_queue(self, button: Button, interaction: MessageInteraction):
        """Adds the user to the queue if they're not already in the queue"""
        member = interaction.author

        # check if member in queue
        if member in self.queue:
            return await interaction.response.send_message(
                f"You can't join a queue you're already in!", ephemeral=True
            )

        # if queue is full
        if len(self.queue) == 20:
            return await interaction.response.send_message(
                f"Sorry, {member.display_name}. The queue is currently full with {len(self.queue)} players.",
                ephemeral=True,
            )

        # member must be in a voice channel to join the queue
        if member.voice is None:
            return await interaction.response.send_message(
                "You must be in a voice channel to join the queue.", ephemeral=True
            )

        # queue not full, add member to queue and update embed
        self.queue.append(member)
        queue = "\n".join([m.display_name for m in self.queue])

        embed = Embed(
            title="Matchmaker",
            description="Start matchmaking! Up to 10 players on each team.\n"
            'Be sure everyone is in a voice channel before clicking "Play"',
        )
        embed.add_field(name=f"In Queue [{len(self.queue)}/20]", value=queue)

        # edit the message with updated embed
        await interaction.message.edit(embed=embed)
        return await interaction.response.send_message(
            f"You joined the queue!", ephemeral=True
        )

    @button(label="Leave Queue", style=ButtonStyle.primary)
    async def leave_queue(self, button: Button, interaction: MessageInteraction):
        """Remove the user from the queue if they are in the queue"""
        member = interaction.author

        # member is not in queue
        if not member in self.queue:
            return await interaction.response.send_message(
                f"Unable to find you in the queue. Are you sure you were in queue already?",
                ephemeral=True,
            )

        # remove member from queue/update embed
        self.queue.remove(member)
        queue = "\n".join([m.display_name for m in self.queue])
        if len(self.queue) == 0:
            queue = "\u200b"

        embed = Embed(
            title="Matchmaker",
            description="Start matchmaking! Up to 10 players on each team.\n"
            'Be sure everyone is in a voice channel before clicking "Play"',
        )
        embed.add_field(name=f"In Queue [{len(self.queue)}/20]", value=queue)

        # edit the message with updated embed
        await interaction.message.edit(embed=embed)
        return await interaction.response.send_message(
            f"You left the queue!", ephemeral=True
        )

    @button(label="Play", emoji="🎮", style=ButtonStyle.success)
    async def play_button(self, button: Button, interaction: MessageInteraction):
        """Starts the match making, displays the teams and moves players in voice to appropriate channels"""

        # only command user can start matchmaker
        if interaction.author != self.author:
            return await interaction.response.send_message(
                f"Sorry. Only {self.author.display_name} can start matchmaking",
                ephemeral=True,
            )

        # if len of queue is <= 2
        if len(self.queue) <= 2:
            return await interaction.response.send_message(
                f"You can't match make with only {len(self.queue)} players in queue.",
                ephemeral=True,
            )

        # split players into teams and select map if available
        red = []
        blue = []
        for i in range(ceil(len(self.queue) / 2)):
            pick = choice(self.queue)
            red.append(pick)
            self.queue.remove(pick)

        blue.extend(self.queue)
        self.queue.clear()
        selected_map = None
        if self.maps:
            selected_map = choice(self.maps)

        # update embed with teams and map (if provided)
        embed = Embed(
            title="Match Found!",
            description="Get to your teams voice channel if you were not already moved.",
        )

        if selected_map:
            embed.add_field(name="Selected Map", value=selected_map)

        embed.add_field(
            name="Red Team", value="\n".join([m.display_name for m in red]), inline=True
        )
        embed.add_field(
            name="Blue Team",
            value="\n".join([m.display_name for m in blue]),
            inline=True,
        )
        embed.set_footer(
            text="Use 'Finished' when the match is over and you're ready to clear this message and delete the channels"
        )

        # check how many active matches then update matches
        match_count = active_matches(interaction.guild.id)
        add_match(interaction.guild.id)

        # create team channels in Match category
        match_category = await interaction.guild.create_category(
            f"Match {match_count + 1:.2f}"
        )
        red_channel = await match_category.create_voice_channel("Red Team")
        blue_channel = await match_category.create_voice_channel("Blue Team")

        # move players to their channels if in voice
        for member in red + blue:
            if member.voice:
                if member in red:
                    await member.move_to(red_channel)
                else:
                    await member.move_to(blue_channel)

        # Edit embed and attach Finished button
        await interaction.message.edit(
            embed=embed,
            view=Finished(self.author, match_category, red_channel, blue_channel),
        )
        return await interaction.response.send_message(
            "Teams and voice channels created, members moved.  Make sure anyone that wasn't moved joins their proper team channel.",
            ephemeral=True,
        )

    @button(label="Cancel", emoji="❌", style=ButtonStyle.danger)
    async def cancel_button(self, button: Button, interaction: MessageInteraction):
        """Cancels the match maker by clearing the queue and removing the embed"""

        if interaction.author != self.author:
            return await interaction.response.send_message(
                f"You do not have permission to cancel the match maker", ephemeral=True
            )

        self.queue.clear()

        await interaction.message.delete()
        await interaction.response.send_message(
            f"Matchmaking has been cancelled.", delete_after=10
        )


class Finished(View):
    """Adds Finished button to remove message and channels when match making is complete"""

    def __init__(self, author, match_category, red_channel, blue_channel):
        super().__init__(timeout=None)
        self.author = author
        self.match_cat = match_category
        self.red = red_channel
        self.blue = blue_channel

    @button(label="Finished", style=ButtonStyle.danger)
    async def finished_button(self, button: Button, interaction: MessageInteraction):
        """Removes created team channels and category and clears the embed message"""
        author = interaction.author

        # if the button press isn't from the original command author
        if author != self.author:
            return await interaction.response.send_message(
                f"You don't have permission to do this.", ephemeral=True
            )

        # delete channels and categories if nobody in them
        if len(self.red.members) != 0 or len(self.blue.members) != 0:
            return await interaction.response.send_message(
                f"Red Team or Blue Team channels are not empty. Please try again",
                ephemeral=True,
            )

        # remove match count
        remove_match(interaction.guild.id)

        await self.red.delete()
        await self.blue.delete()
        await self.match_cat.delete()
        await interaction.message.delete()


class Teams(commands.Cog):
    """Contains Teams commands for generating a match with two teams up to
    10 players on each team"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """invoked when the cog is loaded"""
        # create matches.json if it not exists
        create_json()
        print(f"Cog loaded: {self.qualified_name}")

        create_json()

    @commands.slash_command(name="play")
    async def play_command(
        self, interaction: ApplicationCommandInteraction, maps: str = None
    ):
        """
        Start the matchmaker to create two teams up to 10 players

        Parameters
        ----------
        interaction: disnake.ApplicationCommandInteraction - Represents the interaction instance
        maps: (Optional) Comma separated list of maps to include for random selection
        """

        # split maps into list if passed
        if maps:
            maps = maps.split(",")

        author = interaction.author
        embed = Embed(
            title="Matchmaker",
            description="Start matchmaking! Up to 10 players on each team.\n"
            'Be sure everyone is in a voice channel before clicking "Play"',
        )
        embed.add_field(name="In Queue [1/20]", value=str(author.display_name))

        await interaction.response.send_message(
            f"{author.mention}, matchmaker has started!",
            embed=embed,
            view=MatchButtons(author, maps),
        )
