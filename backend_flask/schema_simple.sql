-- Simple, single-company schema (no multi-tenant)
-- Run this in Supabase SQL Editor to RESET your database
-- WARNING: This will delete all existing data!

drop table if exists public.event_assignments;
drop table if exists public.availabilities;
drop table if exists public.events;
drop table if exists public.users;

-- Users table (simple, no company_id)
create table public.users (
  id uuid default gen_random_uuid() primary key,
  username text unique not null,
  password text not null,
  role text default 'employee',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Events table (simple, no company_id)
create table public.events (
  id uuid default gen_random_uuid() primary key,
  title text,
  description text,
  "start" text,
  "end" text,
  capacity int default 1,
  type text default 'general',
  location text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Event Assignments table (normalized instead of JSONB)
create table public.event_assignments (
  id uuid default gen_random_uuid() primary key,
  event_id uuid not null references public.events(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  status text default 'pending',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(event_id, user_id)
);

-- Availabilities table (simple, no company_id)
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
alter table public.event_assignments enable row level security;
alter table public.availabilities enable row level security;

-- Create policies (allow all access)
create policy "Allow all access to users" on public.users for all using (true);
create policy "Allow all access to events" on public.events for all using (true);
create policy "Allow all access to event_assignments" on public.event_assignments for all using (true);
create policy "Allow all access to availabilities" on public.availabilities for all using (true);
