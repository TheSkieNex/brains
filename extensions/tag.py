import discord
import aiosqlite

from discord.ext import commands
from discord import app_commands

from utils.bot import Brains
from typing import Annotated, Optional


class TagName(commands.clean_content):
    def __init__(self, *, lower: bool = False):
        self.lower: bool = lower
        super().__init__()

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        return converted.strip() if not self.lower else lower

class TagModal(discord.ui.Modal, title='Tag Edit'):
    name = discord.ui.TextInput(
        label='Tag name', required=True, style=discord.TextStyle.short, min_length=1, max_length=64
    )
    content = discord.ui.TextInput(
        label='Tag content', required=True, style=discord.TextStyle.long, min_length=1, max_length=2000
    )

    def __init__(self, name: str, content: str):
        super().__init__()
        self.name.default = name
        self.content.default = content

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.name_text = str(self.name)
        self.content_text = str(self.content)
        self.stop()

class TagAllView(discord.ui.View):
    def __init__(
            self, 
            *, 
            data: list[tuple],
            color: discord.Color,
            timeout: float | None = 180
    ):
        self.data = data
        self.color = color
        self.k = 0
        self.max_page = (len(self.data) // 5) + 1
        super().__init__(timeout=timeout)

    async def create_embed(self, *, description: str, footer_text: str):
        embed = discord.Embed(color=self.color)
        embed.title = 'Tags'
        embed.description = description
        embed.set_footer(text=footer_text)

        return embed

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.blurple)
    async def fast_rewind_back(self, interaction: discord.Interaction, button: discord.Button):
        self.k = 0
        embed = await self.create_embed(
            description='\n'.join(tag[0] for tag in self.data[:5]),
            footer_text=f'Page 1/{self.max_page}'
        )
        
        await interaction.response.defer()
        await interaction.message.edit(embed=embed)
    
    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.blurple)
    async def rewind_back(self, interaction: discord.Interaction, button: discord.Button):
        if self.k > 0: self.k -= 1
        data = self.data[5*self.k:(self.k+1)*5]
        if data:
            embed = await self.create_embed(
                description='\n'.join(tag[0] for tag in data),
                footer_text=f'Page {self.k+1}/{self.max_page}'
            )
            
            await interaction.response.defer()
            await interaction.message.edit(embed=embed)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.blurple)
    async def rewind_forward(self, interaction: discord.Interaction, button: discord.Button):
        max_k = len(self.data) // 5
        if max_k*5 == len(self.data): max_k -= 1
        
        if self.k != max_k: self.k += 1
        data = self.data[5*self.k:(self.k+1)*5]
        if data:
            embed = await self.create_embed(
                description='\n'.join(tag[0] for tag in data),
                footer_text=f'Page {self.k+1}/{self.max_page}'
            )
            
            await interaction.response.defer()
            await interaction.message.edit(embed=embed)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.blurple)
    async def fast_rewind_forward(self, interaction: discord.Interaction, button: discord.Button):
        max_five_multiple = len(self.data) - (len(self.data) % 5) if (len(self.data) % 5) != 0 else len(self.data) - 5
        max_k = len(self.data) // 5
        if max_k*5 == len(self.data): max_k -= 1
        self.k = max_k

        embed = await self.create_embed(
            description='\n'.join(tag[0] for tag in self.data[max_five_multiple:]),
            footer_text=f'Page {self.max_page}/{self.max_page}'
        )

        await interaction.response.defer()
        await interaction.message.edit(embed=embed)

