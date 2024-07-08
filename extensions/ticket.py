import random

import discord

from discord.ext import commands
from discord import app_commands

from utils.bot import Brains
from datetime import datetime


class TicketSetupModal(discord.ui.Modal, title='Ticket System Setup'):
    system_title = discord.ui.TextInput(
        label='Sytem Title', style=discord.TextStyle.short,
        placeholder='Title for the ticket system embed',
        min_length=1, max_length=64
    )
    system_message = discord.ui.TextInput(
        label='Sytem Message', style=discord.TextStyle.long, 
        placeholder='Message which will be shown on the ticket system embed',
        min_length=1, max_length=1200
    )
    button_message = discord.ui.TextInput(
        label='Ticket System Button Text', style=discord.TextStyle.short,
        placeholder='Text which will be displayed on the ticket system\'s create button',
        min_length=1, max_length=64
    )
    ticket_message = discord.ui.TextInput(
        label='Ticket Channel Message', style=discord.TextStyle.long, 
        placeholder='Message which will be shown in the ticket channels',
        min_length=1, max_length=1200
    )

    def __init__(
            self, 
            sys_title: str | None = None,
            sys_message: str | None = None, 
            btn_text: str | None = None,
            ticket_message: str | None = None
    ):
        super().__init__()
        self.system_title.default = sys_title
        self.system_message.default = sys_message
        self.button_message.default = btn_text
        self.ticket_message.default = ticket_message

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.title_text = str(self.system_title)
        self.system_text = str(self.system_message)
        self.button_text = str(self.button_message)
        self.ticket_text = str(self.ticket_message)
        self.stop()

class TicketSetupView(discord.ui.View):
    def __init__(self, bot: Brains):
        super().__init__(timeout=None)
        self.bot = bot

        self.create_ticket_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            custom_id='Brains:create_ticket'
        )
        self.create_ticket_button.callback = self.create_ticket
        self.add_item(self.create_ticket_button)

    async def setup(self, guild_id: int):
        label = await self.fetch_label_text(guild_id)
        self.create_ticket_button.label = label

    async def fetch_label_text(self, guild_id: int):
        query = 'SELECT button_text FROM ticket_system_messages WHERE guild_id = ?'
        button_text = await self.bot.db.fetchone(query, guild_id)

        return button_text[0] if button_text else 'Creat ticket'

    async def create_ticket_channel(self, interaction: discord.Interaction):
        category_id = await self.bot.db.fetchone('SELECT category_id FROM ticket_systems WHERE guild_id = ?', interaction.guild.id)

        ticket_category = interaction.guild.get_channel(category_id[0]) if category_id else None
        random_numbers = f'{random.randint(0, 9999):04}'
        channel_name = f'ticket-{random_numbers}'

        ticket_message = await self.bot.db.fetchone('SELECT ticket_message FROM ticket_system_messages WHERE guild_id = ?', interaction.guild.id)

        if ticket_message:
            ticket_channel = await interaction.guild.create_text_channel(
                channel_name, category=ticket_category
            )
            await ticket_channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_message_history=True)
            

            welcome_embed = discord.Embed(color=self.bot.config.main_color)
            welcome_embed.description = ticket_message[0]
            welcome_embed.set_footer(text=f'Author {interaction.user.display_name}', icon_url=interaction.user.avatar.url)
            welcome_embed.timestamp = datetime.now()

            return ticket_channel, welcome_embed

    async def create_ticket(self, interaction: discord.Interaction):
        ticket_channel, welcome_embed = await self.create_ticket_channel(interaction)

        if ticket_channel and welcome_embed:
            query = 'INSERT INTO ticket_interactions (user_id, channel_id) VALUES (?, ?)'
            await self.bot.db.execute(query, interaction.user.id, ticket_channel.id)

            view = TicketCloseView(self.bot)

            await ticket_channel.send(embed=welcome_embed, view=view)
            await interaction.response.send_message(f'Ticket was created {ticket_channel.mention}', ephemeral=True)
        else:
            await interaction.response.send_message('err', ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self, bot: Brains):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='Close', style=discord.ButtonStyle.secondary, emoji='🔒', custom_id='Brains:close_ticket_first')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'SELECT user_id FROM ticket_interactions WHERE channel_id = ?'
        ticket_author_id = await self.bot.db.fetchone(query, interaction.channel.id)
        ticket_author = interaction.guild.get_member(ticket_author_id[0])

        user_permissions = interaction.channel.permissions_for(ticket_author)
        if user_permissions.view_channel:
            view = TicketCloseWarningView(self.bot)
            await interaction.response.send_message('Are you sure you want to close the ticket?', view=view)
        else:
            await interaction.channel.set_permissions(ticket_author, view_channel=False)
            await interaction.response.send_message(content='Ticket is already closed!', ephemeral=True)

