from flask import Flask, render_template, request, flash, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2.extras
import re
import os
try:
    from common import get_db_connection, generate_token
except ImportError:
    from services.common import get_db_connection, generate_token

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.getenv("FLASK_SECRET", "secret")

CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://127.0.0.1:5001")

@app.route('/', methods=['GET'])
def home():
    if 'loggedin' in session:
        # If already logged in, generate token and redirect to chat
        token = generate_token(session['id'], session['username'])
        return redirect(f"{CHAT_SERVICE_URL}/sso?token={token}")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if registration fields exist
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'fullname' in request.form:
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        _hashed_password = generate_password_hash(password)

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)

        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email or not fullname:
            flash('Please fill out the form!')
        else:
            cursor.execute("INSERT INTO users (fullname, username, password, email) VALUES (%s, %s, %s, %s)", (fullname, username, _hashed_password, email))
            conn.commit()
            flash('You have sucessfully registered!')
            return redirect(url_for('login'))
    
    elif request.method == 'POST':
        flash('Please fill out the form!')

    conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            password_rs = account['password']
            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                
                # Redirect to Chat Service with Token
                token = generate_token(account['id'], account['username'])
                return redirect(f"{CHAT_SERVICE_URL}/sso?token={token}")
            else:
                flash("Incorrect username/password")
        else:
            flash("Incorrect username/password")
    
    conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, port=port)
