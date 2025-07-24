
import sqlite3
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing
from db import get_db, init_app # Import our database functions

app = Flask(__name__)

# Register the init_app function from db.py to handle database closing
init_app(app)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the User Management System API"}), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email FROM users") # Don't return password in GET
    users = cursor.fetchall()
    # Convert list of Row objects to list of dictionaries for jsonify
    users_list = [dict(user) for user in users]
    return jsonify(users_list), 200

@app.route('/user/<int:user_id>', methods=['GET']) # Use int converter for user_id
def get_user(user_id):
    db = get_db()
    cursor = db.cursor()
    # Use parameterized query to prevent SQL Injection
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)) # Don't return password
    user = cursor.fetchone()

    if user:
        return jsonify(dict(user)), 200
    else:
        return jsonify({"message": "User not found"}), 404 # Use proper HTTP status code

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() # Use get_json() for JSON payloads
    if not data:
        return jsonify({"message": "Invalid JSON"}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # Basic input validation
    if not all([name, email, password]):
        return jsonify({"message": "Missing name, email, or password"}), 400

    # Hash the password before storing
    hashed_password = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    try:
        # Use parameterized query to prevent SQL Injection
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, hashed_password))
        db.commit()
        # Return the ID of the newly created user
        return jsonify({"message": "User created successfully!", "user_id": cursor.lastrowid}), 201 # 201 Created
    except sqlite3.IntegrityError:
        # This error occurs if email is not unique
        return jsonify({"message": "User with this email already exists"}), 409 # Conflict
    except Exception as e:
        # Log the error properly in a real app
        print(f"Error creating user: {e}")
        return jsonify({"message": "An internal server error occurred"}), 500 # Internal Server Error

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON"}), 400

    name = data.get('name')
    email = data.get('email')

    # Basic validation: ensure at least one field is provided for update
    if not (name or email):
        return jsonify({"message": "No data provided for update"}), 400

    db = get_db()
    cursor = db.cursor()
    update_fields = []
    update_values = []

    if name:
        update_fields.append("name = ?")
        update_values.append(name)
    if email:
        update_fields.append("email = ?")
        update_values.append(email)

    if not update_fields:
        return jsonify({"message": "No valid fields to update"}), 400

    update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    update_values.append(user_id) # Add user_id to the end for the WHERE clause

    try:
        cursor.execute(update_query, tuple(update_values))
        db.commit()

        if cursor.rowcount == 0:
            # Check if user exists before attempting update again
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if cursor.fetchone() is None:
                return jsonify({"message": "User not found"}), 404
            else:
                return jsonify({"message": "User found but no changes made (data was identical)"}), 200 # No actual change
        return jsonify({"message": "User updated successfully"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"message": "User with this email already exists"}), 409
    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({"message": "An internal server error occurred"}), 500

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = get_db()
    cursor = db.cursor()
    # Use parameterized query
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"message": "User deleted successfully"}), 200

@app.route('/search', methods=['GET'])
def search_users():
    name = request.args.get('name')

    if not name:
        return jsonify({"message": "Please provide a 'name' query parameter to search"}), 400

    db = get_db()
    cursor = db.cursor()
    # Use parameterized query with LIKE wildcard
    # Note: '%' must be part of the parameter, not the query string for security
    search_pattern = f"%{name}%"
    cursor.execute("SELECT id, name, email FROM users WHERE name LIKE ?", (search_pattern,))
    users = cursor.fetchall()

    users_list = [dict(user) for user in users]
    return jsonify(users_list), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON"}), 400

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "Missing email or password"}), 400

    db = get_db()
    cursor = db.cursor()
    # Use parameterized query
    cursor.execute("SELECT id, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    # If user exists, check hashed password
    if user and check_password_hash(user['password'], password):
        return jsonify({"status": "success", "user_id": user['id']}), 200
    else:
        return jsonify({"status": "failed", "message": "Invalid credentials"}), 401 # Unauthorized

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)