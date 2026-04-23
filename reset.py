import sqlite3
import os

# Check the exact name of your database file inside your logger.py
# It is usually 'focus_data.db' or 'logs.db'. Change the name below if needed.
DB_NAME = "focus_data.db" 

if os.path.exists(DB_NAME):
    try:
        os.remove(DB_NAME)
        print(f"SUCCESS: {DB_NAME} completely deleted!")
    except Exception as e:
        print(f"ERROR: Cannot delete. Make sure FocusFlow is closed! ({e})")
else:
    print("Database not found. It is already clean.")