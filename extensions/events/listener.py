import discord
from discord.ext import commands

from utils.bot import Qolga
from datetime import datetime

from utils.views import (
    TicketSetupView, 
    TicketCloseView, 
    TicketCloseWarningView, 
    TicketClosedView, 
    CheckInView
)


class Listener(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketSetupView(self.bot))
        self.bot.add_view(TicketCloseView(self.bot))
        self.bot.add_view(TicketCloseWarningView(self.bot))
        self.bot.add_view(TicketClosedView(self.bot))
        self.bot.add_view(CheckInView(self.bot))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role = member.guild.get_role(self.bot.config.community_role_id)
        await member.add_roles(role)

        welcome_channel = member.guild.get_channel(self.bot.config.welcome_channel_id)
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.description = f'<a:purpleheart:1233379992348659756> მოგესალმებით {member.guild.name} სერვერზე! <a:purpleheart:1233379992348659756>'
        embed.add_field(name='წესები', value='<#1233170863897968700>', inline=False)
        embed.add_field(name='მთავარი', value='<#1125326451944738850>', inline=False)
        embed.add_field(name='შეიქმნა', value=discord.utils.format_dt(member.created_at, 'R'), inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_author(name=member.display_name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = datetime.now()

        await welcome_channel.send(embed=embed)