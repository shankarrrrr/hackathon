"""Quick database connection and status check"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_database():
    """Check database connection and table status"""
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(os.getenv('DATABASE_URL'), connect_timeout=5)
        cur = conn.cursor()
        
        print("✅ Connected!\n")
        
        # Check tables
        print("Checking tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\nChecking row counts...")
        for table in ['customers', 'transactions', 'payments', 'labels']:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count:,} rows")
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        # Check for locks
        print("\nChecking for locks...")
        cur.execute("""
            SELECT pid, usename, application_name, state, query
            FROM pg_stat_activity
            WHERE state != 'idle'
            AND pid != pg_backend_pid()
        """)
        locks = cur.fetchall()
        if locks:
            print(f"Found {len(locks)} active queries:")
            for lock in locks:
                print(f"  PID {lock[0]}: {lock[4][:100]}")
        else:
            print("  No active locks")
        
        cur.close()
        conn.close()
        print("\n✅ Database check complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database()
