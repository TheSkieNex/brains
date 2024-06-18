import os
import sqlite3

DB_DIR = os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), 'database')

def db_setup(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    with open(os.path.join(DB_DIR, 'schema.sql'), 'r') as schema:
        content = schema.read()
        sql_commands = content.split(';')
        for sql_command in sql_commands:
            if sql_command.strip():
                cursor.executescript(sql_command)

        connection.commit()

        print(f'Executed {len(sql_commands) - 1} SQL commands')

def db_prepare():
    connection = sqlite3.connect(os.path.join(DB_DIR, 'database.db'))
    cursor = connection.cursor()

    db_setup(connection, cursor)
    
    connection.close()


if __name__ == '__main__':
    db_prepare()