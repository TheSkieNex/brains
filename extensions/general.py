import re
import io

import discord
import httpx

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
        response = await httpx.get(emoji.url)
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
    async def get_player_ids(self, ctx: commands.Context, limit: str = '1000'):
        await ctx.send("Starting to get the player IDs")

        teams_data = []
        messages = [message async for message in ctx.channel.history(limit=int(limit))]

        for message in messages:
            lines = message.content.strip().split('\n')
            if not lines:
                continue
                
            # Get team name from first line
            team_name = lines[0].strip()
            
            # Extract player IDs from the message
            players_ids = set()
            ids_in_message = re.findall(r'(?<!<@)\b\d+\b(?!>)', message.content)
            
            for id in ids_in_message:
                if len(id) >= 7:
                    players_ids.add(id)
            
            if players_ids:  # Only add teams that have player IDs
                teams_data.append((team_name, players_ids))

        # Format output
        file_content = []
        for team_name, player_ids in teams_data:
            file_content.append(team_name)
            for player_id in sorted(player_ids):
                file_content.append(player_id)
            file_content.append('')  # Blank line between teams
        
        # Remove trailing blank line
        if file_content and file_content[-1] == '':
            file_content.pop()
            
        file_content_str = '\n'.join(file_content)
        file_object = io.StringIO(file_content_str)
        file = discord.File(file_object, filename='teams_and_players.txt')

        total_players = sum(len(ids) for _, ids in teams_data)
        await ctx.send(f'{len(teams_data)} teams with {total_players} total players were saved.', file=file)

    @commands.command()
    @commands.is_owner()
    async def guilds(self, ctx: commands.Context):
        n_guilds = len(self.bot.guilds)

        await ctx.send(str(n_guilds))


async def setup(bot: Brains):
    await bot.add_cog(GeneralCommands(bot))