class Tag(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot

    async def get_tag(self, name: str, guild_id: int):
        query = """SELECT * FROM tags WHERE LOWER(name) = ? AND guild_id = ?"""
        result = await self.bot.db.fetchall(query, name.lower(), guild_id)

        return result
    
    async def create_tag(self, ctx: commands.Context, name: str, content: str):
        query = """INSERT INTO tags (name, content, guild_id) VALUES (?, ?, ?)"""
        try:
            await self.bot.db.execute(query, name, content, ctx.guild.id, commit=False)
        except aiosqlite.IntegrityError:
            await ctx.send(f'Tag named {name} already exists.')
        except:
            await ctx.send('Could not create a tag.')
        else:
            await self.bot.db.commit()
            await ctx.send(f'Tag {name} was created.')

    async def tags_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not current:
            result = await self.bot.db.fetchall('SELECT name FROM tags WHERE guild_id = ? LIMIT 12', interaction.guild.id)
        else:
            result = await self.bot.db.fetchall('SELECT name FROM tags WHERE LOWER(name) LIKE ? AND guild_id = ?', current.lower() + '%', interaction.guild.id)

        return [app_commands.Choice(name=tag, value=tag) for tag, in result]

    @commands.hybrid_group(fallback='get', description='Get a tag')
    @commands.guild_only()
    @app_commands.guild_only()
    @app_commands.describe(name='Tag\'s name')
    @app_commands.autocomplete(name=tags_autocomplete)
    async def tag(self, ctx: commands.Context, *, name: Annotated[str, TagName(lower=True)]):
        try:
            tag = await self.get_tag(name, ctx.guild.id)
            if not tag:
                return await ctx.send(f'Tag named {name} does not exist.', ephemeral=True)
        except RuntimeError as e:
            return await ctx.send(str(e))
        
        await ctx.send(tag[0][1])

    @tag.command(name='create', description='Create a tag')
    @commands.guild_only()
    @app_commands.describe(name='Tag\'s name', content='Tag\'s content')
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def tag_create(self, ctx: commands.Context, name: Annotated[str, TagName], *, content: Annotated[str, commands.clean_content]):
        if len(name) > 63:
            return await ctx.send('Tag name can\'t be more than 64 characters', ephemeral=True)

        if len(content) > 2000:
            return await ctx.send('Tag content can\'t be more than 2000 characters.', ephemeral=True)

        await self.create_tag(ctx, name, content)

    @tag.command(name='edit', description='Edit a tag')
    @commands.guild_only()
    @app_commands.describe(name='Tag\'s name', content='Tag\'s new content, if empty a modal will open')
    @app_commands.autocomplete(name=tags_autocomplete)
    # @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def tag_edit(
        self, 
        ctx: commands.Context, 
        name: Annotated[str, TagName(lower=True)], 
        *, 
        content: Annotated[Optional[str], commands.clean_content] = None
    ):
        changed_name = ''
        is_content = True

        if content is None:
            query = """SELECT name, content FROM tags WHERE LOWER(name) = ? AND guild_id = ?"""
            row = await self.bot.db.fetchone(query, name.lower(), ctx.guild.id)

            if not row:
                return await ctx.send(f'Tag named {name} does not exist.', ephemeral=True)

            modal = TagModal(row[0], row[1])
            await ctx.interaction.response.send_modal(modal)
            await modal.wait()
            ctx.interaction = modal.interaction
            changed_name = modal.name_text
            content = modal.content_text
            is_content = False
                
        if len(content) > 2000:
            return await ctx.send('Tag content can\'t be more than 2000 characters.')

        result = None
        if not is_content:
            query = 'UPDATE tags SET name = ?, content = ? WHERE LOWER(name) = ? AND guild_id = ?'
            result = await self.bot.db.execute(query, changed_name, content, name.lower(), ctx.guild.id)
        else:
            query = 'UPDATE tags SET content = ? WHERE LOWER(name) = ? AND guild_id = ?'
            result = await self.bot.db.execute(query, content, name.lower(), ctx.guild.id)

        if result.rowcount == 0:
            await ctx.send(f'Tag named {name} does not exist.', ephemeral=True)
        else:
            await ctx.send(f'Tag {name} was updated.')

    @tag.command(name='remove', description='Delete a tag', aliases=['delete'])
    @commands.guild_only()
    @app_commands.describe(name='Tag\'s name')
    @app_commands.autocomplete(name=tags_autocomplete)
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def tag_remove(self, ctx: commands.Context, name: str):
        query = """DELETE FROM tags WHERE LOWER(name) = ? AND guild_id = ?"""
        result = await self.bot.db.execute(query, name.lower(), ctx.guild.id)

        if result.rowcount == 0:
            await ctx.send(f'Tag named {name} does not exist.', ephemeral=True)
        else:
            await ctx.send(f'Tag {name} was deleted.')

    @tag.command(name='all', description='All tags')
    @commands.guild_only()
    async def tag_all(self, ctx: commands.Context):
        result = await self.bot.db.fetchall('SELECT * FROM tags WHERE guild_id = ?', ctx.guild.id)

        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = 'Tags'

        view = None
        page = (len(result) // 5) + 1 if len(result) % 5 != 0 else len(result) // 5
        if len(result) > 5:
            embed.description = '\n'.join(tag[0] for tag in result[:5])
            embed.set_footer(text=f'Page 1/{page}')

            view = TagAllView(data=result, color=self.bot.config.main_color, timeout=None)
        elif len(result) <= 5 and len(result) > 0:
            embed.description = '\n'.join(tag[0] for tag in result)
            embed.set_footer(text=f'Page 1/{page}')
        else:
            embed.description = 'There are no tags in this server'

        await ctx.send(embed=embed, view=view)

        
async def setup(bot: Brains):
    await bot.add_cog(Tag(bot))