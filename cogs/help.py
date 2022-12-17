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
Disnake Basic Help Command - 0.1.0
--------------------------------------

Usage:
General help embed includes a description that can be set by setting a `.description` attribute in your bot instance
(ex: bot.description = "My bot description"  or  do not do this and no help embed description will appear

Message and User context commands do not inherently have a description, so these can be set easily by including
{'desc': "Command description"} in the `extras=` kwarg argument 

(ex: @commands.message_command(name="profile", extras={"desc": "View the user's Discord profile"}) )

Admin commands need to contain "Admin" in the command description/docstring to display them separately in the general embed.
Or you can hide them by setting SHOW_ADMIN_COMMANDS = False
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

import disnake
from disnake.ext import commands

SHOW_ADMIN_COMMANDS = True

DESCRIPTION = None


@dataclass
class Argument:
    """Represents slash command argument"""

    name: str
    required: bool
    description: str


@dataclass
class Command:
    """Represents an API command base"""

    id: int
    name: str
    description: str
    requires_admin: bool


@dataclass
class SlashCommand(Command):
    args: Optional[List[Argument]] = None

    @property
    def mention(self):
        """returns the command as a mentionable string"""
        return f"</{self.name}:{self.id}>"


@dataclass
class UserCommand(Command):
    """Represents a user context command"""

    @property
    def mention(self):
        """returns the command as a mentionable string"""
        return f"`{self.name}`"


@dataclass
class MessageCommand(Command):
    """Represents a message context command"""

    @property
    def mention(self):
        """returns the command as a mentionable string"""
        return f"`{self.name}`"


class Help(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="help")
    async def help_command(
        self, inter: disnake.GuildCommandInteraction, command: Optional[str] = None
    ) -> None:
        """Display some helpful information about the bot and it's commands

        Parameters
        ----------
        command: :type:`Optional[str]`
            Define a command to get specific information about it.
        """
        name = command
        # no specific command passed, show all
        all_commands = self.walk_app_commands(inter.guild.id)

        if name is None:
            # formats all commands to a general help embed
            embed = self.create_help_embed(all_commands)

        if name:
            command = self.get_command_named(name, all_commands)
            embed = self.create_command_detail_embed(command)

        await inter.response.send_message(embed=embed)

    def format_args_as_string(self, args: List[Argument]) -> str:
        """Convert a list of arguments to a formatted string"""
        string = ""
        for arg in args:
            if arg.required:
                string += f"[{arg.name}]"

            else:
                string += f"({arg.name})"

        return string

    def get_command_named(
        self, name: str, commands: List[Union[SlashCommand, MessageCommand, UserCommand]]
    ) -> Union[SlashCommand, UserCommand, MessageCommand]:
        """Gets a single command from all commands and returns the command"""

        for command in commands:
            if name == command.name:
                return command

    def walk_app_commands(
        self, guild_id: int
    ) -> List[Union[SlashCommand, MessageCommand, UserCommand]]:

        global_commands = self.bot.global_application_commands
        guild_commands = self.bot.get_guild_application_commands(guild_id)

        _commands = []

        for command in global_commands + guild_commands:
            if command.name == "help":
                continue

            # if slash command
            if command.type == disnake.ApplicationCommandType.chat_input:

                args = self.get_command_args(command)
                sub_commands = self.get_sub_commands(command)
                if sub_commands:
                    _commands.extend(sub_commands)
                else:
                    requires_admin = True if "Admin" in command.description else False
                    _commands.append(
                        SlashCommand(
                            id=command.id,
                            name=command.name,
                            requires_admin=requires_admin,
                            description=command.description,
                            args=args,
                        )
                    )

            # if message context command or user context command
            else:
                _id = command.id
                name = command.name

                if command.type == disnake.ApplicationCommandType.message:
                    # since APIMessageCommands do not include extras we'll need to get the InvokableMessageCommand instead
                    command: commands.InvokableMessageCommand = self.bot.get_message_command(name)
                    description = command.extras.get("desc")
                    requires_admin = True if "Admin" in description else False

                    _commands.append(
                        MessageCommand(
                            id=_id,
                            name=name,
                            description=description,
                            requires_admin=requires_admin,
                        )
                    )

                else:
                    command: commands.InvokableUserCommand = self.bot.get_user_command(name)
                    description = command.extras.get("desc")

                    _commands.append(UserCommand(id=_id, name=name, description=description))

        return _commands

    def get_sub_commands(self, command: disnake.APISlashCommand) -> List[SlashCommand]:
        """Get and return the parent command's sub commands"""

        sub_commands = []

        for option in command.options:

            if option.type not in [
                disnake.OptionType.sub_command,
                disnake.OptionType.sub_command_group,
            ]:
                continue

            args = self.get_command_args(option)
            requires_admin = True if "Admin" in option.description else False

            sub_commands.append(
                SlashCommand(
                    id=command.id,
                    name=f"{command.name} {option.name}",
                    requires_admin=requires_admin,
                    description=option.description,
                    args=args,
                )
            )

        return sub_commands

    def get_command_args(self, command: disnake.APISlashCommand) -> List[Argument]:
        """Get and return the command's arguments"""

        args = []
        for option in command.options:

            if option.type in [
                disnake.OptionType.sub_command,
                disnake.OptionType.sub_command_group,
            ]:
                continue

            args.append(
                Argument(name=option.name, description=option.description, required=option.required)
            )

        return args

    def create_command_detail_embed(
        self, command: Union[SlashCommand, UserCommand, MessageCommand]
    ) -> disnake.Embed:
        """Creates the command detail embed and returns it"""
        embed = disnake.Embed(
            title=f"Command Details",
            description=f"{command.mention} - {command.description}",
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        # check if command is a slash command
        if isinstance(command, SlashCommand):

            if len(command.args) > 0:
                embed.description += (
                    "\n\n*`[` `]` - required argument*\n*`(` `)` - optional argument*\n"
                )

                args = []
                for arg in command.args:

                    if arg.required:
                        name = f"[{arg.name}]"
                    else:
                        name = f"({arg.name})"

                    args.append(f"**{name}** - {arg.description}")

                embed.add_field(name="\u200b", value="\n".join(args), inline=True)

            else:
                embed.add_field(name="'\u200b", value="Command has no arguments")

        return embed

    def create_help_embed(
        self, commands: List[Union[SlashCommand, UserCommand, MessageCommand]]
    ) -> disnake.Embed:
        """Creates the help embed and returns it"""

        embed = disnake.Embed(
            title=f"{self.bot.user.display_name} Command Help",
            description=self.bot.description if hasattr(self.bot, "description") else DESCRIPTION,
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        admin_commands = ""
        slash_commands = ""
        user_commands = ""
        message_commands = ""

        for command in commands:
            if command.requires_admin and SHOW_ADMIN_COMMANDS:
                admin_commands += f"{command.mention} - {command.description}\n"
            elif isinstance(command, SlashCommand):
                slash_commands += f"{command.mention} - {command.description}\n"
            elif isinstance(command, UserCommand):
                user_commands += f"{command.mention} - {command.description}\n"
            elif isinstance(command, MessageCommand):
                message_commands += f"{command.mention} - {command.description}\n"

        if admin_commands:
            embed.add_field(name="Admin Only Commands", value=admin_commands, inline=False)

        if slash_commands:
            embed.add_field(name="Slash Commands", value=slash_commands, inline=False)

        if user_commands:
            embed.add_field(name="User Context Commands", value=user_commands, inline=False)

        if message_commands:
            embed.add_field(name="Message Context Commands", value=message_commands, inline=False)

        return embed

    @help_command.autocomplete("command")
    async def command_autocomplete(
        self, inter: disnake.GuildCommandInteraction, string: str
    ) -> List[str]:
        """Autocomplete for command option in help command"""

        commands = self.walk_app_commands(inter.guild.id)

        return [c.name for c in commands if string.lower() in c.name.lower()][:25]


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(Help(bot))
