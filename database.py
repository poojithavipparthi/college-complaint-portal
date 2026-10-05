import sqlite3
import os
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'college_complaints.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Complaints Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            department TEXT NOT NULL,
            summary TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Submitted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()

    # Seed Admin User if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    admin = cursor.fetchone()
    if not admin:
        admin_pass = generate_password_hash('admin123')
        cursor.execute(
            'INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)',
            ('admin', admin_pass, 'System Administrator', 'admin')
        )
        conn.commit()
        print("Default admin user created: admin / admin123")

    conn.close()

def generate_complaint_id():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"CMP-{suffix}"

def create_user(username, password, full_name, role='student'):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)',
            (username, password_hash, full_name, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists."
    except Exception as e:
        conn.close()
        return False, str(e)

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def create_complaint(user_id, title, description, category, priority, department, summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate unique complaint ID
    while True:
        complaint_id = generate_complaint_id()
        cursor.execute('SELECT id FROM complaints WHERE complaint_id = ?', (complaint_id,))
        if not cursor.fetchone():
            break

    cursor.execute('''
        INSERT INTO complaints 
        (complaint_id, user_id, title, description, category, priority, department, summary, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Submitted')
    ''', (complaint_id, user_id, title, description, category, priority, department, summary))

    conn.commit()
    conn.close()
    return complaint_id

def get_user_complaints(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM complaints 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def get_all_complaints():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, u.full_name as student_name, u.username as student_username
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
    ''')
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def get_complaint_by_id(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, u.full_name as student_name, u.username as student_username
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE c.complaint_id = ?
    ''', (complaint_id,))
    complaint = cursor.fetchone()
    conn.close()
    return complaint

def update_complaint_status(complaint_id, new_status):
    valid_statuses = ['Submitted', 'In Progress', 'Resolved']
    if new_status not in valid_statuses:
        return False, "Invalid status value."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE complaints 
        SET status = ? 
        WHERE complaint_id = ?
    ''', (new_status, complaint_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0, "Status updated successfully."
