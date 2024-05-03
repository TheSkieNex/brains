import discord
import aiosqlite

from discord.ext import commands
from discord import app_commands

from utils.bot import Qolga


class TagModal(discord.ui.Modal, title='თეგის რედაქტირება'):
    name = discord.ui.TextInput(
        label='თეგის სახელი', required=True, style=discord.TextStyle.short, min_length=1, max_length=64
    )
    content = discord.ui.TextInput(
        label='თეგის ტექტსი', required=True, style=discord.TextStyle.long, min_length=1, max_length=2000
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

    def create_embed(self, *, description: str, footer_text: str):
        embed = discord.Embed(color=self.color)
        embed.title = 'თეგები'
        embed.description = description
        embed.set_footer(text=footer_text)

        return embed

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.blurple)
    async def fast_rewind_back(self, interaction: discord.Interaction, button: discord.Button):
        self.k = 0
        embed = self.create_embed(
            description='\n'.join(tag[0] for tag in self.data[:5]),
            footer_text=f'გვერდი 1/{self.max_page}'
        )
        
        await interaction.response.defer()
        await interaction.message.edit(embed=embed)
    
    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.blurple)
    async def rewind_back(self, interaction: discord.Interaction, button: discord.Button):
        if self.k > 0: self.k -= 1
        data = self.data[5*self.k:(self.k+1)*5]
        if data:
            embed = self.create_embed(
                description='\n'.join(tag[0] for tag in data),
                footer_text=f'გვერდი {self.k+1}/{self.max_page}'
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
            embed = self.create_embed(
                description='\n'.join(tag[0] for tag in data),
                footer_text=f'გვერდი {self.k+1}/{self.max_page}'
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

        embed = self.create_embed(
            description='\n'.join(tag[0] for tag in self.data[max_five_multiple:]),
            footer_text=f'გვერდი {self.max_page}/{self.max_page}'
        )

        await interaction.response.defer()
        await interaction.message.edit(embed=embed)

class Tag(commands.Cog):
    def __init__(self, bot: Qolga):
        self.bot = bot

    tag_group = app_commands.Group(name='tag', description='tag group', guild_only=True)

    async def get_tag(self, name: str):
        query = """SELECT * FROM tags WHERE LOWER(name) = ?"""
        result = await self.bot.db.fetchall(query, name.lower())

        return result
    
    async def create_tag(self, interaction: discord.Interaction, name: str, content: str):
        query = """INSERT INTO tags (name, content) VALUES (?, ?)"""
        try:
            await self.bot.db.execute(query, name, content, commit=False)
        except aiosqlite.IntegrityError:
            await interaction.response.send_message('ეს თეგი უკვე არსებობს.')
        except:
            await interaction.response.send_message('ვერ შეიქმნა თეგი')
        else:
            await self.bot.db.commit()
            await interaction.response.send_message(f'თეგი *{name}* წარმატებით შეიქმნა.')

    async def tags_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not current:
            result = await self.bot.db.fetchall('SELECT name FROM tags LIMIT 12')
        else:
            result = await self.bot.db.fetchall('SELECT name FROM tags WHERE LOWER(name) LIKE ?', current.lower() + '%')

        return [app_commands.Choice(name=tag, value=tag) for tag, in result]
    
    @tag_group.command(name='get', description='თეგის გამოძახება')
    @app_commands.describe(name='თეგის სახელი')
    @app_commands.autocomplete(name=tags_autocomplete)
    async def tag(self, interaction: discord.Interaction, name: str):
        try:
            tag = await self.get_tag(name)
            if not tag:
                return await interaction.response.send_message(f'თეგი სახელად *{name}* არ არსებობს.', ephemeral=True)
        except RuntimeError as e:
            return await interaction.response.send_message(str(e))

        await interaction.response.send_message(tag[0][1])

    @tag_group.command(name='create', description='თეგის შექმნა')
    @app_commands.describe(name='თეგის სახელი', content='თეგის თექსტი')
    async def create(self, interaction: discord.Interaction, name: str, content: str):
        admin_role = interaction.guild.get_role(self.bot.config.organizer_role_id)
        if admin_role not in interaction.user.roles and interaction.user.id != self.bot.config.owner_user_id:
            return await interaction.response.send_message('შენ არ გაქვს ამ ქომანდის გამოყენების უფლება!', ephemeral=True)

        if len(name) > 63:
            return await interaction.response.send_message('თეგის სახელი არ შეიძლება 64-ზე მეტი სიმბოლოსგან შედგებოდეს', ephemeral=True)

        if len(content) > 2000:
            return await interaction.response.send_message('თეგის ტექსტი არ შეიძლება 2000-ზე მეტი სიმბოლოსგან შედგებოდეს.', ephemeral=True)

        await self.create_tag(interaction, name, content)

    @tag_group.command(name='edit', description='თეგის რედაქტირება')
    @app_commands.describe(name='თეგის სახელი', content='თეგის ტექტსი, თუ ტექსტი ცარიელია გაიხსნება მოდალი')
    @app_commands.autocomplete(name=tags_autocomplete)
    async def edit(self, interaction: discord.Interaction, name: str, content: str = None):
        admin_role = interaction.guild.get_role(self.bot.config.organizer_role_id)
        if admin_role not in interaction.user.roles and interaction.user.id != self.bot.config.owner_user_id:
            return await interaction.response.send_message('შენ არ გაქვს ამ ქომანდის გამოყენების უფლება!', ephemeral=True)

        changed_name = ''
        is_content = True
        if content is None:
            query = """SELECT name, content FROM tags WHERE LOWER(name) = ?"""
            row = await self.bot.db.fetchone(query, name.lower())

            if not row:
                return await interaction.response.send_message(f'თეგი სახელად *{name}* არ არსებობს.', ephemeral=True)

            modal = TagModal(row[0], row[1])
            await interaction.response.send_modal(modal)
            await modal.wait()
            interaction = modal.interaction
            changed_name = modal.name_text
            content = modal.content_text
            is_content = False
                
        if len(content) > 2000:
            return await interaction.response.send_message('თეგის ტექსტი არ შეიძლება 2000-ზე მეტი სიმბოლოსგან შედგებოდეს.')

        result = None
        if not is_content:
            query = 'UPDATE tags SET name = ?, content = ? WHERE LOWER(name) = ?'
            result = await self.bot.db.execute(query, changed_name, content, name.lower())
        else:
            query = 'UPDATE tags SET content = ? WHERE LOWER(name) = ?'
            result = await self.bot.db.execute(query, content, name.lower())

        if result.rowcount == 0:
            await interaction.response.send_message(f'თეგი სახელად *{name}* არ არსებობს.', ephemeral=True)
        else:
            await interaction.response.send_message(f'თეგი *{name}* წარმატებით განახლდა.')

    @tag_group.command(name='remove', description='თეგის წაშლა')
    @app_commands.describe(name='თეგის სახელი')
    @app_commands.autocomplete(name=tags_autocomplete)
    async def remove(self, interaction: discord.Interaction, name: str):
        admin_role = interaction.guild.get_role(self.bot.config.organizer_role_id)
        if admin_role not in interaction.user.roles and interaction.user.id != self.bot.config.owner_user_id:
            return await interaction.response.send_message('შენ არ გაქვს ამ ქომანდის გამოყენების უფლება!', ephemeral=True)

        query = """DELETE FROM tags WHERE LOWER(name) = ?"""
        result = await self.bot.db.execute(query, name.lower())

        if result.rowcount == 0:
            await interaction.response.send_message(f'თეგი სახელად *{name}* არ არსებობს.', ephemeral=True)
        else:
            await interaction.response.send_message(f'თეგი *{name}* წარმატებით წაიშალა.')

    @tag_group.command(name='all', description='თეგების სია')
    async def all(self, interaction: discord.Interaction):
        result = await self.bot.db.fetchall('SELECT * FROM tags')

        embed = discord.Embed(color=self.bot.config.main_color)
        embed.title = 'თეგები'

        view = None
        page = (len(result) // 5) + 1 if len(result) % 5 != 0 else len(result) // 5
        if len(result) > 5:
            embed.description = '\n'.join(tag[0] for tag in result[:5])
            embed.set_footer(text=f'გვერდი 1/{page}')

            view = TagAllView(data=result, color=self.bot.config.main_color, timeout=None)
        else:
            embed.description = '\n'.join(tag[0] for tag in result)
            embed.set_footer(text=f'გვერდი 1/{page}')

        await interaction.response.send_message(embed=embed, view=view)

        
async def setup(bot: Qolga):
    await bot.add_cog(Tag(bot))