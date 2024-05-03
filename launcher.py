import os
import asyncio
import aiosqlite

from dotenv import load_dotenv

from utils.bot import Qolga, BotDB

load_dotenv()

DEV = os.getenv('DEV_STATE')
token = os.getenv('TEST_BOT_TOKEN') if DEV else os.getenv('BOT_TOKEN')

async def run_sql_commands(db: aiosqlite.Cursor, db_conn: aiosqlite.Connection):
    with open('database/schema.sql', 'r') as schema:
        content = schema.read()
        sql_commands = content.split(';')
        for sql_command in sql_commands:
            if sql_command.strip():
                await db.execute(sql_command)
        await db_conn.commit()
        print(f'{len(sql_commands)-1} SQL commands were executed')

async def run_bot():
    async with aiosqlite.connect('database/database.db') as db_connection:
        async with Qolga() as bot:
            cursor = await db_connection.cursor()
            await run_sql_commands(cursor, db_connection)

            bot.dev = DEV
            bot.db = BotDB(cursor, db_connection)

            bot.remove_command('help')
            await bot.start(token)
    
def main():
    asyncio.run(run_bot())


if __name__ == '__main__':
    main()