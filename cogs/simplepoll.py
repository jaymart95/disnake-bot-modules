"""
MIT License

Copyright (c) 2022 DLCHAMP

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------
Disnake Simple Poll - 0.1.0
------------------------------
A Simple poll module that allows users to create polls with up to 25 options

Keeps track of poll time remaining and announces the winning option when the time expires

Commands:
`/poll` [description] [expires_in] [options]
- description should be a short description on what is being voted on
- expires_in should be a number followed by s, m, or h (seconds, minutes, hours)
- options should be a comma separated list of options (min=2, max=25) example: red, green, blue
"""
import datetime

import disnake
from disnake.ext import commands


class PollOptions(disnake.ui.StringSelect):
    """Select that holds the options"""

    def __init__(self, options: list[str]) -> None:

        options: list[disnake.SelectOption] = [
            disnake.SelectOption(label=o, value=o) for o in options
        ]
        super().__init__(placeholder="Vote Now!", min_values=1, max_values=1, options=options)

    async def callback(self, inter: disnake.MessageInteraction) -> None:
        """Handle the poll option selection"""
        if inter.author.id in self.view.voted:
            return await inter.response.send_message("Hey! You already voted!", ephemeral=True)

        selected_option = self.values[0]
        self.view.add_vote(inter.author.id, selected_option)
        await inter.response.send_message(
            f"Your vote for {selected_option} has been counted!", ephemeral=True
        )


class PollView(disnake.ui.View):
    """Poll instance view - stores the poll counts and the options, and the time at which it expires"""

    message: disnake.Message

    def __init__(self, expires_at: datetime.datetime, /, options: list[str]) -> None:
        timeout = (expires_at - disnake.utils.utcnow()).seconds
        super().__init__(timeout=timeout)
        self.counts: dict[str, int] = dict.fromkeys(options, 0)
        self.voted: list[int] = []

        self.add_item(PollOptions(options))

    def add_vote(self, member_id: int, option: str) -> None:
        """Update the count for a vote"""
        self.counts[option] += 1
        self.voted.append(member_id)

    def select_winners(self) -> list[tuple[str, int]]:
        """Return the option with the most votes or return options with highest vote if tie"""
        sorted_options = {
            k: v for k, v in sorted(self.counts.items(), reverse=True, key=lambda option: option[1])
        }
        values = list(sorted_options.values())
        return [(k, v) for k, v in sorted_options.items() if v == values[0] and v != 0]

    def create_announce_embed(self, winners: list[tuple[str, int]]) -> disnake.Embed:
        """Create the embed announcing the winner(s)"""
        embed = disnake.Embed(title="And the winner is...")
        if len(winners) == 0:
            embed.description = "There were no winners. Nobody voted!"

        elif len(winners) == 1:
            option, count = winners[0]
            embed.description = f"**{option}** with {count} votes!"
        else:

            options = "\n".join([f"**{o[0]}**" for o in winners])
            count = winners[0][1]
            embed.description = f"It's a {len(winners)} tie with {count} votes each!\n{options}"

        return embed

    async def on_timeout(self) -> None:
        """Poll and view have timed out - update the embed with winning option and remove buttons"""
        winners = self.select_winners()
        embed = self.create_announce_embed(winners)

        await self.message.edit(embed=embed, view=self.clear_items())


class SimplePoll(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="poll")
    async def create_poll(
        self,
        inter: disnake.GuildCommandInteraction,
        *,
        options: str,
        expires_in: str,
        description: str | None = None,
    ) -> None:
        """Create a new poll

        Parameters
        ----------
        description: :type:`str`
            Provide some information about this poll
        expires_in: :type:`str`
            Amount of time this poll is active (s= seconds, m = minutes, h= hours, example: 1h)
        options: :type:`str`
            Add up to 25 options as a comma separated list (ex: Waffles, Pancakes, Biscuits,...)
        """
        options: set[str] = set([o.strip() for o in options.split(",")])

        if len(options) < 2:
            return await inter.response.send_message(
                f"Please include more than {len(options)} options for the poll.", ephemeral=True
            )
        if len(options) > 25:
            return await inter.response.send_message(
                "You can only have max 25 options", ephemeral=True
            )

        if expires_in[-1] not in ["m", "s", "h"]:
            return await inter.response.send_message(
                "You must use `m` for minutes, `s` for seconds, or `h` for hours", ephemeral=True
            )

        expires_at = self.calculate_expired_datetime(expires_in)
        view = PollView(expires_at, options)
        embed = self.build_poll_embed(inter.author, expires_at, description)

        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()
        # await inter.response.send_message(str(expires_at), ephemeral=True)

    def build_poll_embed(
        self, author: disnake.Member, expires_at: datetime.datetime, description: str | None
    ) -> disnake.Embed:
        embed = disnake.Embed(title="Vote Now!")
        embed.description = (
            f"{author.mention} created a poll and is looking for votes!.  Select an option below to secure your vote now!"
            if description is None
            else description
        )
        embed.add_field(
            name="\u200b", value=f'This poll expires {disnake.utils.format_dt(expires_at, "R")}'
        )

        return embed

    def calculate_expired_datetime(self, expires_in: str) -> datetime.datetime:
        """Calculates the datetime when the poll expires"""
        now = disnake.utils.utcnow()
        time = int("".join(c for c in expires_in if c.isdigit()))
        metric = expires_in[-1]
        if metric == "s":
            return now + datetime.timedelta(seconds=time)
        if metric == "m":
            return now + datetime.timedelta(minutes=time)
        if metric == "h":
            return now + datetime.timedelta(hours=time)


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(SimplePoll(bot))
