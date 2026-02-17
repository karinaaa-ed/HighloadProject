CREATE SCHEMA IF NOT EXISTS films;

CREATE TABLE IF NOT EXISTS films.request_films (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);