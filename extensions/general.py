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

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def give(self, ctx: commands.Context, role: str):
        if ctx.message.type == discord.MessageType.reply:
            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                _role = ctx.guild.get_role(int(role[3:len(role)-1]))

                for user_id in message.raw_mentions:
                    user = ctx.guild.get_member(user_id)
                    await user.add_roles(_role)

                await ctx.send(f'როლი დაემატა {len(message.raw_mentions)} წევრს.')
            except:
                await ctx.send('რაღაც პრობლემაა, ხელახლა სცადეთ.')

 
async def setup(bot: Qolga):
    await bot.add_cog(GeneralCommands(bot))