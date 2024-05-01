import os
import logging

import discord

from discord.ext import commands

from utils.config import Config


log = logging.getLogger(__name__)

extensions = (
    'extensions.events',
    'extensions.moderation',
    'extensions.ticket',
)

class Qolga(commands.Bot):
    def __init__(self):
        self.dev = os.getenv('DEV_STATE')
        self.config = Config(self.dev)
        super().__init__(
            command_prefix='!',
            status=discord.Status.online,
            intents=discord.Intents.all(),
        )

    async def setup_hook(self) -> None:
        for extension in extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception('Failed to load extension %s.', extension)

        tree = await self.tree.sync()
        print(f'Synced {len(tree)} commands')
        print(f'{self.user.name} is running!')

    async def on_message(self, message):
        if message.author.bot:
            return
        
        await self.process_commands(message)