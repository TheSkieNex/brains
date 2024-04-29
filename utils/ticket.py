import random

import discord 

from discord import ui
from datetime import datetime

from .bot import Qolga


async def setup_ticket_system(bot: Qolga, interaction: discord.Interaction):
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
    
    view = ui.View()
    close_button = ui.Button(label='დახურვა', style=discord.ButtonStyle.secondary, emoji='🔒')

    async def close_button_callback(inter: discord.Interaction):
        confirm_close = ui.Button(label='დახურვა', style=discord.ButtonStyle.danger)
        cancel_close = ui.Button(label='შეწყვეტა', style=discord.ButtonStyle.secondary)

        async def _confirm_close_callback(i: discord.Interaction):
            await confirm_close_callback(bot, i, interaction)

        async def cancel_close_callback(i: discord.Interaction):
            await i.message.delete()

        confirm_close.callback = _confirm_close_callback
        cancel_close.callback = cancel_close_callback

        inner_view = ui.View()
        inner_view.add_item(confirm_close)
        inner_view.add_item(cancel_close)
        
        user_permissions = inter.channel.permissions_for(interaction.user)
        if user_permissions.view_channel:
            await inter.response.send_message('დარწმუნებული ხარ, რომ თიქეთის დახურვა გინდა?', view=inner_view)
        else:
            await inter.channel.set_permissions(interaction.user, view_channel=False)
            await inter.response.send_message(content='თიქეთი უკვე დახურულია!', ephemeral=True)

    close_button.callback = close_button_callback
    view.add_item(close_button)

    await ticket_channel.send(embed=welcome_embed, view=view)
    await interaction.response.send_message(f'თიქეთი შეიქმნა {ticket_channel.mention}', ephemeral=True)

async def confirm_close_callback(bot: Qolga, inter: discord.Interaction, interaction: discord.Interaction):
    main_embed = discord.Embed(color=bot.config.second_color)
    main_embed.description = f'თიქეთი დაიხურა {inter.user.mention}-ს მიერ'

    await inter.channel.set_permissions(interaction.user, view_channel=False)

    reopen_button = ui.Button(label='გახსნა', style=discord.ButtonStyle.secondary)
    delete_button = ui.Button(label='წაშლა', style=discord.ButtonStyle.danger)

    async def reopen_button_callback(i: discord.Interaction):
        embed = discord.Embed(color=bot.config.main_color)
        embed.description = f'თიქეთი გაიხსნა {i.user.mention}-ს მიერ'

        await i.channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_message_history=True)

        await i.message.edit(embed=main_embed, view=None)
        await i.response.defer()
        await i.channel.send(embed=embed)

    async def delete_button_callback(i: discord.Interaction):
        await i.channel.delete()

    reopen_button.callback = reopen_button_callback
    delete_button.callback = delete_button_callback

    view = ui.View()
    view.add_item(reopen_button)
    view.add_item(delete_button)

    await inter.message.delete()
    await inter.response.defer()
    await inter.channel.send(embed=main_embed, view=view)