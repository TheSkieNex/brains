import discord
from discord.ext import commands
from discord import app_commands

from utils.bot import Brains


class Moderation(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot

    @app_commands.command(name='kick', description='Kick a user from the server')
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(
        target='The user to kick',
        reason='Reason of doing so'
    )
    async def kick(self, interaction: discord.Interaction, target: discord.Member, reason: str = None):
        if not reason:
            reason = 'Reason was not specified'

        try:
            embed = discord.Embed()
            embed.description = f'**Reason**: {reason}'
            embed.set_author(name=f'{target.name} was kicked out of the server', icon_url=target.avatar.url)

            await interaction.guild.kick(target, reason=reason)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message('I don\'t have permissions to do that', ephemeral=True)

    @app_commands.command(name='ban', description='Ban a user from the server')
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(
        target='The user to ban',
        reason='Reason of doing so'
    )
    async def ban(self, interaction: discord.Interaction, target: discord.Member, reason: str = None):
        if not reason:
            reason = 'Reason was not specified'

        try:
            embed = discord.Embed()
            embed.description = f'**Reason**: {reason}'
            embed.set_author(name=f'{target.name} was banned from the server', icon_url=target.avatar.url)

            await interaction.guild.ban(target, reason=reason)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message('I don\'t have permissions to do that', ephemeral=True)

    @commands.hybrid_command(name='purge', description='Delete number of messages in a channel')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(limit='The amount of messages to delete')
    async def purge(self, ctx: commands.Context, limit: int = None):
        if not limit:
            limit = 10

        await ctx.channel.purge(limit=limit)
        await ctx.send(f'{limit} messages were deleted', ephemeral=True, delete_after=.5)