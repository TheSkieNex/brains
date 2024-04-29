import discord

from discord.ext import commands
from discord import app_commands, ui

from utils.bot import Qolga
from utils.ticket import setup_ticket_system


class Ticket(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    ticket_group = app_commands.Group(name='ticket', description='ticket group', guild_only=True)

    @ticket_group.command(name='open', description='თიქეთის გახსნა')
    async def ticket_open(self, interaction: discord.Interaction):
        await interaction.response.send_message('ტურნირი ჯერ არ არის დაწყებული', ephemeral=True)
        # await self.setup_ticket_system(interaction)

    @commands.command(name='ticket_setup')
    @commands.is_owner()
    async def _ticket_setup(self, ctx: commands.Context):
        ticket_channel = ctx.guild.get_channel(self.bot.config.ticket_channel_id)

        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = 'რეპორტი'
        embed.description = 'უმიზეზოდ თიქეთის გახსნა დაუშვებელია!'

        create_button = ui.Button(label='თიქეთის გახსნა', style=discord.ButtonStyle.secondary)

        async def create_button_callback(inter: discord.Interaction):
            await setup_ticket_system(self.bot, inter)

        create_button.callback = create_button_callback

        view = ui.View()
        view.add_item(create_button)

        await ticket_channel.send(embed=embed, view=view)
        await ctx.reply('თიქეთის სისტემა გამზადებულია', delete_after=.5)


async def setup(bot: Qolga):
    await bot.add_cog(Ticket(bot))