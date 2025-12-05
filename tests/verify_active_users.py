import socketio
import requests
import re
import sys
import time
import threading

BASE_URL = "http://127.0.0.1:8080"
AUTH_URL = "http://127.0.0.1:5002"
CHAT_URL = BASE_URL

# Global state for verification
updates_received = []
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
    print(f"Login status: {res.status_code}")
    if res.status_code != 302:
        print(f"Login failed. Response: {res.text[:500]}")
        sys.exit(1)
    sso_url = res.headers['Location']
    session.cookies.clear()
    print(f"SSO redirect to {sso_url}...")
    session.get(sso_url)
    print(f"Session obtained for {username}")
    return session

def verify_active_users():
    # User A setup
    session_a = get_session("user_a")
    res = session_a.post(f"{CHAT_URL}/", data={"create": "true"})
    match = re.search(r'Room: <span.*?>(.*?)</span>', res.text)
    if not match:
        print("Failed to create room")
        print(f"Response status: {res.status_code}")
        with open("debug_room.html", "w") as f:
            f.write(res.text)
        print("Response dumped to debug_room.html")
        sys.exit(1)
    room_code = match.group(1)
    print(f"Room created: {room_code}")

    # User A connect
    sio_a = socketio.Client(logger=True, engineio_logger=True)
    
    @sio_a.on('update_users')
    def on_update_a(data):
        print(f"User A received update: {data}")
        updates_received.append(data['users'])
        update_event.set()

    print("User A connecting...")
    try:
        sio_a.connect(BASE_URL, headers={'Cookie': f"session={session_a.cookies.get('session')}"}, transports=['websocket'], wait=True, namespaces=['/'])
        print("User A connected")
    except Exception as e:
        print(f"User A connection failed: {e}")
        sys.exit(1)
    
    # Wait for initial update (User A only)
    print("Waiting for User A initial update...")
    if not update_event.wait(timeout=5):
        print("Timeout waiting for initial update")
        sys.exit(1)
    
    if "user_a" not in updates_received[-1]:
        print("FAILURE: User A not in list")
        sys.exit(1)
    update_event.clear()

    # User B setup & join
    print("User B joining...")
    session_b = get_session("user_b")
    session_b.post(f"{CHAT_URL}/", data={"join": "true", "code": room_code})
    
    # User B connect
    sio_b = socketio.Client(logger=True, engineio_logger=True)
    
    try:
        sio_b.connect(BASE_URL, headers={'Cookie': f"session={session_b.cookies.get('session')}"}, transports=['websocket'], wait=True, namespaces=['/'])
        print("User B connected")
    except Exception as e:
        print(f"User B connection failed: {e}")
        sys.exit(1)

    # Wait for update (User A + User B)
    print("Waiting for update after User B join...")
    if not update_event.wait(timeout=5):
        print("Timeout waiting for update")
        sys.exit(1)
    
    last_update = updates_received[-1]
    if "user_a" in last_update and "user_b" in last_update:
        print("SUCCESS: Both users in list")
    else:
        print(f"FAILURE: List mismatch: {last_update}")
        sys.exit(1)
    update_event.clear()

    # User B disconnect
    print("User B disconnecting...")
    sio_b.disconnect()

    # Wait for update (User A only)
    print("Waiting for update after User B leave...")
    if not update_event.wait(timeout=5):
        print("Timeout waiting for update")
        sys.exit(1)
    
    last_update = updates_received[-1]
    if "user_a" in last_update and "user_b" not in last_update:
        print("SUCCESS: User B removed from list")
    else:
        print(f"FAILURE: List mismatch: {last_update}")
        sys.exit(1)

    sio_a.disconnect()

if __name__ == "__main__":
    verify_active_users()
