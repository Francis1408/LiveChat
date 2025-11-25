from flask import Flask, render_template, request, flash
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secrect_key = ''
DB_HOST = ""
DB_NAME = ""
DB_USER = ""
DB_PASS = ""

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

@app.route('/register', methods=['GET','POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Confere se os campos de registro existem
    if request.method == 'POST' and 'register_username' in request.form and 'register_password' in request.form and 'register_email' in request.form:
        # Cria variáveis para acesso fácil
        username = request.form['register_username']
        password = request.form['register_password']
        email = request.form['register_email']
        
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

    return render_template('index.html')
    


if __name__ == "__main__":
    app.run(debug=True)