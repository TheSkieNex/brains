import discord

from . import bot

from utils.selects import CheckInSelect

class CheckInView(discord.ui.View):
    def __init__(self, bot: bot.Brains):
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