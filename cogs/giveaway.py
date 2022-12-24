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
Disnake Simple Giveaway - 0.1.0
------------------------------
A simple giveaway module that allows users to create giveaways within a channel.  Other members will
have the opportunity to sign up for the giveaway via a simple button click.  All members that sign up 
will be stored and randomly selected from when the giveaway host selects the [Select Winner] button.
At this time a winner will be selected at random and announced via an updated embed.

Command user will also set the amount of time the sign ups are open via the `expires_in` argument.
Should follow the simple format (s, m, h, d) for seconds, minutes, hours, days.  (example: 5d) for 5 days

Commands:
`/giveaway` [prize] (title) (description) (expires_in)
- [required] prize: Prize that is being given away
- (optional) title: Title of the giveaway. If no title provided, the default "Giveaway Time!" will be used
- (optional) description: Description of the giveaway
- (optional) expires_in: Amount of time users will have to sign up for this giveaway. Defaults to 5d

"""

import asyncio
import random
from datetime import datetime, timedelta

import disnake
from disnake.ext import commands


class GiveawayView(disnake.ui.View):

    message: disnake.Message

    def __init__(
        self,
        author: disnake.Member,
        embed: disnake.Embed,
        expires_at: datetime,
        prize: str,
    ) -> None:
        super().__init__(timeout=None)

        self.author: disnake.Member = author
        self.embed: disnake.Embed = embed
        self.expires_at: datetime = expires_at
        self.prize: str = prize

        self.members: list[disnake.Member] = []

    def stop(self) -> None:
        self.members.clear()
        super().stop()

    async def update_embed(self) -> None:
        """Each time someone joins the giveaway, we'll update the message"""
        self.embed.set_footer(text=f"{len(self.members)} entries")

        await self.message.edit(embed=self.embed)

    def is_expired(self) -> bool:
        """Check if the giveaway is expired or not"""
        return disnake.utils.utcnow() >= self.expires_at

    def select_a_winner(self) -> disnake.Member:
        """Randomly select a winner from the participants and return the selected member"""

        count = len(self.members)
        if count == 0:
            return

        random.shuffle(self.members)
        sample_size = count if count < 5 else 5

        group = random.sample(self.members, k=sample_size)
        return random.choice(group)

    @disnake.ui.button(label="Join Giveaway!", style=disnake.ButtonStyle.primary)
    async def join(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:

        if self.is_expired():
            self.join.disabled = True
            await self.message.edit(view=self)
            return await inter.response.send_message(
                "The join period for this giveaway has ended.", ephemeral=True
            )

        if inter.author in self.members:
            return await inter.response.send_message(
                "Sorry.  You're not allowed to enter more than once.", ephemeral=True
            )

        self.members.append(inter.author)

        await self.update_embed()
        await inter.response.send_message(
            "Congrats! You have been entered in to the giveaway!", ephemeral=True
        )

    @disnake.ui.button(label="Select Winner", style=disnake.ButtonStyle.secondary)
    async def select_winner(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:

        if inter.author.id != self.author.id:
            return await inter.response.send_message(
                "Only the giveaway owner can do this.", ephemeral=True
            )

        await inter.response.defer(with_message=True, ephemeral=True)
        await asyncio.sleep(
            1 if len(self.members) < 10 else 3 if 20 < len(self.members) < 50 else 5
        )

        winner = self.select_a_winner()
        if winner is None:
            return await self.cancel.callback(inter)

        embed = disnake.Embed(
            title=self.embed.title,
            description=f"Thank you to all {len(self.members)} members that joined our giveaway.\n\n"
            f"Congrats to {winner.mention}! You are the lucky winner of {self.prize}\n\n"
            "Please reach out to an admin or moderator to claim your prize!",
        )

        await self.message.edit(embed=embed, view=self.clear_items())
        await inter.edit_original_response(
            f"Giveaway has closed and {winner.mention} was selected!"
        )
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:

        if inter.author.id != self.author.id:
            return await inter.response.send_message(
                "Only the giveaway owner can do this.", ephemeral=True
            )

        embed = disnake.Embed(
            title=self.embed.title,
            description=f"This giveaway has been cancelled by {inter.author.mention}",
        )

        await self.message.edit(embed=embed, view=self.clear_items())

        if (
            inter.response._response_type is None
        ):  # making sure it was the button that called this function
            await inter.response.send_message("Giveaway has been cancelled", ephemeral=True)
        else:  # select winners has no members, so we just cancel the giveaway and send this message to the command user
            await inter.edit_original_response("Giveaway was cancelled due to nobody joining")
        self.stop()


async def get_future_time(inter: disnake.GuildCommandInteraction, expires_in: str) -> str:
    """Verifies the argument value for expires_in is correct and returns the converted future datetime object, or
    raises an error"""

    time, metric = expires_in[:-1], expires_in[-1].lower()

    if not time.isdigit() or metric.isdigit():
        raise Exception(f"⚠️ `expires_in` must much the correct format: `1s`, `1m`, `1h`, or `1d`")

    now = disnake.utils.utcnow()
    futures = {
        "s": timedelta(seconds=int(time)),
        "m": timedelta(minutes=int(time)),
        "h": timedelta(hours=int(time)),
        "d": timedelta(days=int(time)),
    }

    if not (future := futures.get(metric)):
        raise Exception(
            f"⚠️ `expires_in` must include one of `s`, `m`, `h` to represent seconds, minutes, or hours"
        )

    return now + future


class GiveAway(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    async def cog_slash_command_error(
        self, inter: disnake.GuildCommandInteraction, error: Exception
    ) -> None:
        """Catches all options that are raised within this cog"""
        if isinstance(error, commands.ConversionError):
            return await inter.response.send_message(str(error.original), ephemeral=True)

        raise

    @commands.slash_command(name="giveaway")
    async def giveaway(
        self,
        inter: disnake.GuildCommandInteraction,
        prize: str,
        expires_in: datetime = commands.Param(
            default="5d", convert_defaults=True, converter=get_future_time
        ),
        title: str = "Giveaway Time!",
        description: str | None = None,
    ) -> None:
        """
        Create a new giveaway

        Parameters
        -----------
        prize: :type:`str`
            What is being given away?
        expires_in: :type:`str`
            Amount of time this giveaway is active (s/seconds, m/minutes, h/hours, d/days) (default: 5d)
        title: :type:`str`
            Title this giveaway
        description: :type:`str|None`
            Description for this giveaway
        """

        if description:
            description += "\n" + f'Drawing {disnake.utils.format_dt(expires_in,"R")}'
        else:
            description = f'Drawing {disnake.utils.format_dt(expires_in,"R")}'

        embed = disnake.Embed(
            title=title,
            description=description,
            timestamp=disnake.utils.utcnow(),
            color=disnake.Color.random(),
        )
        embed.add_field(name="Prize:", value=prize)
        embed.set_footer(text="0 entries")

        view = GiveawayView(inter.author, embed=embed, expires_at=expires_in, prize=prize)
        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(GiveAway(bot))
