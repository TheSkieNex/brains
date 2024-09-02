import discord

from discord.ext import commands
from discord import app_commands
from discord.utils import format_dt

from utils.bot import Brains
from datetime import datetime


class HelpCommandsView(discord.ui.View):
    def __init__(
            self, 
            *, 
            data: list[discord.Embed.fields],
            color: discord.Color,
            timeout: float | None = 180
    ):
        self.data = data
        self.color = color
        self.k = 0
        self.max_page = (len(self.data) // 3)
        super().__init__(timeout=timeout)

    async def create_embed(self, *, fields: list[discord.Embed.fields], footer_text: str):
        embed = discord.Embed(color=self.color)
        embed.title = 'Commands'
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=False)

        embed.set_footer(text=footer_text)

        return embed

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.blurple)
    async def fast_rewind_back(self, interaction: discord.Interaction, button: discord.Button):
        self.k = 0
        embed = await self.create_embed(
            fields=self.data[:3],
            footer_text=f'Page 1/{self.max_page}'
        )
        
        await interaction.response.defer()
        await interaction.message.edit(embed=embed)
    
    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.blurple)
    async def rewind_back(self, interaction: discord.Interaction, button: discord.Button):
        if self.k > 0: self.k -= 1
        data = self.data[3*self.k:(self.k+1)*3]
        if data:
            embed = await self.create_embed(
                fields=data,
                footer_text=f'Page {self.k+1}/{self.max_page}'
            )
            
            await interaction.response.defer()
            await interaction.message.edit(embed=embed)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.blurple)
    async def rewind_forward(self, interaction: discord.Interaction, button: discord.Button):
        max_k = len(self.data) // 3
        if max_k*3 == len(self.data): max_k -= 1
        
        if self.k != max_k: self.k += 1
        data = self.data[3*self.k:(self.k+1)*3]
        if data:
            embed = await self.create_embed(
                fields=data,
                footer_text=f'Page {self.k+1}/{self.max_page}'
            )
            
            await interaction.response.defer()
            await interaction.message.edit(embed=embed)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.blurple)
    async def fast_rewind_forward(self, interaction: discord.Interaction, button: discord.Button):
        max_five_multiple = len(self.data) - (len(self.data) % 3) if (len(self.data) % 3) != 0 else len(self.data) - 3
        max_k = len(self.data) // 3
        if max_k*3 == len(self.data): max_k -= 1
        self.k = max_k

        embed = await self.create_embed(
            fields=self.data[max_five_multiple:],
            footer_text=f'Page {self.max_page}/{self.max_page}'
        )

        await interaction.response.defer()
        await interaction.message.edit(embed=embed)

class Information(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot


    @commands.hybrid_command(name='help', description='Help command')
    @commands.guild_only()
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(color=self.bot.config.main_color)

        embed.title = 'Commands'

        embed_fields = [
            {'name': 'Information', 'value': """
                **/server** - shows server information
                **/user** - shows user information
            """},
            {'name': 'Moderation', 'value': """
                **/kick {target}** - kicks a user
                **/ban {target}** - bans a user
                **purge {limit}** - deletes number of messages in a channel 
            """},
            {'name': 'Tag', 'value': """
                **get [name]** - returns saved tag
                **all** - returns list of tags of the server
                **create [name] [content]** - creates a tag in the server with specific name and it's content
                **edit [name] {content}** - edits a tag. If content is empty discord modal will open with it's data
                **remove [name]** - deletes a tag
            """},
            {'name': 'Ticket System', 'value': """
                **/setup {category}** - setup ticket system, category where ticket channels will be created
                **/system setup** - sends system message in the channel where ticket system was created
                **/system edit {channel} {category}** - edits ticket system. Opens a discord modal. Channel and category are not required, if specified they will update accordingly
                **/system delete** - deletes ticket system
            """},
            {'name': 'Team List', 'value': """
                **/send {channel}** - sends a list in a channel. Opens a modal, put data as it is shown in the placeholders of input fields
                **/edit** - edits team list message in a channel. Make sure that the message itself is the first message in the channel
                **/check_in** - sends check in message in a channel. Make sure team list message and this message are in the same channel
            """},
            {'name': 'Other', 'value': """
                **?steal [emoji]** - steals an emoji from other server and adds it to your server
                **?give [role]** - adds the role to each mentioned user in a message. Make sure to reply to the message with this command in order to make it work
                **?remove [role]** - removes the role from each mentioned user. Same tip as above
            """},
        ]

        for field in embed_fields[:3]:
            embed.add_field(name=field['name'], value=field['value'], inline=False)

        page = (len(embed_fields) // 3) + 1 if len(embed_fields) % 3 != 0 else len(embed_fields) // 3
        embed.set_footer(text=f'Page 1/{page}')

        view = HelpCommandsView(data=embed_fields, color=self.bot.config.main_color, timeout=None)

        await ctx.send(embed=embed, view=view)

    @app_commands.command(name='server', description='Server information')
    @app_commands.guild_only()
    async def server_info(self, interaction: discord.Interaction):
        online = []
        offline = []

        for member in interaction.guild.members:
            if str(member.status) in ('online', 'dnd'):
                online.append(str(member))
            else:
                offline.append(str(member))

        roles = []

        for role in interaction.guild.roles:
            roles.append(str(role.mention))

        roles.reverse()
        roles.pop()
        
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = interaction.guild.name
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        embed.description = f'Created: {format_dt(interaction.guild.created_at, style="R")}'
        embed.add_field(name='Server ID', value=interaction.guild.id, inline=False)
        embed.add_field(name='Server Owner', value=interaction.guild.owner.mention, inline=False)
        embed.add_field(name=f'Roles - {len(interaction.guild.roles)}', value=' '.join(roles), inline=False)
        embed.add_field(name=f'Members - {len(interaction.guild.members)}', value=(
            f'<:green:1235625157389979700> {len(online)}   <:gray:1235625075672350731> {len(offline)}'
        ), inline=False)
        embed.add_field(name=f'Channels - {len(interaction.guild.channels)}', value=(
            f'Category: {len(interaction.guild.categories)}\n'
            f'Text: {len(interaction.guild.text_channels)}\n'
            f'Voice: {len(interaction.guild.voice_channels)}'
        ), inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='user', description='User information')
    @app_commands.guild_only()
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        if not member:
            member = interaction.user

        roles = []

        for role in member.roles:
            roles.append(str(role.mention))

        roles.reverse()
        roles.pop()
        
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.add_field(name='User', value=member.mention, inline=False)
        embed.add_field(name='User ID', value=member.id, inline=False)
        embed.add_field(name='Created', value=format_dt(member.created_at, style="R"), inline=False)
        embed.add_field(name='Joined', value=format_dt(member.joined_at, style="R"), inline=False)
        if len(member.roles) == 1:
            embed.add_field(name='Roles', value='None' , inline=False)
        else:
            embed.add_field(name=f'Roles - {len(roles)}', value=f'{" ".join(roles)}' , inline=False)

        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            
        await interaction.response.send_message(embed=embed)


async def setup(bot: Brains):
    await bot.add_cog(Information(bot))