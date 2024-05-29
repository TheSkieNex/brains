import re
import io

import discord
import requests

from discord.ext import commands
from discord import app_commands

from io import BytesIO
from utils.bot import Qolga
from utils.views import CheckInView
from utils.selects import CapSelect


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

    def __init__(
        self, 
        group: str = None, 
        list_text: str = None,
        match_day: str = None,
        total_maps: str = None
    ):
        self.group.default = group
        self.list_text.default = list_text
        self.match_day.default = match_day
        self.total_maps.default = total_maps
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
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, role: str):
        if ctx.message.type == discord.MessageType.reply:
            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                _role = ctx.guild.get_role(int(role[3:len(role)-1]))

                for user_id in message.raw_mentions:
                    user = ctx.guild.get_member(user_id)
                    await user.remove_roles(_role)

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
    async def list_send(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not channel:
            channel = interaction.channel

        modal = TeamListModal()

        await interaction.response.send_modal(modal)
        await modal.wait()
        group = modal.group
        list_text = modal.list_text.value
        match_day = modal.match_day
        total_maps = int(modal.total_maps.value)
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

    @app_commands.command(name='list_edit', description='ჯგუფის გუნდების სიის რედაქტირება')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def list_edit(self, interaction: discord.Interaction):
        channel_messages = [message async for message in interaction.channel.history(limit=100)]
        list_message = channel_messages[len(channel_messages)-1]
        list_message_content = list_message.content

        lines = list_message_content.split('\n')

        group = lines[0][lines[0].find('ჯგუფი'):][6:]
        list_text = ''
        day = ''
        maps = ''

        for i, line in enumerate(lines):
            if 'დრო' in line:
                lines[i].replace('> ', 'g')
                lines[1] = lines[1][lines[1].find('>'):]
                
                for l in lines[1:i]:
                    list_text += l[2:] + '\n'
                
                day = line[line.find('დრო')+4:line.find('-')].strip()

            if 'რუკა' in line:
                maps = line[line.find('4>')+3:line.find('რუკა')].strip()

        list_text = list_text[:len(list_text)-3]    

        modal = TeamListModal(group, list_text, day, maps)

        await interaction.response.send_modal(modal)
        await modal.wait()
        group = modal.group
        list_text = modal.list_text.value
        match_day = modal.match_day
        total_maps = int(modal.total_maps.value)
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

        await list_message.edit(content=formatted_text)
        await interaction.response.defer()
        await interaction.response.is_done()

    @app_commands.command(name='check_in', description='თამაშის დასტურის მესიჯი')
    @app_commands.guild_only()
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

    @app_commands.command(name='cap', description='მენეჯერის როლის სხვისთვის მიცემა')
    @app_commands.guild_only()
    @app_commands.describe(member='ვისაც როლი გადაეცემა')
    async def cap(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.channel.id == 1241354436773806183:
            exception_roles = [1234921072940552224, self.bot.config.community_role_id]

            roles = []
            for _role in interaction.user.roles:
                if _role.id not in exception_roles and _role.name.startswith('ჯგუფი'):
                    roles.append({'role_name': _role.name, 'role_id': _role.id})
            
            if len(roles) == 1:
                query = 'SELECT * FROM cap_transfer_usage WHERE user_id = ? AND role_id = ?'
                db_result = await self.bot.db.fetchone(query, interaction.user.id, roles[0]['role_id'])

                if not db_result:
                    _role = interaction.guild.get_role(roles[0]['role_id'])
                    await member.add_roles(_role)

                    query = 'INSERT INTO cap_transfer_usage (user_id, role_id) VALUES (?, ?)'
                    await self.bot.db.execute(query, interaction.user.id, roles[0]['role_id'])

                    await interaction.response.send_message(f'როლი წარმატებით გადაეცა {member.mention}-ს.')
                else:
                    await interaction.response.send_message('თქვენ უკვე გადაცემული გაქვთ როლი სხვისთვის.', ephemeral=True)
            elif len(roles) > 1:
                view = discord.ui.View(timeout=None)
                view.add_item(CapSelect(self.bot, roles, member))

                await interaction.response.send_message('ქვემოთ მოცემული ჯგუფებიდან აირჩიე ჯგუფი, რომლის როლის გადაცემაც გსურს.', view=view, ephemeral=True)
        else:
            await interaction.response.send_message(f'ამ ქომანდის გამოყენება მხოლოდ აქ <#1241354436773806183> შეგიძლია.', ephemeral=True)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def clear_cap(self, ctx: commands.Context, role: str):
        _role = ctx.guild.get_role(int(role[3:len(role)-1]))
        query = 'DELETE FROM cap_transfer_usage WHERE role_id = ?'
        result = await self.bot.db.execute(query, _role.id)

        if result.rowcount == 0:
            await ctx.send('მონაცემები არ არსებობს.')
        else:
            await ctx.send('მონაცემები წარმატებით გასუფთავდა.')
        
    
async def setup(bot: Qolga):
    await bot.add_cog(GeneralCommands(bot))