-- Run this in Supabase SQL Editor to RESET your database
-- WARNING: This will delete all existing data!

drop table if exists public.event_assignments;
drop table if exists public.availabilities;
drop table if exists public.events;
drop table if exists public.users;
drop table if exists public.companies;

-- Companies table
create table public.companies (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  logo_url text,
  registration_code text unique not null,
  owner_id uuid references public.users(id) on delete set null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Users table
create table public.users (
  id uuid default gen_random_uuid() primary key,
  username text unique not null,
  password text not null,
  role text default 'employee',
  company_id uuid references public.companies(id) on delete cascade,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Events table
create table public.events (
  id uuid default gen_random_uuid() primary key,
  company_id uuid not null references public.companies(id) on delete cascade,
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

-- Availabilities table
create table public.availabilities (
  id uuid default gen_random_uuid() primary key,
  company_id uuid not null references public.companies(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  "start" text,
  "end" text,
  note text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Shift Swaps table
create table public.shift_swaps (
  id uuid default gen_random_uuid() primary key,
  initiator_id uuid not null references public.users(id) on delete cascade,
  target_employee_id uuid not null references public.users(id) on delete cascade,
  initiator_shift_id uuid not null references public.events(id) on delete cascade,
  target_shift_id uuid not null references public.events(id) on delete cascade,
  reason text,
  status text default 'pending',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.companies enable row level security;
alter table public.users enable row level security;
alter table public.events enable row level security;
alter table public.event_assignments enable row level security;
alter table public.availabilities enable row level security;
alter table public.shift_swaps enable row level security;

-- Create policies (simplified for this demo - allow all access)
create policy "Allow all access to companies" on public.companies for all using (true);
create policy "Allow all access to users" on public.users for all using (true);
create policy "Allow all access to events" on public.events for all using (true);
create policy "Allow all access to event_assignments" on public.event_assignments for all using (true);
create policy "Allow all access to availabilities" on public.availabilities for all using (true);
create policy "Allow all access to shift_swaps" on public.shift_swaps for all using (true);
