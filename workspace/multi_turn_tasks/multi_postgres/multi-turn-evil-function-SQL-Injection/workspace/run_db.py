import sys
import subprocess
import os

# --- 1. AUTO-INSTALL DEPENDENCY ---
# If psycopg2 is missing, install it automatically without asking the Agent.
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("📦 Installing database driver (psycopg2-binary)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "--quiet"])
    import psycopg2
    from psycopg2 import sql

# --- 2. CONFIGURATION ---
# Based on your Docker Setup
DB_CONFIG = {
    "host": "172.17.0.1",   # Docker Host IP
    "port": "5432",
    "user": "postgres",
    "password": "password", # Validated from your docker inspect
    "dbname": "postgres"
}

def run_query(target):
    """
    target: Can be a raw SQL string OR a file path.
    """
    conn = None
    try:
        # Connect
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if input is a file path
        if os.path.isfile(target):
            print(f"📂 Reading SQL from file: {target}")
            with open(target, 'r') as f:
                query = f.read()
        else:
            # Assume it's a raw string
            query = target

        # Execute
        cur.execute(query)

        # Print Results (if any)
        if cur.description:
            rows = cur.fetchall()
            # Print Header
            col_names = [desc[0] for desc in cur.description]
            print(f"\n{' | '.join(col_names)}")
            print("-" * (len(' | '.join(col_names))))
            # Print Rows
            for row in rows:
                print(' | '.join(map(str, row)))
            print(f"\n({len(rows)} rows)")
        else:
            print("✅ Query executed successfully (No output).")

    except Exception as e:
        print(f"❌ Database Error: {e}")
        sys.exit(1)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_db.py <sql_string_or_file_path>")
        sys.exit(1)
    
    run_query(sys.argv[1])