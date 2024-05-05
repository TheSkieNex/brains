import discord
import requests

from discord.ext import commands
from io import BytesIO

from utils.bot import Qolga


class GeneralCommands(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def steal(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        response = requests.get(emoji.url)
        image_bytes = BytesIO(response.content)

        await ctx.guild.create_custom_emoji(name=emoji.name, image=image_bytes.read())
        if emoji.animated:
            await ctx.send(f'ემოჯი <a:{emoji.name}:{emoji.id}> დაემატა სერვერზე!')
        else:
            await ctx.send(f'ემოჯი <:{emoji.name}:{emoji.id}> დაემატა სერვერზე!')

async def setup(bot: Qolga):
    await bot.add_cog(GeneralCommands(bot))