from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import re

app = Flask(__name__)
CORS(app)  # Allow requests from frontend
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change this in production!
jwt = JWTManager(app)

DB_PATH = 'voicecare_reminders.db'

def get_user(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(email, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400
    if get_user(email):
        return jsonify({'success': False, 'message': 'Email already registered'}), 409
    user_id = create_user(email, password)
    if user_id:
        access_token = create_access_token(identity=email, expires_delta=datetime.timedelta(days=1))
        return jsonify({'success': True, 'user': {'id': user_id, 'email': email}, 'token': access_token})
    return jsonify({'success': False, 'message': 'Signup failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = get_user(email)
    if user and user[2] == password:
        access_token = create_access_token(identity=email, expires_delta=datetime.timedelta(days=1))
        return jsonify({'success': True, 'user': {'id': user[0], 'email': user[1]}, 'token': access_token})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/reminders', methods=['GET'])
@jwt_required()
def get_reminders():
    email = get_jwt_identity()
    user = get_user(email)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    user_id = user[0]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task, time, date FROM reminders WHERE user_id = ? ORDER BY date, time", (user_id,))
    reminders = [
        {'id': row[0], 'task': row[1], 'time': row[2], 'date': row[3]} for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify({'success': True, 'reminders': reminders})

@app.route('/api/reminders', methods=['POST'])
@jwt_required()
def add_reminder():
    email = get_jwt_identity()
    user = get_user(email)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    user_id = user[0]
    data = request.json
    task = data.get('task')
    time = data.get('time')
    date = data.get('date')
    if not task or not time or not date:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (task, time, date, user_id) VALUES (?, ?, ?, ?)", (task, time, date, user_id))
    conn.commit()
    reminder_id = cursor.lastrowid
    conn.close()
    return jsonify({'success': True, 'reminder': {'id': reminder_id, 'task': task, 'time': time, 'date': date}})

@app.route('/api/voice-command', methods=['POST'])
@jwt_required()
def process_voice_command():
    email = get_jwt_identity()
    user = get_user(email)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    data = request.json
    command = data.get('command', '').lower()
    
    if 'remind' in command or 'reminder' in command:
        # Simple parsing - in production, use the sophisticated parsing from voicecare_assistant.py
        if 'at' in command and ('today' in command or 'tomorrow' in command):
            # Extract basic reminder info
            parts = command.split('at')
            if len(parts) >= 2:
                task = parts[0].replace('remind me to', '').replace('reminder', '').strip()
                time_part = parts[1].strip()
                
                # Extract time
                time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)', time_part)
                if time_match:
                    time = time_match.group(1)
                    # Determine date
                    if 'tomorrow' in command:
                        from datetime import datetime, timedelta
                        date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    else:
                        from datetime import datetime
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Save reminder
                    user_id = user[0]
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO reminders (task, time, date, user_id) VALUES (?, ?, ?, ?)", (task, time, date, user_id))
                    conn.commit()
                    reminder_id = cursor.lastrowid
                    conn.close()
                    
                    return jsonify({
                        'success': True, 
                        'message': f'Reminder set: {task} at {time} on {date}',
                        'reminder': {'id': reminder_id, 'task': task, 'time': time, 'date': date}
                    })
    
    return jsonify({'success': False, 'message': 'Could not understand the command'})

if __name__ == '__main__':
    # Ensure users and reminders tables exist for demo
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            time TEXT NOT NULL,
            date TEXT NOT NULL,
            user_id INTEGER,
            recurring BOOLEAN DEFAULT FALSE,
            remaining_days INTEGER DEFAULT 0,
            original_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Insert a test user if not exists
    cursor.execute("SELECT * FROM users WHERE email = 'test@example.com'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ('test@example.com', 'password123'))
    conn.commit()
    conn.close()
    app.run(port=5000, debug=True)
