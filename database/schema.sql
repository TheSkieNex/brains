CREATE TABLE IF NOT EXISTS tags (
    name TEXT NOT NULL PRIMARY KEY,
    content TEXT
);

CREATE TABLE IF NOT EXISTS ticket_interactions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL
);