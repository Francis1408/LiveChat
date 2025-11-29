from flask import Flask, render_template, request, flash, url_for, session, redirect
from flask_socketio import join_room, leave_room, send, SocketIO
import psycopg2.extras
from string import ascii_uppercase
import random
import os
try:
    from common import get_db_connection, decode_token
except ImportError:
    from services.common import get_db_connection, decode_token

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.getenv("FLASK_SECRET", "secret")
socketio = SocketIO(app)

AUTH_SERVICE_URL = "http://127.0.0.1:5000"

def generate_unique_code(length, cursor):
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

@app.route('/sso', methods=['GET'])
def sso():
    token = request.args.get('token')
    if not token:
        return redirect(AUTH_SERVICE_URL)
    
    payload = decode_token(token)
    if payload:
        session['loggedin'] = True
        session['id'] = payload['user_id']
        session['username'] = payload['username']
        return redirect(url_for('home'))
    else:
        return redirect(AUTH_SERVICE_URL)

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'loggedin' not in session:
        return redirect(AUTH_SERVICE_URL)
    
    # Clear room session when in menu
    session.pop('room', None)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == "POST":
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if create != False:
            code = generate_unique_code(4, cursor)
            user_id = session["id"]
            cursor.execute("INSERT INTO room (code, owner_id) VALUES (%s, %s)", (code, user_id))
            conn.commit()
            session['room'] = code
            flash('You have sucessfully created a room!')
            conn.close()
            return redirect(url_for("room"))

        if join != False:
            if not code:
                flash('Please enter a room code')
                conn.close()
                return render_template('home.html', username=session['username'], code=code)

            cursor.execute('SELECT * FROM room WHERE code = %s', (code,))
            room = cursor.fetchone()

            if not room:
                flash("Room does not exist")
                conn.close()
                return render_template('home.html', username=session['username'], code=code)

            session['room'] = code
            conn.close()
            return redirect(url_for("room"))

    conn.close()
    return render_template('home.html', username=session['username'])

@app.route("/room")
def room():
    if 'loggedin' not in session:
        return redirect(AUTH_SERVICE_URL)
        
    room_code = session.get("room")
    if room_code is None:
        return redirect(url_for("home"))
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute('SELECT * FROM room WHERE code = %s', (room_code,))
    room = cursor.fetchone()

    if not room:
        conn.close()
        return redirect(url_for("home"))
    
    room_id = room['id']
    
    cursor.execute("""
        SELECT users.username, messages.content
        FROM messages
        JOIN users ON messages.user_id = users.id
        WHERE messages.room_id = %s
        ORDER BY messages.id ASC
    """, (room_id,))
    
    messages = cursor.fetchall()
    
    formatted_messages = [
        {"name": msg["username"], "message": msg["content"]}
        for msg in messages
    ]
    
    conn.close()
    return render_template("room.html", code=room_code, messages=formatted_messages)

@socketio.on("message")
def message(data):
    room_code = session.get("room")
    user_id = session.get("id")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute('SELECT * FROM room WHERE code = %s', (room_code,))
    room = cursor.fetchone()

    if not room:
        conn.close()
        return
    
    room_id = room['id']
    
    content = {
        "name": session.get("username"),
        "message": data["data"]
    }
    send(content, to=room_code)

    cursor.execute("INSERT INTO messages (room_id, user_id, content) VALUES (%s, %s, %s)", (room_id, user_id, data["data"]))
    conn.commit()
    conn.close()
    print(f"{session.get('username')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room_code = session.get("room")
    username = session.get("username")
    user_id = session.get("id")

    if not room_code or not username:
        return
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute('SELECT * FROM room WHERE code = %s', (room_code,))
    room = cursor.fetchone()

    if not room:
        leave_room(room_code)
        conn.close()
        return
    
    room_id = room['id']
    
    join_room(room_code)
    send({"name": username, "message": "has entered the room"}, to=room_code)
    
    cursor.execute("SELECT * FROM room_members WHERE room_id = %s AND user_id = %s", (room_id, user_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO room_members (room_id, user_id) VALUES (%s, %s)", (room_id, user_id))
        conn.commit()
        
    conn.close()
    print(f"{username} joined room {room_code}")

@socketio.on("disconnect")
def disconnect():
    room_code = session.get("room")
    username = session.get("username")
    user_id = session.get("id")

    if not room_code or not username:
        return
 
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute('SELECT * FROM room WHERE code = %s', (room_code,))
    room = cursor.fetchone()

    if not room:
        conn.close()
        return
    
    room_id = room['id']

    send({"name": username, "message": "has left the room"}, to=room_code)

    cursor.execute('DELETE FROM room_members WHERE room_id = %s AND user_id = %s', (room_id, user_id))
    conn.commit()
    
    cursor.execute('SELECT * FROM room_members WHERE room_id = %s', (room_id,))
    members = cursor.fetchall()

    if len(members) == 0:
        cursor.execute('DELETE FROM room WHERE id = %s', (room_id,))
        conn.commit()
        print(f"Room {room_code} deleted")

    leave_room(room_code)
    conn.close()
    print(f"{username} left room {room_code}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(f"{AUTH_SERVICE_URL}/logout")

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
