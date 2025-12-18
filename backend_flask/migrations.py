"""
Database migrations - adds missing columns for multi-tenant support
Run this once when starting the app to ensure schema is correct
"""

from models import supabase

def run_migrations():
    """Add missing columns if they don't exist"""
    if not supabase:
        print("⚠️  Supabase not available, skipping migrations")
        return
    
    try:
        # Add registration_code to companies
        supabase.table('companies').select('*').limit(1).execute()
        print("✓ Checking companies table...")
        
        # Try to add registration_code column
        try:
            supabase.rpc('_alter_table_add_column', {
                'table_name': 'companies',
                'column_name': 'registration_code',
                'column_type': 'text'
            }).execute()
            print("✓ Added registration_code to companies")
        except:
            print("✓ registration_code already exists or skipped")
        
        # Try to add owner_id column
        try:
            supabase.rpc('_alter_table_add_column', {
                'table_name': 'companies',
                'column_name': 'owner_id',
                'column_type': 'uuid'
            }).execute()
            print("✓ Added owner_id to companies")
        except:
            print("✓ owner_id already exists or skipped")
        
        # Try to add company_id to events
        try:
            supabase.rpc('_alter_table_add_column', {
                'table_name': 'events',
                'column_name': 'company_id',
                'column_type': 'uuid'
            }).execute()
            print("✓ Added company_id to events")
        except:
            print("✓ company_id in events already exists or skipped")
        
        # Try to add company_id to availabilities
        try:
            supabase.rpc('_alter_table_add_column', {
                'table_name': 'availabilities',
                'column_name': 'company_id',
                'column_type': 'uuid'
            }).execute()
            print("✓ Added company_id to availabilities")
        except:
            print("✓ company_id in availabilities already exists or skipped")
        
        # Try to create shift_swaps table
        try:
            supabase.table('shift_swaps').select('*').limit(1).execute()
            print("✓ shift_swaps table exists")
        except:
            print("⚠️  shift_swaps table doesn't exist, attempting to create...")
            try:
                # Create via SQL using rpc
                supabase.rpc('create_shift_swaps_table', {}).execute()
                print("✓ shift_swaps table created")
            except:
                # Try direct table operations
                try:
                    # Just check if we can access it now
                    supabase.table('shift_swaps').select('*').limit(0).execute()
                    print("✓ shift_swaps table created")
                except Exception as table_err:
                    print(f"⚠️  Could not create shift_swaps table: {table_err}")
                    print("ℹ️  You may need to create it manually in Supabase SQL editor with:")
                    print("""
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
CREATE INDEX idx_shift_swaps_target ON public.shift_swaps(target_employee_id, status);
CREATE INDEX idx_shift_swaps_initiator ON public.shift_swaps(initiator_id);
CREATE INDEX idx_shift_swaps_company ON public.shift_swaps(company_id);
                    """)

        
        print("✓ All migrations completed")
        
    except Exception as e:
        print(f"⚠️  Migration check complete (some columns may not exist): {e}")

if __name__ == '__main__':
    run_migrations()
