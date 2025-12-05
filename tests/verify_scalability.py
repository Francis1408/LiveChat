import socketio
import requests
import time
import sys
import threading

# Nginx Entry Point
BASE_URL = "http://127.0.0.1:8080"
AUTH_URL = "http://127.0.0.1:5002"

# Global state
messages_received = []
update_event = threading.Event()

def get_session(username):
    print(f"Getting session for {username}...")
    session = requests.Session()
    try:
        session.post(f"{AUTH_URL}/register", data={"username": username, "password": "password", "email": f"{username}@example.com", "fullname": username})
    except:
        pass
    
    print(f"Logging in {username}...")
    res = session.post(f"{AUTH_URL}/login", data={"username": username, "password": "password"}, allow_redirects=False)
    if res.status_code != 302:
        print(f"Login failed for {username}: {res.status_code}")
        sys.exit(1)
        
    sso_url = res.headers['Location']
    # IMPORTANT: The SSO URL from Auth Service points to CHAT_SERVICE_URL env var.
    # If Auth Service thinks Chat is at 8080, it redirects to 8080.
    # We need to follow that redirect to get the session cookie for Nginx.
    
    print(f"SSO redirect to {sso_url}...")
    session.cookies.clear()
    res = session.get(sso_url, allow_redirects=False)
    
    # If Nginx redirects again (e.g. to /), follow it
    if res.status_code == 302:
        location = res.headers['Location']
        if location.startswith("/"):
            location = f"{BASE_URL}{location}"
        session.get(location)
        
    print(f"Session obtained for {username}")
    return session

def verify_scalability():
    # 1. User A creates a room
    session_a = get_session("user_a")
    res = session_a.post(f"{BASE_URL}/", data={"create": "true"})
    if "Room:" not in res.text:
        print("Failed to create room")
        sys.exit(1)
    
    # Extract room code (simple parsing)
    import re
    match = re.search(r'Room: <span.*?>(.*?)</span>', res.text)
    room_code = match.group(1)
    print(f"Room created: {room_code}")

    # 2. Connect User A via SocketIO (through Nginx)
    sio_a = socketio.Client(logger=True, engineio_logger=True)
    
    @sio_a.event
    def connect():
        print("User A connected")
        
    @sio_a.event
    def message(data):
        print(f"User A received: {data}")
        if "user_b" in str(data):
            messages_received.append("A_received_B")
            update_event.set()

    # Connect A
    print("User A connecting to Nginx...")
    sio_a.connect(BASE_URL, headers={'Cookie': f"session={session_a.cookies.get('session')}"}, transports=['polling'], wait=False)
    
    # Wait for connection to stabilize
    time.sleep(1)
    
    # 3. Connect User B via SocketIO (through Nginx)
    session_b = get_session("user_b")
    # Join room HTTP
    session_b.post(f"{BASE_URL}/", data={"join": "true", "code": room_code})
    
    sio_b = socketio.Client(logger=True, engineio_logger=True)
    
    @sio_b.event
    def connect():
        print("User B connected")
        sio_b.emit('join', {'room': room_code})
        
    @sio_b.event
    def message(data):
        print(f"User B received: {data}")

    # Connect B
    print("User B connecting to Nginx...")
    sio_b.connect(BASE_URL, headers={'Cookie': f"session={session_b.cookies.get('session')}"}, transports=['polling'], wait=True, namespaces=['/'])

    # Wait for connection to stabilize
    time.sleep(2)
    print(f"User B connected state: {sio_b.connected}")
    # Wait for connection to stabilize
    time.sleep(2)
    print(f"User B connected state: {sio_b.connected}")
    print(f"User B namespaces: {sio_b.namespaces}")
    print("User B sending message...")
    sio_b.emit('message', {'msg': 'Hello from B', 'room': room_code})
    
    # 5. Verify A received it
    print("Waiting for message...")
    if update_event.wait(timeout=10):
        print("SUCCESS: User A received message from User B via Nginx/Redis")
    else:
        print("FAILURE: User A did not receive message")
        sys.exit(1)

    sio_a.disconnect()
    sio_b.disconnect()

if __name__ == "__main__":
    verify_scalability()
