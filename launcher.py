import os
import asyncio
import aiosqlite

from dotenv import load_dotenv

from utils.bot import Qolga

load_dotenv()

DEV = os.getenv('DEV_STATE')
token = os.getenv('TEST_BOT_TOKEN') if DEV else os.getenv('BOT_TOKEN')

async def run_bot():
    async with aiosqlite.connect('database/database.db') as db_connection:
        async with Qolga() as bot:
            bot.dev = DEV
            bot.db = await db_connection.cursor()
            bot.db_conn = db_connection
            
            # bot.remove_command('help')
            await bot.start(token)
    
def main():
    asyncio.run(run_bot())


if __name__ == '__main__':
    main()