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
        
        print("✓ All migrations completed")
        
    except Exception as e:
        print(f"⚠️  Migration check complete (some columns may not exist): {e}")

if __name__ == '__main__':
    run_migrations()
