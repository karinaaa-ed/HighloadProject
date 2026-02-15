SELECT 'CREATE DATABASE review2'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'review2')\gexec

\connect review2

CREATE TABLE IF NOT EXISTS films (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