class TicketCloseWarningView(discord.ui.View):
    def __init__(self, bot: Brains):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='Close', style=discord.ButtonStyle.danger, custom_id='Brains:close_ticket_main')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'SELECT user_id FROM ticket_interactions WHERE channel_id = ?'
        interaction_user_id = await self.bot.db.fetchone(query, interaction.channel.id)
        ticket_author = interaction.guild.get_member(interaction_user_id[0])

        embed = discord.Embed(color=self.bot.config.second_color)
        embed.description = f'Ticket was closed by {interaction.user.mention}'

        await interaction.channel.set_permissions(ticket_author, view_channel=False)

        await interaction.message.delete()
        await interaction.response.defer()
        await interaction.channel.send(embed=embed, view=TicketClosedView(self.bot))
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary, custom_id='Brains:cancel_close_ticket')
    async def cancel_close(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.message.delete()

class TicketClosedView(discord.ui.View):
    def __init__(self, bot: Brains):
        super().__init__(timeout=None) 
        self.bot = bot

    @discord.ui.button(label='Reopen', style=discord.ButtonStyle.secondary, custom_id='Brains:reopen_ticket')
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'SELECT user_id FROM ticket_interactions WHERE channel_id = ?'
        interaction_user_id = await self.bot.db.fetchone(query, interaction.channel.id)
        ticket_author = interaction.guild.get_member(interaction_user_id[0])
    
        embed = discord.Embed(color=self.bot.config.main_color)
        embed.description = f'Ticket was reopened by {interaction.user.mention}'

        await interaction.channel.set_permissions(ticket_author, view_channel=True, send_messages=True, read_message_history=True)

        main_embed = interaction.message.embeds[0]

        await interaction.message.edit(embed=main_embed, view=None)
        await interaction.response.defer()
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label='Delete', style=discord.ButtonStyle.danger, custom_id='Brains:delete_ticket')
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.Button):
        query = 'DELETE FROM ticket_interactions WHERE channel_id = ?'
        await self.bot.db.execute(query, interaction.channel.id)
        
        await interaction.channel.delete()

# class TicketSytemView(discord.ui.View):
#     def __init__(self, query_list: list[tuple]):
#         super().__init__(timeout=None)
#         options = [
#             discord.SelectOption(label=ticket_system[1], value=ticket_system[0])
#             for ticket_system in query_list
#         ]
#         self.system_select = discord.ui.Select(
#             custom_id='Brains:system_select',
#             placeholder='Select a ticket system',
#             options=options
#         )
#         self.system_select.callback = self.system_select_callback
#         self.add_item(self.system_select)

#     async def system_select_callback(self, interaction: discord.Interaction):
#         self.interaction = interaction
#         self.stop()

