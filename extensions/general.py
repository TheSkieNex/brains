import re
import io

import discord
import requests

from discord.ext import commands

from io import BytesIO
from utils.bot import Brains


class GeneralCommands(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def steal(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        response = requests.get(emoji.url)
        image_bytes = BytesIO(response.content)

        await ctx.guild.create_custom_emoji(name=emoji.name, image=image_bytes.read())
        await ctx.send(f'Emoji {emoji.name} was added to the server!')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def give(self, ctx: commands.Context, role: str):
        if ctx.message.type == discord.MessageType.reply:
            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                _role = ctx.guild.get_role(int(role[3:len(role)-1]))

                errors = 0
                for user_id in message.raw_mentions:
                    try: 
                        user = ctx.guild.get_member(user_id)
                        await user.add_roles(_role)
                    except:
                        errors += 1
                        continue

                await ctx.message.add_reaction('✅')
                if errors > 0:
                    await ctx.send(f'{errors} users are not in the server.')
            except:
                await ctx.send('Something unexpected happened.')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, role: str):
        if ctx.message.type == discord.MessageType.reply:
            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                _role = ctx.guild.get_role(int(role[3:len(role)-1]))
                
                errors = 0
                for user_id in message.raw_mentions:
                    try:
                        user = ctx.guild.get_member(user_id)
                        await user.remove_roles(_role)
                    except:
                        errors += 1
                        continue

                await ctx.message.add_reaction('✅')
                if errors > 0:
                    await ctx.send(f'{errors} users are not in the server.')
            except:
                await ctx.send('Something unexpected happened.')

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def get_players_ids(self, ctx: commands.Context, limit: str):
        players_ids = set()
        messages = [message async for message in ctx.channel.history(limit=int(limit))]

        for message in messages:
            ids_in_message = re.findall(r'(?<!<@)\b\d+\b(?!>)', message.content)

            for id in ids_in_message:
                if len(id) >= 7:
                    players_ids.add(id)

        file_content = '\n'.join(players_ids)
        file_object = io.StringIO(file_content)
        file = discord.File(file_object, filename='players_ids.txt')

        await ctx.send(f'{len(players_ids)} players ids was saved.', file=file)

    @commands.command()
    @commands.is_owner()
    async def guilds(self, ctx: commands.Context):
        n_guilds = len(self.bot.guilds)

        await ctx.send(str(n_guilds))


async def setup(bot: Brains):
    await bot.add_cog(GeneralCommands(bot))