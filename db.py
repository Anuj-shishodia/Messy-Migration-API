
import sqlite3
from flask import g # Keep g for app context usage
import os
from werkzeug.security import generate_password_hash # Import for initial hashed passwords

DATABASE = 'users.db'

def get_db():
    """
    Establishes a database connection for the current request context.
    If a connection does not exist, it creates one and stores it in Flask's 'g' object.
    This ensures that the same connection is used throughout a request lifecycle.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row # This makes rows behave like dictionaries
    return g.db

def close_db(e=None):
    """
    Closes the database connection at the end of a request.
    This function is registered with Flask's teardown_appcontext.
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db_command(): # Renamed to avoid confusion with internal init_db function
    """
    Initializes the database schema and optionally populates it with sample data.
    This function is designed to be called from the Flask CLI or direct script execution.
    It will create a fresh connection, not use 'g'.
    """
    # Remove existing database file if present to start fresh
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Removed existing database: {DATABASE}")

    # Establish a direct connection for initialization, not relying on 'g'
    with sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        ''')
        conn.commit()

        # Check if table is empty, then insert sample data
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Hash passwords for initial sample data for consistency
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                           ('John Doe', 'john@example.com', generate_password_hash('password123')))
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                           ('Jane Smith', 'jane@example.com', generate_password_hash('secret456')))
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                           ('Bob Johnson', 'bob@example.com', generate_password_hash('qwerty789')))
            conn.commit()
            print("Database initialized with sample data (passwords hashed).")
        else:
            print("Database already contains data, skipping sample data insertion.")

def init_app(app):
    """
    Registers the close_db function with the Flask application context.
    Also, allows calling init_db_command from Flask CLI if needed.
    """
    app.teardown_appcontext(close_db)
    # If you wanted to expose 'flask init-db' command later, you'd add:
    # app.cli.add_command(init_db_command)

if __name__ == '__main__':
    # When db.py is run directly, call the initialization command
    print("Running db.py directly to initialize database.")
    init_db_command()