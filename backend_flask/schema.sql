-- Run this in Supabase SQL Editor to RESET your database
-- WARNING: This will delete all existing data!

drop table if exists public.availabilities;
drop table if exists public.events;
drop table if exists public.users;

-- Users table
create table public.users (
  id uuid default gen_random_uuid() primary key,
  username text unique not null,
  password text not null,
  role text default 'employee',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Events table
create table public.events (
  id uuid default gen_random_uuid() primary key,
  title text,
  description text,
  "start" text,
  "end" text,
  capacity int default 1,
  type text default 'general',
  location text,
  hours text,
  assigned jsonb default '[]'::jsonb,
  pending jsonb default '[]'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Availabilities table
create table public.availabilities (
  id uuid default gen_random_uuid() primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  "start" text,
  "end" text,
  note text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.users enable row level security;
alter table public.events enable row level security;
alter table public.availabilities enable row level security;

-- Create policies (simplified for this demo - allow all access)
create policy "Allow all access to users" on public.users for all using (true);
create policy "Allow all access to events" on public.events for all using (true);
create policy "Allow all access to availabilities" on public.availabilities for all using (true);
