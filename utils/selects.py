from typing import Any
import discord


class CheckInSelect(discord.ui.Select):
    def __init__(self, team_names: list[str], response_type: int):
        options = [
            discord.SelectOption(label=team_name, value=team_name)
            for team_name in team_names
        ]
        self.response_type = response_type

        super().__init__(placeholder='აირჩიე გუნდი', options=options, min_values=1, max_values=1, custom_id='qolga:check_in_select')

    async def callback(self, interaction: discord.Interaction):
        list_message = [message async for message in interaction.channel.history(limit=10)]
        list_content = list_message[len(list_message)-1].content

        response_message = 'უარყოფილი იქნა ❌' if self.response_type == 0 else 'დადასტურდა ✅'
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
            await interaction.response.send_message('თქვენ არ ხართ ლისტში მონიშნული', ephemeral=True)