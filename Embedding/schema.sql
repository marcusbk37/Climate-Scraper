-- Run this SQL in your Supabase SQL editor to create the articles table
-- Database → SQL Editor → paste and run

create extension if not exists pgcrypto;

create table if not exists articles (
  id uuid primary key default gen_random_uuid(),
  url text not null unique,  -- Added unique constraint to prevent duplicates
  domain text,
  title text,
  authors jsonb,
  published_at timestamptz,
  text text not null,
  metadata jsonb,
  created_at timestamptz not null default now()
);

-- Indexes for common queries
create index if not exists idx_articles_domain on articles(domain);
create index if not exists idx_articles_published_at on articles(published_at);
create index if not exists idx_articles_created_at on articles(created_at); 