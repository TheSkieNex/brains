import discord

from discord.ext import commands
from discord import app_commands

from utils.bot import Brains
from utils.views import CheckInView

from datetime import datetime


class TeamListModal(discord.ui.Modal, title='ჯგუფის გუნდების სია'):
    header = discord.ui.TextInput(
        label='Header', required=True, style=discord.TextStyle.short,  min_length=1, max_length=64,
        placeholder='Tournament Name'
    )
    team_list = discord.ui.TextInput(
        label='Team List', required=True, style=discord.TextStyle.long, min_length=1, max_length=2000,
        placeholder='1. Team Name <@530689295699148800> \n2. Team Name <@967529104435990608>'
    )
    footer = discord.ui.TextInput(
        label='Footer', required=False, style=discord.TextStyle.paragraph, min_length=0, max_length=128,
        placeholder=f'Match Day: {datetime.now().strftime("%B %d")} \nTime: {datetime.now().strftime("%H:%M")}'
    )

    def __init__(
        self, 
        header: str = None, 
        team_list: str = None,
        footer: str = None,
    ):
        self.header.default = header
        self.team_list.default = team_list
        self.footer.default = footer
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class CheckInSelect(discord.ui.Select):
    def __init__(self, team_names: list[str], response_type: int):
        options = [
            discord.SelectOption(label=team_name, value=team_name)
            for team_name in team_names
        ]
        self.response_type = response_type

        super().__init__(placeholder='Select a team', options=options, min_values=1, max_values=1, custom_id='Brains:check_in_select')

    async def callback(self, interaction: discord.Interaction):
        list_message = [message async for message in interaction.channel.history(limit=10)]
        list_content = list_message[len(list_message)-1].content

        response_message = 'was rejected ❌' if self.response_type == 0 else 'was confirmed ✅'
        format = '~~' if self.response_type == 0 else '__'

        if interaction.user.id in list_message[len(list_message)-1].raw_mentions:
            lines = list_content.split('\n')

            for i, line in enumerate(lines):
                if str(interaction.user.id) in line and self.values[0] in line:
                    dot_index = line.find('.')
                    id_index = line.find(f'<@{interaction.user.id}>')

                    team_name = line[dot_index+1:id_index].strip()
                    team_name_clean = (
                        team_name[2:len(team_name)-2] 
                        if team_name.startswith('_') 
                        or team_name.startswith('~') 
                        else team_name
                    )
                    updated_line = line[0:dot_index] + '. ' + format+team_name_clean+format + ' ' + line[id_index:]
                    lines[i] = updated_line 
                    break

            await list_message[len(list_message)-1].edit(content='\n'.join(lines))
            await interaction.response.send_message(self.values[0] + ' ' + response_message, ephemeral=True)
        else:
            await interaction.response.send_message('You are not tagged in the list', ephemeral=True)

