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

--------------------------------------
Disnake Basic Admin/Moderator - 0.1.0
--------------------------------------
A super basic Moderation cog.  By default these command are only viewable by members with the Administrator permissions.  This
can be altered using the guild > integration tab where you can whitelist other roles or members. These commands also require 
that both the bot and member have necessary permissions to use any specific command.


Commands:
`/kick` [member] (reason)
    - [member] : Member to be kicked.
    - (reason) : Optional reason the user was kicked

`/ban` [member] (reason)
    - [member] : Member to be kicked.
    - (reason) : Optional reason the user was kicked

`/timeout` [member] (duration) (reason)
    - [member] : Member to be kicked.
    - (duration) : Amount of time the member is to be timed out for.  (1s, 1m, 1h, 1d) (set to None to remove any timeout)
    - (reason) : Optional reason the user was kicked
"""

import disnake
from disnake.ext import commands
from datetime import timedelta, datetime


async def get_duration(inter: disnake.GuildCommandInteraction, duration: str) -> datetime:
    """Converts the entered text duration datetime and returns the delta between now and the future date in seconds"""
    if duration.lower() == "none":
        return None

    time, metric = duration[:-1], duration[-1].lower()
    now = disnake.utils.utcnow()
    futures = {
        "s": timedelta(seconds=int(time)),
        "m": timedelta(minutes=int(time)),
        "h": timedelta(hours=int(time)),
        "d": timedelta(days=int(time)),
    }

    if not time.isdigit() or metric.isdigit():
        return await inter.response.send_message(
            f"⚠️ `duration` must much the correct format: `1s`, `1m`, `1h` or `1d`",
            ephemeral=True,
        )

    if metric == "d" and time > 28:
        time == 28

    if not (future := futures.get(metric)):
        return await inter.response.send_message(
            f"⚠️ `duration` must include one of (`s`, `m`, `h`, `d`) to represent seconds, minutes, hours, or days",
            ephemeral=True,
        )

    return now + future


class Moderation(
    commands.Cog,
    slash_command_attrs={"default_member_permissions": disnake.Permissions(administrator=True)},
):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    async def cog_slash_command_error(
        self, inter: disnake.GuildCommandInteraction, error: Exception
    ) -> None:
        """Catches any error that originates from within this cog.  We're only wanting to catch
        missing perms/role errors, other errors are raised"""
        if isinstance(error, commands.BotMissingPermissions):
            return await inter.response.send_message(
                "I do no have the required permissions to perform this action", ephemeral=True
            )

        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message(
                "You have not been granted permission to use this command.", ephemeral=True
            )
        if isinstance(error, disnake.Forbidden):
            return await inter.response.send_message(
                "You cannot perform this action against the selected member", ephemeral=True
            )

        raise  # raise other exceptions

    def create_alert_embed(self, **kwargs) -> disnake.Embed:

        action: str = kwargs.get("action")
        reason: str = kwargs.get("reason") or "None Provided"
        mod: disnake.Member = kwargs.get("mod")
        desc: str = kwargs.get("desc") or None
        member: disnake.Member = kwargs.get("member")

        embed = disnake.Embed(
            title="Moderation Action was Taken",
            description=desc,
            timestamp=disnake.utils.utcnow(),
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Action taken by: {mod.display_name}")

        return embed

    @commands.slash_command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_member(
        self,
        inter: disnake.GuildCommandInteraction,
        *,
        member: disnake.Member,
        reason: str | None = None,
    ) -> None:
        """Kick a member from the guild with an optional reason

        Parameters
        ----------
        member: :type:`disnake.Member`
            Member to kick
        reason: :type:`Optional[str]`
            Include a reason (optional)
        """

        embed = self.create_alert_embed(
            member=member,
            mod=inter.author,
            action="Kick",
            desc=None,
            reason=reason,
        )

        await member.kick(reason=reason)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout_member(
        self,
        inter: disnake.GuildCommandInteraction,
        *,
        member: disnake.Member,
        duration: str = commands.Param(default="5m", convert_defaults=True, converter=get_duration),
        reason: str | None = None,
    ) -> None:
        """Timeout a member

        Parameters
        ----------
        member: :type:`disnake.Member`
            Member to Timeout
        duration: :type:`str`
            Amount of time to timeout the member, set to None to remove (default 5m)
        reason: :type:`Optional[str]`
            Include a reason (optional)
        """
        if member.current_timeout is None and duration is None:
            return await inter.response.send_message(
                f"{member.mention} is not currently timed out", ephemeral=True
            )
        if member.current_timeout is None:
            embed = self.create_alert_embed(
                member=member,
                mod=inter.author,
                action="Timeout",
                desc=f"Expires {disnake.utils.format_dt(duration, 'R')}",
                reason=reason,
            )

        else:
            if duration is None:
                embed = self.create_alert_embed(
                    member=member,
                    mod=inter.author,
                    action="Timeout Removed",
                    desc=None,
                    reason=reason,
                )

        await member.timeout(
            duration=(duration - disnake.utils.utcnow()) if duration is not None else duration,
            reason=reason,
        )
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(
        self,
        inter: disnake.GuildCommandInteraction,
        *,
        member: disnake.Member,
        delete_messages_days: int = 1,
        reason: str | None = None,
    ) -> None:

        """Ban a member

        Parameters
        ----------
        member: :type:`disnake.Member`
            Member to Ban
        delete_message_days: :type:`int
            Removes messages from the past {amount} days (default 1)
        reason: :type:`Optional[str]`
            Include a reason (optional)
        """
        desc = (
            f"Removed messages from last {delete_messages_days} days"
            if delete_messages_days > 0
            else None
        )
        embed = self.create_alert_embed(
            member=member, mod=inter.author, action="Ban", desc=desc, reason=reason
        )
        await member.ban(delete_message_days=delete_messages_days, reason=reason)
        await inter.response.send_message(embed=embed)


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(Moderation(bot))
