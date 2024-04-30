import discord
from discord.ext import commands

from utils.bot import Qolga
from utils.ticket import setup_ticket_system

class Listener(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        ticket_channel = self.bot.get_channel(self.bot.config.ticket_channel_id)

        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = 'რეპორტი'
        embed.description = 'უმიზეზოდ თიქეთის გახსნა დაუშვებელია!'

        create_button = discord.ui.Button(label='თიქეთის გახსნა', style=discord.ButtonStyle.secondary)

        async def create_button_callback(inter: discord.Interaction):
            await setup_ticket_system(self.bot, inter)

        create_button.callback = create_button_callback

        view = discord.ui.View()
        view.add_item(create_button)

        await ticket_channel.purge(limit=1)
        await ticket_channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome_channel = member.guild.get_channel(self.bot.config.welcome_channel_id)
        role = member.guild.get_role(self.bot.config.community_role_id)

        embed = discord.Embed(color=self.bot.config.main_color)
        embed.description = f'Welcome {member.mention} to {member.guild.name}!'
        embed.add_field(name='Rules', value='<#1233170863897968700>', inline=False)
        embed.add_field(name='General', value='<#1125326451944738850>', inline=False)
        embed.add_field(name='User since', value=discord.utils.format_dt(member.created_at, 'R'), inline=False)
        embed.set_thumbnail(url=member.avatar.url)

        await member.add_roles(role)
        await welcome_channel.send(embed=embed)