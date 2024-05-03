import discord
import aiosqlite

from discord.ext import commands
from discord import app_commands

from utils.bot import Qolga


class TagModal(discord.ui.Modal, title='თეგის რედაქტირება'):
    content = discord.ui.TextInput(
        label='თეგის ტექტსი', required=True, style=discord.TextStyle.long, min_length=1, max_length=2000
    )

    def __init__(self, text: str):
        super().__init__()
        self.content.default = text

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.text = str(self.content)
        self.stop()
        

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
    @app_commands.describe(name='თაგის სახელი')
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

        if len(content) > 2000:
            return await interaction.response.send_message('თეგის ტექსტი არ შეიძლება 2000-ზე მეტი სიმბოლოსგან შედგებოდეს.')

        await self.create_tag(interaction, name, content)

    @tag_group.command(name='edit', description='თეგის რედაქტირება')
    @app_commands.describe(name='თეგის სახელი', content='თეგის ტექტსი, თუ ტექსტი ცარიელია გაიხსნება მოდალი')
    @app_commands.autocomplete(name=tags_autocomplete)
    async def edit(self, interaction: discord.Interaction, name: str, content: str = None):
        admin_role = interaction.guild.get_role(self.bot.config.organizer_role_id)
        if admin_role not in interaction.user.roles and interaction.user.id != self.bot.config.owner_user_id:
            return await interaction.response.send_message('შენ არ გაქვს ამ ქომანდის გამოყენების უფლება!', ephemeral=True)

        if content is None:
            query = """SELECT content FROM tags WHERE LOWER(name) = ?"""
            row = await self.bot.db.fetchone(query, name.lower())
            
            if not row:
                return await interaction.response.send_message(f'თეგი სახელად *{name}* არ არსებობს.', ephemeral=True)

            modal = TagModal(row[0])
            await interaction.response.send_modal(modal)
            await modal.wait()
            interaction = modal.interaction
            content = modal.text
                
        if len(content) > 2000:
            return await interaction.response.send_message('თეგის ტექსტი არ შეიძლება 2000-ზე მეტი სიმბოლოსგან შედგებოდეს.')

        query = """UPDATE tags SET content = ? WHERE LOWER(name) = ?"""
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



async def setup(bot: Qolga):
    await bot.add_cog(Tag(bot))