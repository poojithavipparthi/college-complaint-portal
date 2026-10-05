import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv

import database
import ai_service

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secret-college-complaint-key')

# Initialize SQLite database on startup
database.init_db()

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Unauthorized access.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not full_name or not username or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return render_template('register.html')

        success, result = database.create_user(username, password, full_name, role='student')
        if success:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {result}', 'error')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = database.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    user_id = session['user_id']
    complaints = database.get_user_complaints(user_id)
    return render_template('student_dashboard.html', complaints=complaints)

@app.route('/student/complaint/new', methods=['GET', 'POST'])
@login_required(role='student')
def new_complaint():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not description:
            flash('Title and Description are required.', 'error')
            return render_template('new_complaint.html')

        category = request.form.get('category', '').strip()
        priority = request.form.get('priority', '').strip()
        department = request.form.get('department', '').strip()
        summary = request.form.get('summary', '').strip()

        # If user submitted without clicking "Analyze with AI" preview, run Gemini AI analysis now
        if not category or not priority or not department or not summary:
            ai_res = ai_service.analyze_complaint_with_gemini(title, description)
            category = ai_res.get('category', 'Other')
            priority = ai_res.get('priority', 'Medium')
            department = ai_res.get('department', 'General')
            summary = ai_res.get('summary', title)

        complaint_id = database.create_complaint(
            user_id=session['user_id'],
            title=title,
            description=description,
            category=category,
            priority=priority,
            department=department,
            summary=summary
        )

        flash(f'Complaint submitted successfully! Your Ticket ID: {complaint_id}', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('new_complaint.html')

@app.route('/api/analyze', methods=['POST'])
@login_required()
def api_analyze():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()

    if not title or not description:
        return jsonify({'success': False, 'error': 'Title and description are required.'}), 400

    analysis = ai_service.analyze_complaint_with_gemini(title, description)
    return jsonify({'success': True, 'analysis': analysis})

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    complaints = database.get_all_complaints()
    return render_template('admin_dashboard.html', complaints=complaints)

@app.route('/admin/complaint/<complaint_id>/status', methods=['POST'])
@login_required(role='admin')
def update_status(complaint_id):
    new_status = request.form.get('status', '').strip()
    success, msg = database.update_complaint_status(complaint_id, new_status)
    if success:
        flash(f'Status for {complaint_id} updated to "{new_status}".', 'success')
    else:
        flash(f'Failed to update status: {msg}', 'error')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    print("Starting AI-Powered College Complaint Classifier on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
