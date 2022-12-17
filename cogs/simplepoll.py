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
import io

import disnake
import matplotlib.pyplot as plt
from disnake.ext import commands


def build_plot(data: dict[str, int]) -> None:
    """Builds and returns the pie chart as a disnake.File"""
    labels = []
    sizes = []
    max = sum(data.values())

    for k, v in data.items():
        if v == 0:
            continue
        else:
            labels.append(k)
            sizes.append(round((v / max) * 100, 2))

    _, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return disnake.File(buffer, filename="poll.png")


class PollOptions(disnake.ui.StringSelect):
    """Select that holds the options"""

    def __init__(self, options: dict[str, int]) -> None:

        options: list[disnake.SelectOption] = [
            disnake.SelectOption(label=o, value=o) for o in options.keys()
        ]
        super().__init__(placeholder="Vote Now!", min_values=1, max_values=1, options=options)

    async def callback(self, inter: disnake.MessageInteraction) -> None:
        """Handle the poll option selection"""

        selected_option = self.values[0]

        if inter.author.id in self.view.voted:
            previous_option = self.view.voted.get(inter.author.id)
            self.view.change_vote(inter.author.id, previous_option, selected_option)
            await inter.response.send_message(
                f"Your vote has been changed from {previous_option} to {selected_option}",
                ephemeral=True,
            )
        else:
            self.view.add_vote(inter.author.id, selected_option)
            await inter.response.send_message(
                f"Your vote for {selected_option} has been counted!", ephemeral=True
            )

        await self.view.update_message()


class PollView(disnake.ui.View):
    """Poll instance view - stores the poll counts and the options, and the time at which it expires"""

    message: disnake.Message

    def __init__(self, timeout: float, embed: disnake.Embed, /, options: dict[str, int]) -> None:
        print(timeout)
        super().__init__(timeout=timeout - 2)
        self.counts: dict[str, int] = options
        self.voted: dict[int, str] = {}
        self.embed: disnake.Embed = embed

        self.add_item(PollOptions(options))

    async def update_message(self) -> None:
        """Updates the embed with a new graph image"""
        self.embed.set_image(file=build_plot(self.counts))
        await self.message.edit(embed=self.embed, attachments=None)

    def add_vote(self, member_id: int, option: str) -> None:
        """Update the count for a vote"""
        self.counts[option] += 1
        self.voted[member_id] = option

    def change_vote(self, member_id: int, previous_option: str, option: str) -> None:
        """Change the vote if the user tries to vote again"""

        self.counts[previous_option] -= 1
        self.counts[option] += 1
        self.voted[member_id] = option

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
            embed.description = f"It's a {len(winners)} way tie with {count} votes each!\n{options}"

        return embed

    async def on_timeout(self) -> None:
        """Poll and view have timed out - update the embed with winning option and remove buttons"""
        winners = self.select_winners()
        embed = self.create_announce_embed(winners)
        if winners:
            embed.set_image(file=build_plot(self.counts))

        await self.message.edit(embed=embed, view=self.clear_items(), attachments=None)


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

        expires_at, timeout = self.calculate_expired_datetime(expires_in)
        options_as_dict = dict.fromkeys(options, 0)
        embed = self.build_poll_embed(inter.author, expires_at, description)
        view = PollView(timeout, embed, options=options_as_dict)

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

    def calculate_expired_datetime(self, expires_in: str) -> tuple[datetime.datetime, float]:
        """Calculates the datetime when the poll expires"""
        now = disnake.utils.utcnow()
        time = int("".join(c for c in expires_in if c.isdigit()))
        metric = expires_in[-1]

        if metric == "s":
            future = now + datetime.timedelta(seconds=time)
            timeout = datetime.datetime.timestamp(future) - datetime.datetime.timestamp(now)
        elif metric == "m":
            future = now + datetime.timedelta(minutes=time)
            timeout = datetime.datetime.timestamp(future) - datetime.datetime.timestamp(now)
        elif metric == "h":
            future = now + datetime.timedelta(hours=time)
            timeout = datetime.datetime.timestamp(future) - datetime.datetime.timestamp(now)

        return future, timeout


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(SimplePoll(bot))
