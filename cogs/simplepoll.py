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
Disnake Simple Poll - 0.3.0
------------------------------
A Simple poll module that allows users to create polls with up to 25 options
Keeps track of poll time remaining and announces the winning option when the time expires

While the poll is active and as votes roll in, the embed will be updated with a pie chart 
that will update with each vote showing the current poll numbers

Commands:
`/poll` [options] (title) (description) (expires_in)
- [required] options: Add up to 25 options as a comma separated list (ex: Waffles, Pancakes, Biscuits,...)
- (optional) title: Provide a title for the poll  
- (optional) description: Provide a description for the poll
- (optional) expires_in: Amount of time this poll is active (s/seconds, m/minutes, h/hours) (default: 10m)
"""
import datetime
import io
import math

import disnake
import matplotlib.pyplot as plt
from disnake.ext import commands


def value_format(value: float) -> str:
    """Custom format for pie chart to display value (percentage)"""
    return f"{value//100} ({value:.2%})"


def build_plot(data: dict[str, int]) -> None:
    """Builds and returns the pie chart as a disnake.File"""
    labels = []
    votes = []
    vote_sum = sum(data.values())

    for k, v in data.items():
        if v != 0:
            labels.append(k)
            votes.append(v)

    def explode():
        values = []
        for i in votes:
            if i == max(votes):
                values.append(0.07)
            else:
                values.append(0.0)
        return tuple(values)

    def format_values(x: float) -> str:
        """Format the values as `value (percentage)`"""
        return f"{math.floor(x / vote_sum)} ({x/100:.2%})"

    # create the pie chart
    _, ax = plt.subplots()
    ax.pie(
        votes, labels=labels, autopct=format_values, startangle=0, explode=explode(), shadow=True
    )
    ax.axis("equal")

    # stores the pie chart image as bytes and returns as disnake.File
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    return disnake.File(buffer, filename="poll.png")


async def options_to_string(inter: disnake.GuildCommandInteraction, options: str) -> set[str]:
    """Converts the passed options to a set and returns or raises an error"""

    options: set[str] = set([o.strip() for o in options.split(",")])

    if len(options) < 2:
        raise Exception(f"⚠️ Please include more than {len(options)} options for the poll.")
    if len(options) > 25:
        raise Exception("⚠️ You can only have max 25 options")

    return options


async def check_expires_in_format(inter: disnake.GuildCommandInteraction, expires_in: str) -> str:
    """Verifies the argument value for expires_in is correct and returns it, or raises an error"""
    time, metric = expires_in[:-1], expires_in[-1].lower()
    if not time.isdigit() or metric.isdigit():
        raise Exception(f"⚠️ `expires_in` must much the correct format: `1s`, `1m`, or `1h`")

    if metric not in ("s", "m", "h"):
        raise Exception(
            f"⚠️ `expires_in` must include one of `s`, `m`, `h` to represent seconds, minutes, or hours"
        )

    return int(time), metric


class PollOptions(disnake.ui.StringSelect):
    """Select that holds the options"""

    def __init__(self, options: set[str]) -> None:

        options: list[disnake.SelectOption] = [
            disnake.SelectOption(label=o, value=o) for o in options
        ]
        super().__init__(
            placeholder="Select an Option!", min_values=1, max_values=1, options=options
        )

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

    def __init__(self, timeout: float, embed: disnake.Embed, /, options: set[str]) -> None:

        super().__init__(timeout=timeout - 2)
        self.counts: dict[str, int] = dict.fromkeys(options, 0)
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

    async def cog_slash_command_error(
        self, inter: disnake.GuildCommandInteraction, error: Exception
    ) -> None:
        """Catches all options that are raised within this cog"""
        if isinstance(error, commands.ConversionError):
            return await inter.response.send_message(str(error.original), ephemeral=True)

        raise

    @commands.slash_command(name="poll")
    async def create_poll(
        self,
        inter: disnake.GuildCommandInteraction,
        *,
        options: list[str] = commands.Param(converter=options_to_string),
        expires_in: str = commands.Param(
            convert_defaults=True, converter=check_expires_in_format, default="10m"
        ),
        title: str = commands.Param(default="Poll!"),
        description: str | None = commands.Param(default=None),
    ) -> None:
        """Create a new poll

        Parameters
        ----------
        options: :type:`str`
            Add up to 25 options as a comma separated list (ex: Waffles, Pancakes, Biscuits,...)
        expires_in: :type:`str`
            Amount of time this poll is active (s/seconds, m/minutes, h/hours) (default: 10m)
        title: :type:`str`
            Provide a title for the poll
        description: :type:`str`
            Provide a description for the poll

        """

        expires_at, timeout = self.calculate_expiration(expires_in)
        embed = self.build_poll_embed(inter.author, expires_at, title, description)
        view = PollView(timeout, embed, options=options)

        await inter.response.send_message(embed=embed, view=view)

        # since interaction responses do not normally return a message, we need to fetch it here
        # to pass to the view for editing later
        view.message = await inter.original_message()

    def build_poll_embed(
        self,
        author: disnake.Member,
        expires_at: datetime.datetime,
        title: str | None,
        description: str | None,
    ) -> disnake.Embed:
        embed = disnake.Embed(title=title)
        embed.set_author(
            name=author.display_name,
            icon_url=author.display_avatar.url if author.display_avatar else disnake.utils.MISSING,
        )
        embed.description = (
            f"{author.mention} created a poll and is looking for votes!.  Select an option below to secure your vote now!"
            if description is None
            else description
        )
        embed.add_field(
            name="\u200b", value=f'This poll expires {disnake.utils.format_dt(expires_at, "R")}'
        )

        return embed

    def calculate_expiration(self, expires_in: tuple[str, str]) -> tuple[datetime.datetime, float]:
        """Calculates the datetime when the poll expires"""
        now = disnake.utils.utcnow()
        time, metric = expires_in

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
