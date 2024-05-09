import random

import discord

from datetime import datetime
from . import bot


async def create_ticket_channel(bot: bot.Qolga, interaction: discord.Interaction):
    ticket_category = interaction.guild.get_channel(bot.config.ticket_category_id)
    random_numbers = '{:04}'.format(random.randint(0, 9999))
    channel_name = f'ticket-{random_numbers}'

    ticket_channel = await interaction.guild.create_text_channel(
        channel_name, category=ticket_category
    )
    await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_message_history=True)

    welcome_embed = discord.Embed(color=bot.config.main_color)
    welcome_embed.description = 'ადმინისტრაცია მალე გიპასუხებთ'
    welcome_embed.set_footer(text=f'ავტორი {interaction.user.display_name}', icon_url=interaction.user.avatar.url)
    welcome_embed.timestamp = datetime.now()

    return ticket_channel, welcome_embed

class TicketSetupView(discord.ui.View):
    def __init__(self, bot: bot.Qolga):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='თიქეთის გახსნა', style=discord.ButtonStyle.secondary, custom_id='qolga:create_ticket')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.Button):
        ticket_channel, welcome_embed = await create_ticket_channel(self.bot, interaction)

        query = 'INSERT INTO ticket_interactions (user_id, channel_id) VALUES (?, ?)'
        await self.bot.db.execute(query, interaction.user.id, ticket_channel.id)

        view = TicketCloseView(self.bot)

        await ticket_channel.send(embed=welcome_embed, view=view)
        await interaction.response.send_message(f'თიქეთი შეიქმნა {ticket_channel.mention}', ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self, bot: bot.Qolga):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='დახურვა', style=discord.ButtonStyle.secondary, emoji='🔒', custom_id='qolga:close_ticket_first')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'SELECT user_id FROM ticket_interactions WHERE channel_id = ?'
        ticket_author_id = await self.bot.db.fetchone(query, interaction.channel.id)
        ticket_author = interaction.guild.get_member(ticket_author_id[0])

        user_permissions = interaction.channel.permissions_for(ticket_author)
        if user_permissions.view_channel:
            view = TicketCloseWarningView(self.bot)
            await interaction.response.send_message('დარწმუნებული ხარ, რომ თიქეთის დახურვა გინდა?', view=view)
        else:
            await interaction.channel.set_permissions(ticket_author, view_channel=False)
            await interaction.response.send_message(content='თიქეთი უკვე დახურულია!', ephemeral=True)

class TicketCloseWarningView(discord.ui.View):
    def __init__(self, bot: bot.Qolga):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='დახურვა', style=discord.ButtonStyle.danger, custom_id='qolga:close_ticket_main')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'SELECT user_id FROM ticket_interactions WHERE channel_id = ?'
        interaction_user_id = await self.bot.db.fetchone(query, interaction.channel.id)
        ticket_author = interaction.guild.get_member(interaction_user_id[0])

        embed = discord.Embed(color=self.bot.config.second_color)
        embed.description = f'თიქეთი დაიხურა {interaction.user.mention}-ს მიერ'

        await interaction.channel.set_permissions(ticket_author, view_channel=False)

        await interaction.message.delete()
        await interaction.response.defer()
        await interaction.channel.send(embed=embed, view=TicketClosedView(self.bot))
    
    @discord.ui.button(label='შეწყვეტა', style=discord.ButtonStyle.secondary, custom_id='qolga:cancel_close_ticket')
    async def cancel_close(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.message.delete()

class TicketClosedView(discord.ui.View):
    def __init__(self, bot: bot.Qolga):
        self.bot = bot
        super().__init__(timeout=None) 

    @discord.ui.button(label='გახსნა', style=discord.ButtonStyle.secondary, custom_id='qolga:reopen_ticket')
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'SELECT user_id FROM ticket_interactions WHERE channel_id = ?'
        interaction_user_id = await self.bot.db.fetchone(query, interaction.channel.id)
        ticket_author = interaction.guild.get_member(interaction_user_id[0])
    
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.description = f'თიქეთი გაიხსნა {interaction.user.mention}-ს მიერ'

        await interaction.channel.set_permissions(ticket_author, view_channel=True, send_messages=True, read_message_history=True)

        main_embed = interaction.message.embeds[0]

        await interaction.message.edit(embed=main_embed, view=None)
        await interaction.response.defer()
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label='წაშლა', style=discord.ButtonStyle.danger, custom_id='qolga:delete_ticket')
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'DELETE FROM ticket_interactions WHERE channel_id = ?'
        await self.bot.db.execute(query, interaction.channel.id)
        
        await interaction.channel.delete()