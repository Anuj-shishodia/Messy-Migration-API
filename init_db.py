import os
from db import init_db_command, DATABASE # Corrected import name

# Optional: Remove existing database file to start fresh every time init_db.py is run
# This is useful during development to ensure a clean slate.
# Be careful with this line in a production environment!
if os.path.exists(DATABASE):
    os.remove(DATABASE)
    print(f"Removed existing database: {DATABASE}")

# Initialize the database using the function from our new db.py
init_db_command() # Corrected function call name

print("Database re-initialized and populated (if empty).")