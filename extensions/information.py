import discord

from discord.ext import commands
from discord import app_commands
from discord.utils import format_dt

from utils.bot import Brains
from datetime import datetime


class Information(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot

    @app_commands.command(name='server', description='Server information')
    @app_commands.guild_only()
    async def server_info(self, interaction: discord.Interaction):
        guild = self.bot.get_guild(self.bot.config.guild_id)

        online = []
        offline = []

        for member in guild.members:
            if str(member.status) in ('online', 'dnd'):
                online.append(str(member))
            else:
                offline.append(str(member))

        roles = []

        for role in guild.roles:
            roles.append(str(role.mention))

        roles.reverse()
        roles.pop()
        
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = guild.name
        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon.url)

        embed.description = f'Created: {format_dt(guild.created_at, style="R")}'
        embed.add_field(name='Server ID', value=guild.id, inline=False)
        embed.add_field(name='Server Owner', value=guild.owner.mention, inline=False)
        embed.add_field(name=f'Roles - {len(guild.roles)}', value=' '.join(roles), inline=False)
        embed.add_field(name=f'Members - {len(guild.members)}', value=(
            f'<:green:1235625157389979700> {len(online)}   <:gray:1235625075672350731> {len(offline)}'
        ), inline=False)
        embed.add_field(name=f'Channels - {len(guild.channels)}', value=(
            f'Category: {len(guild.categories)}\n'
            f'Text: {len(guild.text_channels)}\n'
            f'Voice: {len(guild.voice_channels)}'
        ), inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='user', description='User information')
    @app_commands.guild_only()
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        if not member:
            member = interaction.user

        roles = []

        for role in member.roles:
            roles.append(str(role.mention))

        roles.reverse()
        roles.pop()
        
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.add_field(name='User', value=member.mention, inline=False)
        embed.add_field(name='User ID', value=member.id, inline=False)
        embed.add_field(name='Created', value=format_dt(member.created_at, style="R"), inline=False)
        embed.add_field(name='Joined', value=format_dt(member.joined_at, style="R"), inline=False)
        if len(member.roles) == 1:
            embed.add_field(name='Roles', value='None' , inline=False)
        else:
            embed.add_field(name=f'Roles - {len(roles)}', value=f'{" ".join(roles)}' , inline=False)

        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            
        await interaction.response.send_message(embed=embed)


async def setup(bot: Brains):
    await bot.add_cog(Information(bot))