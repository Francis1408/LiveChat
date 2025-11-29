import threading
import time
import socketio
import requests
import sys
import os

# Ensure services are running before running this test!

AUTH_URL = "http://localhost:5000"
CHAT_URL = "http://localhost:5001"

def simulate_user(user_id):
    sio = socketio.Client()
    username = f"loaduser_{user_id}"
    password = "password123"
    email = f"{username}@example.com"

    session = requests.Session()

    # Register
    try:
        session.post(f"{AUTH_URL}/register", data={
            "username": username,
            "password": password,
            "email": email
        })
    except Exception as e:
        print(f"User {user_id}: Register failed (might exist) - {e}")

    # Login
    try:
        res = session.post(f"{AUTH_URL}/login", data={
            "username": username,
            "password": password
        }, allow_redirects=False)
        
        if 'sso?token=' not in res.headers.get('Location', ''):
            print(f"User {user_id}: Login failed")
            return

        sso_url = res.headers['Location']
        
        # SSO to Chat
        res = session.get(sso_url)
        
        # Create/Join Room (Hardcoded room for load test)
        room_code = "LOAD"
        # Try to create (ignore if exists)
        session.post(f"{CHAT_URL}/", data={"create": "true"}) 
        # Actually we need to capture the code if we create it.
        # Simplification: User 1 creates, others join.
        
        if user_id == 0:
            # Create room
            res = session.post(f"{CHAT_URL}/", data={"create": "true"})
            # We need to extract code or just define a fixed code in DB for testing.
            # For this test, let's just assume we join a room "ABCD" if we can't easily extract.
            # Or better, let's just use the 'room' session variable if the server sets it.
            # But `requests` session cookie jar handles it.
        else:
            # Join room (assuming User 0 created one or we use a known one)
            # This is tricky without coordination.
            pass

        # SocketIO Connection
        # We need to pass the session cookie to SocketIO
        # python-socketio client doesn't easily share requests session cookies unless we extract them.
        
        cookies = session.cookies.get_dict()
        # Convert to format expected by socketio if needed, or just pass as headers?
        # SocketIO client usually takes headers.
        
        # Actually, Flask-SocketIO uses the Flask session which is signed in the cookie.
        # We just need to pass the 'session' cookie.
        
        headers = {}
        # sio.connect(CHAT_URL, headers=headers, namespaces=['/'])
        # But we need the cookie.
        # sio.connect(CHAT_URL, headers={'Cookie': f"session={cookies.get('session')}"})
        
        # Note: This might be flaky if the server expects specific cookie format.
        
        print(f"User {user_id}: Ready to connect socket")
        
    except Exception as e:
        print(f"User {user_id}: Error - {e}")

threads = []
for i in range(10):
    t = threading.Thread(target=simulate_user, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Load test finished")
