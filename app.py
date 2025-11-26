from flask import Flask, render_template, request, flash, url_for, session, redirect
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("FLASK_SECRET")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)


@app.route('/')
def home():
    # Confere se a sessão está ativa
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    
    return redirect(url_for('login'))

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

    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)