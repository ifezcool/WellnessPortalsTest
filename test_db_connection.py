# test_db_connection.py
"""
Standalone script to test SQL Server connection via SQLAlchemy + pyodbc
Helps diagnose: wrong database, wrong schema, table not found, etc.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ────────────────────────────────────────────────
#  Load your secrets (same as in your main app)
# ────────────────────────────────────────────────
load_dotenv('secrets.env')           # adjust path if needed

server   = os.environ.get('server_name')
database = os.environ.get('db_name')
username = os.environ.get('db_username')
password = os.environ.get('db_password')

# Optional: if you're using a full connection string instead
# conn_str = os.environ.get('conn_str')

# ────────────────────────────────────────────────
#  Build connection string
# ────────────────────────────────────────────────
if not all([server, database, username, password]):
    print("ERROR: Missing one or more environment variables (server_name, db_name, db_username, db_password)")
    exit(1)

connection_url = (
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&TrustServerCertificate=yes"
    "&encrypt=yes"
)

# If you prefer using the full conn_str from env instead, uncomment this:
# connection_url = conn_str

engine = create_engine(
    connection_url,
    connect_args={
        'TrustServerCertificate': 'yes'
    }
)

# ────────────────────────────────────────────────
#  Helper functions
# ────────────────────────────────────────────────

def run_query(query, fetch_all=True, scalar=False):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if scalar:
                return result.scalar()
            elif fetch_all:
                return result.fetchall()
            else:
                return result.fetchone()
    except Exception as e:
        print(f"Query failed: {query}")
        print(f"Error: {e}")
        return None


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


# ────────────────────────────────────────────────
#  Tests
# ────────────────────────────────────────────────

print_section("1. Basic connection test & current database")

current_db = run_query("SELECT DB_NAME()", scalar=True)
current_user = run_query("SELECT SYSTEM_USER", scalar=True)
current_login = run_query("SELECT ORIGINAL_LOGIN()", scalar=True)

print(f"Connected to database : {current_db}")
print(f"Connected as user     : {current_user}")
print(f"Original login        : {current_login}")

print_section("2. List all databases (to see if you're in the right one)")

dbs = run_query("""
    SELECT name 
    FROM sys.databases 
    WHERE name NOT IN ('master','model','msdb','tempdb')
    ORDER BY name
""")

if dbs:
    print("Available user databases:")
    for row in dbs:
        print(f"  - {row[0]}")
else:
    print("Could not list databases (permissions?)")

print_section("3. Try to find the users table in different schemas")

possible_schemas = ['dbo', 'portal', 'wellness', 'auth', 'security', 'staging']

target_table = 'tbl_provider_wellness_submission_portal_users'

found = False

for schema in possible_schemas:
    print(f"  Checking {schema}.{target_table} ... ", end="")
    try:
        count = run_query(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{schema}' 
              AND TABLE_NAME = '{target_table}'
        """, scalar=True)
        
        if count and count > 0:
            print("FOUND!")
            found = True
            print(f"\nSUCCESS → table exists as: {schema}.{target_table}\n")
            
            # Bonus: show first few rows (careful with passwords!)
            print("First 3 rows (limited columns):")
            sample = run_query(f"""
                SELECT TOP 3 code, providername 
                FROM {schema}.{target_table}
            """)
            if sample:
                for row in sample:
                    print(f"  {row}")
            else:
                print("  (no rows or permission issue)")
            break
        else:
            print("not found")
    except Exception as e:
        print(f"error: {str(e)[:80]}...")

if not found:
    print("\nTable not found in common schemas.")
    print("Trying broader search for similar table names...\n")

    similar = run_query("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%provider%'
           OR TABLE_NAME LIKE '%wellness%'
           OR TABLE_NAME LIKE '%portal%'
           OR TABLE_NAME LIKE '%users%'
           OR TABLE_NAME LIKE '%submission%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)

    if similar:
        print("Tables that might be related:")
        for sch, tbl in similar:
            print(f"  {sch}.{tbl}")
    else:
        print("No similar tables found (or no permission to INFORMATION_SCHEMA)")

print_section("Done")

print("\nNext steps:")
print("1. If you found the table → update your main app to use correct schema:")
print("   FROM dbo.tbl_provider_wellness_submission_portal_users   (or whatever schema it is)")
print("2. If wrong database → change 'db_name' in secrets.env")
print("3. If still not found → ask DBA / check SSMS with same credentials")