class CheckInView(discord.ui.View):
    def __init__(self, bot: Brains):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, custom_id='Brains:check_in_confirm')
    async def accept_button(self, interaction: discord.Interaction, button: discord.Button):
        await self.execute_interaction(interaction, 1)

    @discord.ui.button(label='Reject', style=discord.ButtonStyle.danger, custom_id='Brains:check_in_reject')
    async def reject_button(self, interaction: discord.Interaction, button: discord.Button):
        await self.execute_interaction(interaction, 0)

    async def execute_interaction(self, interaction: discord.Interaction, type: int):
        list_message = [message async for message in interaction.channel.history(limit=100)]
        list_content = list_message[len(list_message)-1].content

        response_message = 'Rejected ❌' if type == 0 else 'Confirmed ✅'
        response = 'already rejected' if type == 0 else 'already confirmed'
        format = '~~' if type == 0 else '__'

        if interaction.user.id in list_message[len(list_message)-1].raw_mentions:
            lines = list_content.split('\n')

            if list_message[len(list_message)-1].raw_mentions.count(interaction.user.id) == 1:
                for i, line in enumerate(lines):
                    if str(interaction.user.id) in line:
                        dot_index = line.find('.')
                        id_index = line.find('<@')
                        
                        team_name = line[dot_index+1:id_index].strip()
                        team_name_clean = (
                            team_name[2:len(team_name)-2] 
                            if team_name.startswith('__')
                            or team_name.startswith('~~')
                            else team_name
                        )
                        updated_line = line[0:dot_index] + '. ' + format+team_name_clean+format + ' ' + line[id_index:]
                        lines[i] = updated_line                        
                        break
                
                await list_message[len(list_message)-1].edit(content='\n'.join(lines))
                await interaction.response.send_message(response_message, ephemeral=True)
            else:
                team_names = []
                for i, line in enumerate(lines):
                    if str(interaction.user.id) in line:
                        dot_index = line.find('.')
                        id_index = line.find(f'<@{interaction.user.id}>')

                        team_name = line[dot_index+1:id_index].strip()
                        if not team_name.startswith(format):
                            team_name_clean = (
                                team_name[2:len(team_name)-2] 
                                if team_name.startswith('_') 
                                or team_name.startswith('~') 
                                else team_name
                            )
                            team_names.append(team_name_clean)
                
                if team_names:
                    view = discord.ui.View(timeout=None)
                    view.add_item(CheckInSelect(team_names, type))

                    await interaction.response.send_message('Select a team from below', view=view, ephemeral=True)
                else:
                    await interaction.response.send_message(f'Your teams are {response}', ephemeral=True)
        else:
            await interaction.response.send_message('You are not tagged in the list', ephemeral=True)

class ListCommands(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot

    list_group = app_commands.Group(
        name='list', 
        description='list group', 
        guild_only=True, 
        default_permissions=discord.Permissions(administrator=True)
    )

    @list_group.command(name='send', description='Send a team list')
    @app_commands.describe(channel='Channel where team list will be sent')
    async def list_send(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not channel:
            channel = interaction.channel

        modal = TeamListModal()

        await interaction.response.send_modal(modal)
        await modal.wait()
        header = modal.header.value
        team_list = modal.team_list.value
        footer = modal.footer.value
        interaction = modal.interaction

        lines = team_list.split('\n')
        formatted_lines = '\n'.join(lines)
        formatted_footer = '\n' + footer

        formatted_text = f"""
            {header}
            {formatted_lines}
            {formatted_footer}
        """

        await channel.send(formatted_text)
        await interaction.response.defer()


    @list_group.command(name='edit', description='Edit a team list')
    async def list_edit(self, interaction: discord.Interaction):
        channel_messages = [message async for message in interaction.channel.history(limit=100)]
        list_message = channel_messages[len(channel_messages)-1]
        list_message_content = list_message.content

        lines = list_message_content.split('\n')

        header = '\n'.join(lines[:next(index for index, line in enumerate(lines) if '<@' in line)])
        team_list = '\n'.join(
            lines[
                next(index for index, line in enumerate(lines) if '<@' in line)
                :
                max(index for index, line in enumerate(lines) if line.strip() and (line[0] == '>' or line[0].isdigit())) + 1
            ]
        )
        footer = '\n'.join(lines[max(index for index, line in enumerate(lines) if line.strip() and (line[0] == '>' or line[0].isdigit())) + 1:])

        modal = TeamListModal(header.strip(), team_list.strip(), footer.strip())

        await interaction.response.send_modal(modal)
        await modal.wait()
        header = modal.header.value
        team_list = modal.team_list.value
        footer = modal.footer.value
        interaction = modal.interaction

        lines = team_list.split('\n')
        formatted_lines = '\n'.join(lines)
        formatted_footer = '\n' + footer

        formatted_text = f"""
            {header}
            {formatted_lines}
            {formatted_footer}
        """

        await list_message.edit(content=formatted_text)
        await interaction.response.defer()

    @app_commands.command(name='checkin', description='Send a check in embed')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def check_in(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(color=self.bot.config.main_color)
            embed.description = (
                '**Please confirm whether you are playing or not**'
            )

            await interaction.response.send_message(embed=embed, view=CheckInView(self.bot))
        except:
            await interaction.response.send_message('Something .', ephemeral=True)
        

async def setup(bot: Brains):
    await bot.add_cog(ListCommands(bot))