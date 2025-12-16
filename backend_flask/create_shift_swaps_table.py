#!/usr/bin/env python3
"""
Script to create the shift_swaps table in Supabase
Run this once to set up the database schema for shift swaps
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY environment variables are required")
    exit(1)

supabase = create_client(url, key)

# SQL to create the shift_swaps table
sql = """
CREATE TABLE IF NOT EXISTS public.shift_swaps (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp DEFAULT now(),
  initiator_id uuid REFERENCES public.users(id) ON DELETE CASCADE,
  target_employee_id uuid REFERENCES public.users(id) ON DELETE CASCADE,
  initiator_shift_id uuid REFERENCES public.events(id) ON DELETE CASCADE,
  target_shift_id uuid REFERENCES public.events(id) ON DELETE CASCADE,
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  reason text,
  company_id uuid REFERENCES public.companies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_shift_swaps_target ON public.shift_swaps(target_employee_id, status);
CREATE INDEX IF NOT EXISTS idx_shift_swaps_initiator ON public.shift_swaps(initiator_id);
CREATE INDEX IF NOT EXISTS idx_shift_swaps_company ON public.shift_swaps(company_id);
"""

try:
    # Execute raw SQL via RPC
    result = supabase.rpc('exec_sql', {'sql': sql}).execute()
    print("✓ shift_swaps table created successfully!")
except Exception as e:
    print(f"Note: Could not use RPC method (this is normal): {e}")
    print("\nPlease run this SQL manually in Supabase SQL Editor:")
    print("=" * 80)
    print(sql)
    print("=" * 80)
    print("\nSteps:")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Go to SQL Editor")
    print("4. Click 'New Query'")
    print("5. Paste the SQL above")
    print("6. Click 'Run'")
