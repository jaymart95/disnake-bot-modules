from disnake.ext import commands
from disnake import Embed, CommandInteraction, Member
from tabulate import tabulate
from asyncio import sleep

from cogs._trivia.utils import api, db
from cogs._trivia.utils.buttons import AnswerButtons, LeaderView

from json import load
from random import shuffle


def load_cat_list():
    """load the list of categories from categories.json"""
    with open("./cogs/_trivia/data/categories.json") as f:
        data = load(f)
    return [k for item in data["categories"] for (k, v) in item.items()]


def load_trivia_help_body():
    """load the formatted trivia help body text from trivia.txt"""
    with open("./cogs/_trivia/data/trivia.txt") as f:
        return f.read()


class Trivia(commands.Cog):
    """Trivia bot module"""

    def __init__(self, bot):
        self.bot = bot
        self.difficulties = ["Easy", "Medium", "Hard"]
        self.categories = load_cat_list()

    @commands.Cog.listener()
    async def on_ready(self):
        '''
        When Cog is ready, ensure bot is ready and update categories
        Print ready message to console
        '''
        await self.bot.wait_until_ready()
        await api.update_categories()
        print(f"Cog loaded: {self.qualified_name}")

    @commands.slash_command(name="trivia")
    async def trivia_command(self, inter):
        '''Command is always invoked if child is invoked'''
        pass

    @trivia_command.sub_command(name="question")
    async def trivia_question(
        self, inter, category: str = None, difficulty: str = None
    ):
        """
        Get a trivia question

        Parameters
        ----------
        category: (Optional) Specify question category
        difficulty: (Optional) Specify question difficulty
        """
        # fetch the trivia question and shuffle the incorrect and correct answers into answers variable
        cat, diff, quest, correct, incorrect, points = await api.trivia_question(
            category, difficulty
        )

        # combine correct and incorrect answers, then shuffle
        answers = incorrect
        answers.append(correct)
        shuffle(answers)
        member = inter.author

        # Discord button view
        view = AnswerButtons(member, answers, correct, inter, points, quest)

        # build the initial embed
        embed = Embed(
            title="Hurry! Your time is limited!",
            description=":stopwatch: **20s** remaining",
        )
        embed.add_field(
            name="Info", value=f"Category: {cat}\nDifficulty: {diff}", inline=False
        )
        embed.add_field(name="Question:", value=quest)

        await inter.response.send_message(embed=embed, view=view)

        # start countdown and edit embed each second until time runs out or interaction
        t = 20
        while t:

            # if the interaction view is completed, break this loop
            if view.is_finished():
                break

            await sleep(1)
            t -= 1

            embed = Embed(
                title="Hurry! Your time is limited!",
                description=f":stopwatch: **{t}s** remaining",
            )
            embed.add_field(
                name="Info",
                value=f"Category: {cat}\nDifficulty: {diff}\u200b",
                inline=False,
            )
            embed.add_field(name="Question:", value=quest)

            # if the interaction view is completed, break this loop
            if view.is_finished():
                break

            await inter.edit_original_message(embed=embed)

    @trivia_command.sub_command(name="help")
    async def trivia_categories(self, inter):
        '''
        Display Trivia specific help and information
        '''

        categories = "\n".join(self.categories)
        difficulties = "\n".join(self.difficulties)
        body = load_trivia_help_body()

        embed = Embed(
            title="Trivia Help")
        embed.add_field(name="Categories", value=categories, inline=True)
        embed.add_field(name="Difficulties", value=difficulties, inline=True)
        embed.set_footer(text="All data provided by OpenTDB.com")

        await inter.response.send_message(embed=embed, ephemeral=True)

    @trivia_command.sub_command(name="leaderboard")
    async def trivia_leaderboard(self, inter, target: Member = None):
        '''
        View the Trivia Leaderboard or a target's trivia stats

        Parameter
        ---------
        target: (Optional) The target guild member
        '''

        # if no target passed
        if not target:
            guild = inter.guild

            # fetch all db rows, sorted by points
            db_points = db.fetch_leaderboard_points()
            points_leaderboard = []

            # create the list of lists for tabulate's magic
            for index, item in enumerate(db_points, 1):
                member = guild.get_member(item.member_id)

                points_leaderboard.append(
                    [
                        f"{index}.",
                        item.points,
                        member,
                        f"{round(((item.total_corr/(item.total_corr + item.total_wro))*100),2)}%",
                    ]
                )


            # fetch all db rows, sorted by total_corr
            db_correct = db.fetch_leaderboard_correct()
            correct_leaderboard = []

            # create a list of lists for tabulate's magic
            for index, item in enumerate(db_correct, 1):
                member = guild.get_member(item.member_id)

                correct_leaderboard.append(
                    [
                        f"{index}.",
                        item.total_corr,
                        member,
                        f"{round(((item.total_corr/(item.total_corr + item.total_wro))*100),2)}%",
                    ]
                )

            # Tabulate the points leaderboard
            points_leaderboard = tabulate(
                points_leaderboard,
                headers=["Rank", "Points", "Member", "Correct %"],
                tablefmt="plain",
                stralign="center",
                numalign="center",
            )

            # Tabulate the correct count leaderboard
            correct_leaderboard = tabulate(
                correct_leaderboard,
                headers=["Rank", "Count", "Member", "Correct %"],
                tablefmt="plain",
                stralign="center",
                numalign="center",
            )

            # points embed
            points_em = Embed(
                title=":star: Trivia Leaderboard (Points) :star:",
                description="\u200b\n:sunglasses: Look at all these winners!\n\u200b",
            )
            points_em.add_field(
                name="Leaderboard", value=f"```py\n{points_leaderboard}```"
            )

            # correct leaderboard
            correct_em = Embed(
                title=":star: Trivia Leaderboard (Correct Count) :star:",
                description="\u200b\n:sunglasses: Look at all these winners!\n\u200b",
            )
            correct_em.add_field(
                name="Leaderboard", value=f"```py\n{correct_leaderboard}```"
            )

            # send the embed and generate the views
            await inter.response.send_message(
                embed=points_em, view=LeaderView(points_em, correct_em)
            )

        # if target
        else:
            # fetch the target row from the DB
            db_member = db.get_member(target)

            # if target exists in DB
            if db_member:

                # create tabulate list of db_member stats
                db_member_stats = [
                    [db_member.points, "Points"],
                    [db_member.total_corr, "Total Answers Correct"],
                    [db_member.total_wro, "Total Answers Wrong"],
                    [
                        f"{round((db_member.total_corr/(db_member.total_corr + db_member.total_wro)*100),2)}%",
                        "Correct Percentage",
                    ],
                ]

                # Tabulate the db_member's stats
                db_member_stats = tabulate(db_member_stats, tablefmt="plain")

                embed = Embed(
                    title=f"{target.display_name}'s Trivia Stats",
                    description=f"```py\n{db_member_stats}```",
                )
                if target.display_avatar:
                    embed.set_thumbnail(url=target.display_avatar.url)

                await inter.response.send_message(embed=embed)

            # if target, and not in db
            else:
                await inter.response.send_message(
                    "Looks like this member has not done any trivia yet.",
                    ephemeral=True,
                )


    '''
    Auto complete functions

    These functions are necessary to allow members to have selectable argument options (difficulty and categories)
    when using the /trivia question slash command
    '''
    @trivia_question.autocomplete("category")
    async def cat_autocomplete(self, inter: CommandInteraction, string: str):
        string = string.lower()
        return [cat for cat in self.categories if string in cat.lower()]

    @trivia_question.autocomplete("difficulty")
    async def diff_autocomplete(self, inter: CommandInteraction, string: str):
        string = string.lower()
        return [diff for diff in self.difficulties if string in diff.lower()]




# bot setup function for this cog
def setup(bot):
    bot.add_cog(Trivia(bot))
