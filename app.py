from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/register', methods=['GET','POST'])
def register():
    # Confere se os campos de registro existem
    if request.method == 'POST' and 'register_username' in request.form and 'register_password' in request.form and 'register_email' in request.form:
        # Cria variáveis para acesso fácil
        username = request.form['register_username']
        password = request.form['register_password']
        email = request.form['register_email']
        print(f'{username} | {password} | {email}')
    
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)