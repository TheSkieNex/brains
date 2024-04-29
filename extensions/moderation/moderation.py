import discord
from discord.ext import commands
from discord import app_commands

from utils.bot import Qolga


class Moderation(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    @app_commands.command(name='kick', description='აგდებს წევრს სერვერიდან')
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(
        target='ის ვინც გინდა რომ გააგდო',
        reason='მიზეზი თუ რატომ აგდებ მას სერვერიდან'
    )
    async def kick(self, interaction: discord.Interaction, target: discord.Member, reason: str = None):
        if not reason:
            reason = 'არ იყო მითითებული'

        embed = discord.Embed()
        embed.description = f'**მიზეზი**: {reason}'
        embed.set_author(name=f'{target.name} გავარდა სერვერდიან', icon_url=target.avatar.url)

        await interaction.guild.kick(target, reason=reason)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='ban', description='უკრძალავს წევრს სერვერზე ყოფნას')
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(
        target='სერვერის წევრი ვისაც გინდა რომ აეკრძალოს სერვერზე ყოფნა',
        reason='მიზეზი თუ რატომ გინდა რომ მას აეკრძალოს სერვერზე ყოფნა'
    )
    async def ban(self, interaction: discord.Interaction, target: discord.Member, reason: str = None):
        if not reason:
            reason = 'არ იყო მითითებული'

        embed = discord.Embed()
        embed.description = f'**მიზეზი**: {reason}'
        embed.set_author(name=f'{target.name} აეკრძალა სერვერზე ყოფნა', icon_url=target.avatar.url)

        await interaction.guild.ban(target, reason=reason)
        await interaction.response.send_message(embed=embed)


async def setup(bot: Qolga):
    await bot.add_cog(Moderation(bot))