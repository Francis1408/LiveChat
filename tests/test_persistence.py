import requests
import re
import sys
import argparse

AUTH_URL = "http://127.0.0.1:5002"
CHAT_URL = "http://127.0.0.1:5003"
USERNAME = "persist_user"
PASSWORD = "password123"
EMAIL = "persist@example.com"

def get_session():
    session = requests.Session()
    # Register (ignore if exists)
    try:
        print("Registering...")
        session.post(f"{AUTH_URL}/register", data={"username": USERNAME, "password": PASSWORD, "email": EMAIL, "fullname": "Persist User"})
        print("Registered.")
    except Exception as e:
        print(f"Register failed: {e}")
    
    # Login
    print("Logging in...")
    res = session.post(f"{AUTH_URL}/login", data={"username": USERNAME, "password": PASSWORD}, allow_redirects=False)
    print(f"Login response: {res.status_code}")
    if 'sso?token=' not in res.headers.get('Location', ''):
        print("Login failed")
        sys.exit(1)
        
    sso_url = res.headers['Location']
    session.cookies.clear()
    session.get(sso_url)
    return session

def setup():
    session = get_session()
    
    # Create Room
    res = session.post(f"{CHAT_URL}/", data={"create": "true"})
    match = re.search(r'Room: <span.*?>(.*?)</span>', res.text)
    if not match:
        print("Failed to create room")
        sys.exit(1)
    
    room_code = match.group(1)
    print(f"SETUP_CREATED_ROOM:{room_code}")
    
    # Verify it is in the list immediately
    res = session.get(f"{CHAT_URL}/")
    if room_code in res.text:
        print("SETUP_VERIFIED_IN_LIST:YES")
    else:
        print("SETUP_VERIFIED_IN_LIST:NO")
        sys.exit(1)

def verify(room_code):
    session = get_session()
    
    # Check list
    res = session.get(f"{CHAT_URL}/")
    if room_code in res.text:
        print(f"VERIFY_SUCCESS: Room {room_code} found in list after restart.")
    else:
        print(f"VERIFY_FAILURE: Room {room_code} NOT found in list.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['setup', 'verify'])
    parser.add_argument('room_code', nargs='?', help='Room code to verify')
    args = parser.parse_args()

    if args.mode == 'setup':
        setup()
    elif args.mode == 'verify':
        if not args.room_code:
            print("Error: room_code required for verify mode")
            sys.exit(1)
        verify(args.room_code)
