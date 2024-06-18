CREATE TABLE IF NOT EXISTS tags (
    name TEXT NOT NULL PRIMARY KEY,
    content TEXT,
    guild_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_interactions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cap_transfer_usage (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_systems (
    id INTEGER NOT NULL PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    category_id INTEGER,
    guild_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_system_messages (
    id INTEGER NOT NULL PRIMARY KEY,
    system_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    system_title VARCHAR(64) NOT NULL,
    system_message VARCHAR(1200) NOT NULL,
    button_text VARCHAR(64) NOT NULL,
    ticket_message VARCHAR(1200) NOT NULL,
    FOREIGN KEY (system_id) REFERENCES ticket_systems(id),
    FOREIGN KEY (guild_id) REFERENCES ticket_systems(guild_id)
);