class Ticket(commands.Cog):
    def __init__(self, bot: Brains):
        self.bot = bot

    ticket_group = app_commands.Group(
        name='ticket', 
        description='ticket group', 
        guild_only=True, 
        default_permissions=discord.Permissions(administrator=True)
    )

    ticket_system_group = app_commands.Group(
        name='system', 
        description='ticket system group', 
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True)
    )

    ticket_group.add_command(ticket_system_group)
    
    @ticket_group.command(name='setup', description='Setup new ticket system in a server')
    async def ticket_setup(self, interaction:  discord.Interaction, category: discord.CategoryChannel = None):
        ticket_already_exists = await self.bot.db.fetchone('SELECT id FROM ticket_systems WHERE guild_id = ?', interaction.guild.id)
        if ticket_already_exists:
            return await interaction.response.send_message('Ticket system on this server already exists', ephemeral=True)
        
        category_id = category.id if category else None

        modal = TicketSetupModal()

        await interaction.response.send_modal(modal)
        await modal.wait()

        interaction = modal.interaction
        system_title = modal.title_text
        system_text = modal.system_text
        button_text = modal.button_text
        ticket_text = modal.ticket_text

        try:
            ticket_system = await self.bot.db.execute(
                'INSERT INTO ticket_systems (channel_id, category_id, guild_id) VALUES (?, ?, ?)', 
                interaction.channel.id, category_id, interaction.guild.id
            )
            await self.bot.db.execute(
                'INSERT INTO ticket_system_messages (system_id, guild_id, system_title, system_message, button_text, ticket_message) VALUES (?, ?, ?, ?, ?, ?)',
                ticket_system.lastrowid, interaction.guild.id, system_title, system_text, button_text, ticket_text
            )

            await interaction.response.send_message(f'Ticket system was successfully created for {interaction.channel.mention} channel')
        except:
            await interaction.response.send_message('Something unexpected happened', ephemeral=True)

    @ticket_system_group.command(name='setup', description='Send a ticket system message to the ticket system channel')
    async def ticket_system_setup(self, interaction: discord.Interaction):
        # query = """
        #     SELECT ts.id, tsm.system_title
        #     FROM ticket_systems ts
        #     JOIN ticket_system_messages tsm ON ts.id = tsm.system_id
        #     WHERE ts.guild_id = ?
        # """
        # query_result = await self.bot.db.fetchone(query, interaction.guild.id)

        query = 'SELECT channel_id FROM ticket_systems WHERE guild_id = ?'
        system_channel_id = await self.bot.db.fetchone(query, interaction.guild.id)

        # if len(query_result) > 1:
        #     view = TicketSytemView(query_result)
        
        #     await interaction.response.send_message(view=view, ephemeral=True)
        #     await view.wait()

        #     interaction = view.interaction

        #     system_id, system_title = query_result[int(interaction.data['values'][0])]

        #     query = 'SELECT channel_id FROM ticket_systems WHERE id = ?'

        #     system_channel_id = (await self.bot.db.fetchone(query, system_id))[0]

        system_channel = interaction.guild.get_channel(system_channel_id[0])

        if not system_channel_id or not system_channel:
            return await interaction.response.send_message('There is no ticket system set up or the system channel doesn\'t exist anymore.', ephemeral=True)
        
        system_title, system_message = await self.bot.db.fetchone(
            'SELECT system_title, system_message FROM ticket_system_messages WHERE guild_id = ?',
            interaction.guild.id
        )

        if system_title and system_message:
            embed = discord.Embed(color=self.bot.config.main_color)
            embed.title = system_title
            embed.description = system_message

            view = TicketSetupView(self.bot)
            await view.setup(interaction.guild.id)

            await system_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f'Ticket system was sent to {system_channel.mention}', ephemeral=True)

    @ticket_system_group.command(name='edit', description='Edit a ticket system')
    @app_commands.describe(channel='New channel for the ticket system', category='Category where ticket channels will be created')
    async def ticket_system_edit(self, interaction: discord.Interaction, channel: discord.TextChannel = None, category: discord.CategoryChannel = None):
        _system_title, system_message, _button_text, ticket_message = await self.bot.db.fetchone(
            'SELECT system_title, system_message, button_text, ticket_message FROM ticket_system_messages WHERE guild_id = ?',
            interaction.guild.id
        )
        modal = TicketSetupModal(
            _system_title, 
            system_message,
            _button_text, 
            ticket_message
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        interaction = modal.interaction
        system_title = modal.title_text
        system_text = modal.system_text
        button_text = modal.button_text
        ticket_text = modal.ticket_text

        try:
            updated = False

            if channel:
                await self.bot.db.execute('UPDATE ticket_systems SET channel_id = ? WHERE guild_id = ?', channel.id, interaction.guild.id)
                updated = True
            
            if category:
                await self.bot.db.execute('UPDATE ticket_systems SET category_id = ? WHERE guild_id = ?', category.id, interaction.guild.id)
                updated = True

            query = 'UPDATE ticket_system_messages SET '
            params = []
            data_changed = False

            if _system_title != system_title:
                query += 'system_title = ?, '
                params.append(system_title)
                updated = True
                data_changed = True

            if system_message != system_text:
                query += 'system_message = ?, '
                params.append(system_text)
                updated = True
                data_changed = True

            if _button_text != button_text:
                query += 'button_text = ?, '
                params.append(button_text)
                updated = True
                data_changed = True

            if ticket_message != ticket_text:
                query += 'ticket_message = ?, '
                params.append(ticket_text)
                updated = True
                data_changed = True

            query = query.rstrip(', ') + ' WHERE guild_id = ?'
            params.append(interaction.guild.id)
            final_params = tuple(params)
            
            if updated:
                if data_changed:
                    await self.bot.db.execute(query, *final_params)

                await interaction.response.send_message(
                    f'Ticket system was successfully updated for {channel.mention if channel else interaction.channel.mention} channel. Make sure to resend the system message', 
                    ephemeral=True
                )
            else:
                await interaction.response.send_message('Nothing was changed', ephemeral=True)
        except:
            await interaction.response.send_message('Something unexpected happened', ephemeral=True)

    @ticket_system_group.command(name='delete', description='Delete a ticket system')
    async def delete_ticket_system(self, interaction: discord.Interaction): 
        exists = await self.bot.db.fetchone('SELECT id FROM ticket_systems WHERE guild_id = ?', interaction.guild.id)
        print(exists)
        query = 'DELETE FROM ticket_systems WHERE guild_id = ?'
        await self.bot.db.execute(query, interaction.guild.id)

        await self.bot.db.execute('DELETE FROM ticket_system_messages WHERE guild_id = ?', interaction.guild.id)

        await interaction.response.send_message('Ticket system in this server was successfully deleted.')

async def setup(bot: Brains):
    await bot.add_cog(Ticket(bot))