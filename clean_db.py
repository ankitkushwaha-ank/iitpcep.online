import sqlite3
import os

# Connect to your local database
db_path = "db.sqlite3"

if not os.path.exists(db_path):
    print(f"Error: Could not find {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Cleaning Database ---")

    # 1. Check for orphans in moodle_option
    # This deletes options where the question_id does not exist in the questions table
    cursor.execute("""
        DELETE FROM moodle_option 
        WHERE question_id NOT IN (SELECT id FROM moodle_question)
    """)

    deleted_count = cursor.rowcount
    print(f"Deleted {deleted_count} orphaned options (ghost answers).")

    # Commit and close
    conn.commit()
    conn.close()
    print("--- Cleanup Complete ---")