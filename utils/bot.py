import os
import logging
import aiosqlite

import discord

from discord.ext import commands

from utils.config import Config


log = logging.getLogger(__name__)

extensions = (
    'extensions.events',
    'extensions.moderation',
    'extensions.ticket',
    'extensions.information',
    'extensions.tag',
    'extensions.general',
    'extensions.list',
)

class BotDB:
    def __init__(self, db: aiosqlite.Cursor, db_conn: aiosqlite.Connection):
        self.db = db
        self.db_conn = db_conn

    async def execute(self, query: str, *parameters, commit: bool = True):
        exc = await self.db.execute(query, parameters if parameters else ())
        if commit:
            await self.db_conn.commit()
            return exc
    
    async def commit(self):
        await self.db_conn.commit()

    async def fetchone(self, query: str, *parameters):
        await self.db.execute(query, parameters if parameters else ())
        return await self.db.fetchone()

    async def fetchall(self, query: str, *parameters):
        await self.db.execute(query, parameters if parameters else ())
        return await self.db.fetchall()    


class Brains(commands.Bot):
    db: BotDB
    def __init__(self):
        self.dev = os.getenv('DEV_STATE')
        self.config = Config(self.dev)
        super().__init__(
            command_prefix='?',
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