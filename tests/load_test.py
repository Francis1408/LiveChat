import threading
import time
import socketio
import requests
import re
import random

# Configuration
AUTH_URL = "http://127.0.0.1:5002"
CHAT_URL = "http://127.0.0.1:5003"
NUM_USERS = 10
MESSAGES_PER_USER = 5

# Global coordination
ROOM_CODE = None
START_EVENT = threading.Event()
ALL_THREADS_FINISHED = threading.Event()

def simulate_user(user_id):
    global ROOM_CODE
    
    # Initialize SocketIO Client
    sio = socketio.Client()
    username = f"loaduser_{user_id}"
    password = "password123"
    email = f"{username}@example.com"
    
    session = requests.Session()
    
    print(f"[{user_id}] Starting...")

    # 1. Register (ignore if already exists)
    try:
        session.post(f"{AUTH_URL}/register", data={
            "username": username,
            "password": password,
            "email": email,
            "fullname": f"Load User {user_id}"
        })
    except Exception:
        pass # User might already exist

    # 2. Login
    try:
        res = session.post(f"{AUTH_URL}/login", data={
            "username": username,
            "password": password
        }, allow_redirects=False)
        
        if 'sso?token=' not in res.headers.get('Location', ''):
            print(f"[{user_id}] Login failed. Status: {res.status_code}")
            print(f"[{user_id}] Headers: {res.headers}")
            # print(f"[{user_id}] Content: {res.text}")
            return

        sso_url = res.headers['Location']
        
        # 3. SSO to Chat Service (gets the session cookie for chat)
        # Clear cookies to avoid conflict between Auth and Chat service cookies on localhost
        session.cookies.clear()
        res = session.get(sso_url)
        
        # 4. Create or Join Room
        if user_id == 0:
            # User 0 creates the room
            print(f"[{user_id}] Creating room...")
            res = session.post(f"{CHAT_URL}/", data={"create": "true"})
            
            # Extract Room Code from HTML
            match = re.search(r'Room: <span.*?>(.*?)</span>', res.text)
            if match:
                ROOM_CODE = match.group(1)
                print(f"[{user_id}] Room created: {ROOM_CODE}")
                START_EVENT.set() # Signal other threads
            else:
                print(f"[{user_id}] Failed to extract room code")
                print(f"[{user_id}] Response URL: {res.url}")
                # print(f"[{user_id}] Response Text: {res.text}")
                return
        else:
            # Other users wait for room code
            print(f"[{user_id}] Waiting for room code...")
            START_EVENT.wait()
            
            # Join the room
            session.post(f"{CHAT_URL}/", data={"join": "true", "code": ROOM_CODE})
            # print(f"[{user_id}] Joined room {ROOM_CODE}")

        # 5. Connect via SocketIO
        # We must pass the 'session' cookie from the requests session
        chat_cookie = session.cookies.get('session')
        if not chat_cookie:
            print(f"[{user_id}] No session cookie found for Chat Service")
            return

        # Connect
        sio.connect(CHAT_URL, headers={'Cookie': f"session={chat_cookie}"})
        
        # Define events
        @sio.on('message')
        def on_message(data):
            # print(f"[{user_id}] Received: {data}")
            pass

        # 6. Send Messages
        for i in range(MESSAGES_PER_USER):
            msg = f"Hello from {username} ({i+1}/{MESSAGES_PER_USER})"
            sio.emit('message', {'data': msg})
            # print(f"[{user_id}] Sent: {msg}")
            time.sleep(random.uniform(0.1, 0.5))

        # Disconnect
        sio.disconnect()
        print(f"[{user_id}] Finished")

    except Exception as e:
        print(f"[{user_id}] Error: {e}")

if __name__ == "__main__":
    print(f"Starting load test with {NUM_USERS} users...")
    
    threads = []
    for i in range(NUM_USERS):
        t = threading.Thread(target=simulate_user, args=(i,))
        threads.append(t)
        t.start()
        # Stagger start slightly to avoid overwhelming auth service instantly
        time.sleep(0.1)

    for t in threads:
        t.join()

    print("Load test completed.")
