"""
A very simple random team generator module

Use the /matchmaker command and an embed will be sent to the channel where the
command was used.  This embed will include buttons that will allow members to join
or leave the queue.  Once enough players have joined, the command user will be able 
to click the [Play] button where the embed will be updated with Team One and Team Two
and the members of each team randomized based on the queued players.

The embed will update each time the queue is updated (when someone joins/leaves)

Include a max amount of players that will be allowed to join the queue, or leave it at the 
default 10 players (5v5)

Optionally, you can include a list of maps, where the bot can randomly select and display
the selected map that the match will be played on.

Maps should be entered as a comma separated list (ie:  Breeze, Fracture, Icebox, ...)
You can also include a thumbnail and/or image to be displayed for this match making event.
"""


import math
import random

import disnake
from disnake.ext import commands


class TeamBuilder(disnake.ui.View):
    def __init__(
        self,
        leader: disnake.Member,
        image: disnake.Attachment | None,
        thumbnail: disnake.Attachment | None,
        max_players: int = 10,
        maps: list[str] | None = None,
    ) -> None:
        super().__init__(timeout=None)

        self.leader: disnake.Member = leader
        self.image: disnake.Attachment | None = image
        self.thumbnail: disnake.Attachment | None = thumbnail
        self.max_players: int = max_players
        self.maps: list[str] = maps

        self.queue: list[disnake.Member] = []
        self.embed: disnake.Embed = None  # is set later

    def stop(self) -> None:
        """Clears the queue before calling view.stop()"""
        self.queue.clear()
        super().stop()

    def update_queue_embed(self) -> None:
        """Update the state of the queue embed - update as queue changes"""

        embed = self.embed or disnake.Embed(title="Matchmaker")
        embed.clear_fields()  # just to clear the fields if reusing embed

        if len(self.queue) == 0:
            embed.add_field(name=f"Players in Queue -- [0/{self.max_players}]", value="\u200b")
        else:
            queue = "\n".join([m.mention for m in self.queue])
            embed.add_field(
                name=f"Players in Queue -- [{len(self.queue)}/{self.max_players}]", value=queue
            )

        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail.proxy_url)

        if self.image:
            embed.set_image(ur=self.image.proxy_url)

        self.embed = embed

    def update_buttons(self) -> None:
        """Update the state of the buttons, disable [Join] if `self.max_players` has been reached, or enabled
        otherwise"""

        self.join.disabled = True if len(self.queue) == self.max_players else False
        self.play.disabled = True if len(self.queue) < 2 else False
        self.leave.disabled = True if len(self.queue) == 0 else False

    @disnake.ui.button(label="Join Queue", style=disnake.ButtonStyle.primary)
    async def join(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """Add the interaction user to the queue if they are not already in it"""

        if inter.author in self.queue:
            return await inter.response.send_message(
                "I hate to ruin your excitement but you can only join the queue one time 😀",
                ephemeral=True,
            )

        self.queue.append(inter.author)
        self.update_buttons()
        self.update_queue_embed()

        await inter.message.edit(embed=self.embed, view=self)
        return await inter.response.send_message("Ayyyyy! You joined the queue!.", ephemeral=True)

    @disnake.ui.button(label="Leave Queue", style=disnake.ButtonStyle.secondary)
    async def leave(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """Remove the interaction user from the queue if they area in it"""

        if inter.author not in self.queue:
            return await inter.response.send_message(
                "Wow. You're not even in the queue and you're trying to leave it.  Who hurt you? 😟",
                ephemeral=True,
            )

        self.queue.remove(inter.author)
        self.update_buttons()
        self.update_queue_embed()

        await inter.message.edit(embed=self.embed, view=self)
        return await inter.response.send_message(
            "I removed you from the queue, but I really think you should reconsider joining 😀",
            ephemeral=True,
        )

    @disnake.ui.button(label="Play", style=disnake.ButtonStyle.success)
    async def play(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """Performs the match making process by generating the teams and selecting a map (if available)"""

        if inter.author.id != self.leader.id:
            return await inter.response.send_message(
                f"Only the party leader can start matchmaking. Let {self.leader.mention} that you're ready.",
                ephemeral=True,
            )

        # select a random map
        _map: list[str] | None = random.choice(self.maps) if len(self.maps) > 0 else None

        team_one: list[disnake.Member] = []
        team_two: list[disnake.Member] = []

        # create the teams
        for _ in range(math.ceil(len(self.queue))):
            player = random.choice(self.queue)
            team_one.append(player.mention)
            self.queue.remove(player)

        team_two = [p.mention for p in self.queue]

        embed = disnake.Embed(title="Let's play!", description=f"**Map: {_map}" if _map else None)
        embed.add_field(name="Team One:", value="\n".join(team_one), inline=True)
        embed.add_field(name="Team Two:", value="\n".join(team_two), inline=True)

        await inter.response.edit_message(None, embed=embed, view=self.clear_items())
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.danger)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """Cancels matchmaking, clear the queue and buttons, and stops the view"""

        if inter.author.id != self.leader.id:
            return await inter.response.send_message(
                f"Only {self.leader.mention} can cancel match making. If you do not with to participate, leave the queue instead.",
                ephemeral=True,
            )

        await inter.response.edit_message(
            "Matchmaking has been cancelled.", embed=None, view=self.clear_items()
        )
        self.stop()


class MatchMaker(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot: commands.InteractionBot = bot

    @commands.slash_command(name="matchmaker")
    async def matchmaker(
        self,
        inter: disnake.GuildCommandInteraction,
        max_players: int = commands.Param(le=20, default=10),
        maps: str = None,
        role: disnake.Role | None = None,
        thumbnail: disnake.Attachment | None = None,
        image: disnake.Attachment | None = None,
    ) -> None:
        """Create a custom game among friends

        Parameters
        ----------
        max_player: :type:`Optional[int]`
            The max numbers allowed to queue
        maps: :type:`str`
            Include a comma separated list of maps (ie Breeze, Fracture, Icebox)
        role: :type:`Optional[disnake.Role]`
            Ping a role
        thumbnail: :type:`Optional[disnake.Attachment]`
            Attach an image to be used as the embed thumbnail
        image: :type:`Optional[disnake.Attachment]`
            Attach an image to be used as the larger embed image
        """

        if maps:
            maps = [m.strip() for m in maps.split(",")]

            if len(maps) == 1:
                return await inter.response.send_message(
                    "If you wish to include maps, please make sure they are typed as a comma separated list\n (ie: `Breeze, Fracture, Icebox`)"
                )

        if maps is None:
            maps = []

        if role:
            message = f"{role.mention} "
        else:
            message = ""

        message += f"{inter.author.mention} is looking to play some games!.  Click to join the queue below!"

        view = TeamBuilder(inter.author, image, thumbnail, max_players, maps)
        view.queue.append(inter.author)

        view.update_buttons()
        view.update_queue_embed()

        await inter.response.send_message(message, embed=view.embed, view=view)


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(MatchMaker(bot))
