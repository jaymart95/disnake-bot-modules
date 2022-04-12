from disnake import Embed, ButtonStyle, Interaction
from disnake.ui import View, Button, button

from cogs._trivia.utils import db


class AnswerButtons(View):
    '''
    View class that contains trivia answer buttons

    Parameters
    ----------
    answers: (list) the list of answers provided from trivia api (correct + wrong - shuffled)
    correct: (str) the correct answer provided by trivia API to compare interaction
    inter: (obj) The discord interaction object (from original slash command response that invokes this view)
    points: (int) The calculated points
    quest: (str) The trivia question
    '''

    def __init__(self, answers, correct, inter, points, bonus, quest):
        super().__init__(timeout=20)
        [self.add_item(Button(label=a, style=ButtonStyle.primary)) for a in answers]
        self.correct = correct
        self.inter = inter
        self.points = points
        self.bonus = bonus
        self.quest = quest

    async def on_timeout(self):
        '''Invoked if the view times out - 20 seconds'''

        embed = Embed(
            title=":yellow_circle: Sorry! You ran out of time",
            description=f'{str(self.inter.author.mention)} earned no points this time.',
        )
        embed.add_field(
            name="Question",
            value=f"{self.quest}\n\nThe correct answer is: **{self.correct}**.",
        )
        if self.inter.author.avatar:
            embed.set_thumbnail(url=self.inter.author.avatar.url)

        # iterate view buttons and assign colors and disable
        for button in self.children:
            if button.label == self.correct:
                button.style = ButtonStyle.success
            button.disabled = True

        # Respond to the interaction and upate the view, stop View listener
        await self.inter.channel.send(embed=embed, view=self)
        self.stop()

        # update the member in db
        db.update_member(member=self.inter.author, wrong=1)

    async def interaction_check(self, interaction):
        '''invoked when any interaction takes place on the invoked View'''
        author = interaction.author

        # If button interaction user == original slash command user
        if author == self.inter.author:
            # assign default values
            points = 0
            correct = 0
            wrong = 0
            bonus = 0

            # check if the interacted button is the correct answer button
            if interaction.component.label == self.correct:
                correct = 1
                points = self.points
                bonus = self.bonus

                embed = Embed(
                    title=":green_circle: Hey! You did it!",
                    description=f"{str(self.inter.author.mention)} earned **{self.points} points (+ {bonus} bonus)**!",
                )
                embed.add_field(
                    name="Question",
                    value=f"{self.quest}\n\n**{self.correct}** is correct!.",
                )

                if self.inter.author.avatar:
                    embed.set_thumbnail(url=self.inter.author.avatar.url)

                # iterate view buttons and assign colors and disable
                for button in self.children:
                    if button.label == interaction.component.label:
                        button.style = ButtonStyle.success
                    button.disabled = True

                # Respond to the interaction and upate the view, stop View listener
                await interaction.response.defer()
                await interaction.channel.send(embed=embed, view=self)
                self.stop()

            # If the answer selected is not correct
            else:
                wrong = 1
                embed = Embed(
                    title=":red_circle: Sorry! That wasn't correct",
                    description=f'{str(self.inter.author.mention)} earned no points this time.',
                )
                embed.add_field(
                    name="Question",
                    value=f"{self.quest}\n\n**The correct answer is: {self.correct}**.",
                )
                if self.inter.author.avatar:
                    embed.set_thumbnail(url=self.inter.author.avatar.url)

                # iterate view buttons and assign colors and disable
                for button in self.children:
                    if button.label == interaction.component.label:
                        button.style = ButtonStyle.danger
                    elif button.label == self.correct:
                        button.style = ButtonStyle.success
                    button.disabled = True

                # Respond to the interaction and upate the view, stop View listener
                await interaction.response.defer()
                await interaction.channel.send(embed=embed, view=self)
                self.stop()

            # update the member in the db
            db.update_member(member=self.inter.author, points=points+bonus, correct=correct, wrong=wrong)

        # If button interaction user != original slash command user
        else:
            await interaction.response.send_message(
                f"Hey! This isn't your question!", ephemeral=True
            )


class LeaderView(View):
    def __init__(self, points_em, correct_em, inter):
        super().__init__(timeout=300)
        self.points_em = points_em
        self.correct_em = correct_em
        self.inter = inter


    async def on_timeout(self):
        ''''buttons timeout after 300s (5m), disable buttons'''
        for button in self.children:
            button.disabled = True

        # Respond to the interaction and upate the view, stop View listener
        await self.inter.edit_original_message(view=self)
        self.stop()

    @button(label="Sort: Points", style=ButtonStyle.primary)
    async def points_view(self, button: Button, interaction: Interaction):

        await interaction.response.edit_message(embed=self.points_em)

    @button(label="Sort: Correct", style=ButtonStyle.primary)
    async def correct_view(self, button: Button, interaction: Interaction):

        await interaction.response.edit_message(embed=self.correct_em)
