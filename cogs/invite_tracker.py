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


---------------------------------------------------
Disnake Invite Tracker with Welcome Embed - 0.1.0
---------------------------------------------------

A simple Invite tracker that keeps a cache of all guilds and their invites.
It will automatically add the invite to the guild's invite when it is created, 
removed if expires or is deleted, and can get the invite that was used by
the most recent new member

Includes a useable cog that will manage all of this and automatically send
a welcome message to the system channel or first channel that it has permission 
to view/send messages in with an embed that welcomes the new member and shows 
who created the invite that was used.

This module also includes a simple command to show all invites with the url, creator, and uses
for each invite.  This will create a slash command called `/invites` that is useable for any
member that has `manage_guild` permissions
"""

import disnake
from disnake.ext import commands
from loguru import logger


class InviteTracker:
    def __init__(self, bot):
        self.bot = bot
        self.cache: dict[int, dict[str, disnake.Invite]] = {}

        self.bot.add_listener(self.populate_invite_cache, "on_ready")
        self.bot.add_listener(self.add_guild_to_cache, "on_guild_join")
        self.bot.add_listener(self.remove_guild_from_cache, "on_guild_remove")
        self.bot.add_listener(self.add_invite_to_cache, "on_invite_create")
        self.bot.add_listener(self.remove_invite_from_cache, "on_invite_delete")

    async def populate_invite_cache(self) -> None:
        """Populates the InviteTracker's cache on bot ready"""

        for guild in self.bot.guilds:
            try:
                self.cache[guild.id] = {}
                for invite in await guild.invites():
                    self.cache[guild.id][invite.code] = invite

            except disnake.Forbidden:  # missing permission to manage guild
                logger.warning(
                    f"Missing `manage_guild` permissions in {guild.name} ({guild.id}) | Unable to cache invites"
                )
                continue

    async def add_guild_to_cache(self, guild: disnake.Guild) -> None:
        """Adds a guild and it's current invites the cache"""

        self.cache[guild.id] = {}

        for invite in await guild.invites():
            self.cache[guild.id][invite.code] = invite

    async def remove_guild_from_cache(self, guild: disnake.Guild) -> None:
        """Remove a guild from the cache"""
        try:
            self.cache.pop(guild.id)
        except:  # likely the guild just doesn't exist, so we can quietly return
            return

    async def add_invite_to_cache(self, invite: disnake.Invite) -> None:
        """Adds a created invite to the guild's invite cache"""

        if not invite.guild.id in self.cache.keys():
            self.cache[invite.guild.id] = {}

        self.cache[invite.guild.id][invite.code] = invite

    async def remove_invite_from_cache(self, invite: disnake.Invite) -> None:
        """Removes an invite from the cache"""

        if not invite.guild.id in self.cache.keys():
            return

        for _invite in self.cache[invite.guild.id].values():
            if invite.code == _invite.code:
                self.cache[invite.guild.id].pop(invite.code)

    async def get_invite(self, guild: disnake.Guild) -> disnake.Invite | None:
        """Get an invite from the cache"""

        for guild_invite in await guild.invites():
            for cached_invite in self.cache[guild.id].values():
                if (
                    cached_invite.uses < guild_invite.uses
                    and guild_invite.code == cached_invite.code
                ):
                    cached_invite.uses += 1

                    return cached_invite


class Invites(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot: commands.InteractionBot = bot
        self.invite_cache: InviteTracker

    async def get_channel(self, guild: disnake.Guild) -> disnake.TextChannel:
        """Gets the guild's system channel, if present, or it selects the first `disnake.TextChannel` the bot
        has permission to view and send messages in"""

        channel = guild.system_channel

        if channel is None or not self.check_permissions(channel):
            for channel in guild.text_channels:
                if self.check_permissions(channel):
                    return channel

    def check_permissions(self, channel: disnake.TextChannel) -> bool:
        """Checks bot's view and message send permissions for the channel"""
        me = channel.guild.me

        return (
            channel.permissions_for(me).view_channel and channel.permissions_for(me).send_messages
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        """Called when a member joins the guild - Update the invite cache and send welcome message"""

        bot = self.bot
        guild = member.guild

        if invite := await self.invite_cache.get_invite(guild):
            embed = disnake.Embed(description=f"**Welcome {member.mention}!**")
            embed.set_thumbnail(
                url=bot.user.avatar.url
                if bot.user.avatar
                else guild.icon.url
                if guild.icon
                else None
            )
            embed.add_field(name="Invited by:", value=invite.inviter.mention)

            await self.get_channel(guild).send(embed=embed)

    @commands.slash_command(name="invites")
    @commands.default_member_permissions(manage_guild=True)
    async def show_invites(self, inter: disnake.GuildCommandInteraction) -> None:
        """View guild's cached invites"""

        if not inter.guild.me.guild_permissions.manage_guild:
            return await inter.response.send_message(
                "I do not have permission to access this guild's invites.", ephemeral=True
            )

        invites: list[disnake.Invite] = self.invite_cache.cache[inter.guild.id].values()

        if not invites:
            return await inter.response.send_message(
                "This guild has no active invites.",
                ephemeral=True,
            )

        formatted_invites = "\n".join(
            f"Invite Code: {invite.code} | Created by: {invite.inviter.mention} | Uses: {invite.uses}"
            for invite in invites
        )

        await inter.response.send_message(
            formatted_invites,
            ephemeral=True
        )


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(Invites(bot))
