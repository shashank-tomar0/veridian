import sqlite3
import os

db_path = './veridian.db'
print(f"Opening database at {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the column exists first
    cursor.execute("PRAGMA table_info(analysis_results)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'result_json' not in columns:
        print("Adding 'result_json' column to 'analysis_results' table...")
        cursor.execute('ALTER TABLE analysis_results ADD COLUMN result_json TEXT')
        conn.commit()
        print("Migration successful.")
    else:
        print("'result_json' column already exists.")

    # Also check 'media_hash' since it was referenced in the code
    if 'media_hash' not in columns:
        print("Adding 'media_hash' column...")
        cursor.execute('ALTER TABLE analysis_results ADD COLUMN media_hash TEXT')
        conn.commit()

except Exception as e:
    print(f"Error during migration: {e}")
finally:
    conn.close()
