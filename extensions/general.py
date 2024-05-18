import re
import io

import discord
import requests

from discord.ext import commands
from discord import app_commands

from io import BytesIO
from utils.bot import Qolga
from utils.views import CheckInView


class TeamListModal(discord.ui.Modal, title='ჯგუფის გუნდების სია'):
    group = discord.ui.TextInput(
        label='ჯგუფი', required=True, style=discord.TextStyle.short,  min_length=1, max_length=64
    )
    list_text = discord.ui.TextInput(
        label='გუნდების სია', required=True, style=discord.TextStyle.long, min_length=1, max_length=2000
    )
    match_day = discord.ui.TextInput(
        label='თამაშის დღე', required=True, style=discord.TextStyle.short, min_length=1, max_length=32
    )
    total_maps = discord.ui.TextInput(
        label='მაპების რაოდენობა', required=True, style=discord.TextStyle.short, min_length=1, max_length=3
    )
    # footer = discord.ui.TextInput(
    #     label='ტოპ', required=True, style=discord.TextStyle.short, min_length=1, max_length=64
    # )

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

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
            await ctx.send(f'ემოჯი {emoji.name} დაემატა სერვერზე!')
        else:
            await ctx.send(f'ემოჯი {emoji.name} დაემატა სერვერზე!')

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

                await ctx.message.add_reaction('✅')
            except:
                await ctx.send('რაღაც პრობლემაა, ხელახლა სცადეთ.')

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    # @commands.has_permissions(administrator=True)
    async def get_players_ids(self, ctx: commands.Context, limit: str):
        players_ids = set()
        messages = [message async for message in ctx.channel.history(limit=int(limit))]

        for message in messages:
            ids_in_message = re.findall(r'(?<!<@)\b\d+\b(?!>)', message.content)

            for id in ids_in_message:
                if len(id) >= 6:
                    players_ids.add(id)

        file_content = '\n'.join(players_ids)
        file_object = io.StringIO(file_content)
        file = discord.File(file_object, filename='players_ids.txt')

        await ctx.send(f'ჩაიწერა {len(players_ids)} მოთამაშის აიდი.', file=file)

    @app_commands.command(name='list_send', description='ჯგუფის გუნდების სიის გაგზავნა')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel='ჯგუფის არხი')
    async def send_list(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not channel:
            channel = interaction.channel

        modal = TeamListModal()

        await interaction.response.send_modal(modal)
        await modal.wait()
        group = modal.group
        list_text = modal.list_text.value
        match_day = modal.match_day
        total_maps =int (modal.total_maps.value)
        # footer = modal.footer
        interaction = modal.interaction

        lines = list_text.split('\n')
        formatted_lines = [f'> {line}' for line in lines if line.strip()]
        formatted_string = '\n'.join(formatted_lines)

        four_maps = (
            '<:era:1237124795074740316> | <:mir:1237124887785635951> | <:era:1237124795074740316> | <:mir:1237124887785635951>'
        )
        five_maps = (
            '<:era:1237124795074740316> | <:mir:1237124887785635951> | <:era:1237124795074740316> | <:mir:1237124887785635951> | <:era:1237124795074740316>'
        )

        formatted_text = f"""
            <:umbrellatour:1233412554320117912> **Umbrella Tournament - ჯგუფი {group}
            {formatted_string}**
            **<a:att:1241259984428335144> დრო: {match_day} - 22:00 საათი**
            **<a:att:1241259984428335144> {total_maps} რუკა:** **{four_maps if total_maps == 4 else five_maps}**
        """

        await channel.send(formatted_text)
        await interaction.response.defer()
        await interaction.response.is_done()

    @app_commands.command(name='check_in', description='თამაშის დასტურის მესიჯი')
    @app_commands.guild_only
    @app_commands.default_permissions(administrator=True)
    async def check_in(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(color=self.bot.config.main_color)
            embed.description = (
                '**გთხოვთ დაადასტუროთ/უარყოთ მონაწილეობა დღევანდელ თამაშზე 12:00 საათიდან 20:00 საათამდე**'
            )

            await interaction.response.send_message('<@&1234921072940552224>', embed=embed, view=CheckInView(self.bot))
        except:
            await interaction.response.send_message('რაღაც პრობლემაა, ხელახლა სცადეთ.', ephemeral=True)

 
async def setup(bot: Qolga):
    await bot.add_cog(GeneralCommands(bot))