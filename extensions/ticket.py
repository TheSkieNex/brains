import discord

from discord.ext import commands
from discord import app_commands

from utils.bot import Qolga
from utils.views import TicketSetupView


class Ticket(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    ticket_group = app_commands.Group(name='ticket', description='ticket group', guild_only=True)

    @ticket_group.command(name='open', description='თიქეთის გახსნა')
    async def ticket_open(self, interaction: discord.Interaction):
        await interaction.response.send_message('ჯერ ტურნირი არ არის დაწყებული', ephemeral=True)
        # await self.setup_ticket_system(interaction)

    @commands.command(name='ticket_setup')
    @commands.is_owner()
    async def _ticket_setup(self, ctx: commands.Context):
        ticket_channel = ctx.guild.get_channel(self.bot.config.ticket_channel_id)

        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = 'რეპორტი'
        embed.description = 'უმიზეზოდ თიქეთის გახსნა დაუშვებელია!'

        await ticket_channel.send(embed=embed, view=TicketSetupView(self.bot))
        await ctx.reply('თიქეთის სისტემა გამზადებულია', delete_after=.5)


async def setup(bot: Qolga):
    await bot.add_cog(Ticket(bot))