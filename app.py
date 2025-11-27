from flask import Flask, render_template, request, flash, url_for, session, redirect
from flask_socketio import join_room, leave_room, send, SocketIO
from dotenv import load_dotenv
from string import ascii_uppercase
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("FLASK_SECRET")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

# Cria um código único para a sala
def generate_unique_code(length, cursor):

    # Pega os códigos das salas existentes
    cursor.execute("SELECT code FROM room")
    rooms = cursor.fetchall()
    codes = [r[0] for r in rooms]

    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in codes:
            break
    
    return code


@app.route('/', methods=['GET','POST'])
def home():
    # Confere se a sessão está ativa
    if not'loggedin' in session:
        return redirect(url_for('login'))
    
    # Sempre limpa a cache da sala quando re-entra na home
    session.pop('room', None)

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == "POST":
        username = session['username']
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        # CREATE
        if create != False:
            code = generate_unique_code(4, cursor)
            user_id = session["id"]
            cursor.execute("INSERT INTO room (code, owner_id) VALUES (%s, %s)", (code, user_id))
            conn.commit()

            session['room'] = code
            flash('You have sucessfully created a room!')
            return redirect(url_for("room"))

        # JOIN
        if join != False:

            if not code:
                flash('Please enter a room code')
                return render_template('home.html', username=session['username'], code=code)

            cursor.execute('SELECT * FROM room WHERE code = %s', (code,))
            room = cursor.fetchone()

            if not room:
                flash("Room does not exist")
                return render_template('home.html', username=session['username'], code=code)

            session['room'] = code
            return redirect(url_for("room"))

    return render_template('home.html', username=session['username'])


@app.route('/register', methods=['GET','POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Confere se os campos de registro existem
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Cria variáveis para acesso fácil
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Transforma a senha em hash
        _hashed_password = generate_password_hash(password)

        # Confere se a conta existe no MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)

        # Erros de validação caso a conta exista
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            # A conta não existe. segue as regras e pode ser criada
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, _hashed_password, email))
            conn.commit()
            flash('You have sucessfully registered!')
    
    # Se o formulário possui dados faltantes
    elif request.method == 'POST':
        flash('Please fill out the form!')

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Cria variáveis para acesso fácil
        username = request.form['username']
        password = request.form['password']

        # Confere se conta existe no DB
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

       
        if account:
            password_rs = account['password']
            # Cofere a validade da senha
            if check_password_hash(password_rs, password):
                # Cria session data
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redireciona para a homepage
                return redirect(url_for('home'))

            else:
                flash("Incorrect username/password")

        else:
            flash("Incorrect username/password")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove a session data
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('room', None)

    return redirect(url_for('login'))

@app.route("/room")
def room():
    # Garante que a sessão está ativa
    if not'loggedin' in session or session.get("room") is None:
        return redirect(url_for("home"))

    return render_template("room.html")

if __name__ == "__main__":
    app.run(debug=True)