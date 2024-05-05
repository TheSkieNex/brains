import discord
from discord.ext import commands

from utils.bot import Qolga
from utils.ticket import setup_ticket_system
from datetime import datetime


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

        view = discord.ui.View(timeout=None)
        view.add_item(create_button)

        await ticket_channel.purge(limit=1)
        await ticket_channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role = member.guild.get_role(self.bot.config.community_role_id)
        await member.add_roles(role)

        welcome_channel = member.guild.get_channel(self.bot.config.welcome_channel_id)
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.description = f'<a:purpleheart:1233379992348659756> Welcome to {member.guild.name}! <a:purpleheart:1233379992348659756>'
        embed.add_field(name='Rules', value='<#1233170863897968700>', inline=False)
        embed.add_field(name='General', value='<#1125326451944738850>', inline=False)
        embed.add_field(name='Created', value=discord.utils.format_dt(member.created_at, 'R'), inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_author(name=member.display_name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = datetime.now()

        await welcome_channel.send(embed=embed)