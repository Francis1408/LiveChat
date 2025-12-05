import requests
import re
import sys

AUTH_URL = "http://127.0.0.1:5002"
CHAT_URL = "http://127.0.0.1:5003"

def verify_list():
    session = requests.Session()
    username = "verify_user"
    password = "password123"
    email = "verify@example.com"

    # Register/Login
    try:
        session.post(f"{AUTH_URL}/register", data={"username": username, "password": password, "email": email, "fullname": "Verify User"})
    except:
        pass
    
    res = session.post(f"{AUTH_URL}/login", data={"username": username, "password": password}, allow_redirects=False)
    if 'sso?token=' not in res.headers.get('Location', ''):
        print("Login failed")
        sys.exit(1)
        
    sso_url = res.headers['Location']
    session.cookies.clear()
    session.get(sso_url)

    # Create Room
    res = session.post(f"{CHAT_URL}/", data={"create": "true"})
    match = re.search(r'Room: <span.*?>(.*?)</span>', res.text)
    if not match:
        print("Failed to create room")
        sys.exit(1)
    
    room_code = match.group(1)
    print(f"Created room: {room_code}")

    # Go back to Home
    res = session.get(f"{CHAT_URL}/")
    
    # Check if room code is in the list
    if room_code in res.text and "Your Conversations" in res.text:
        print("SUCCESS: Room found in conversation list!")
    else:
        print("FAILURE: Room NOT found in conversation list.")
        # print(res.text)
        sys.exit(1)

if __name__ == "__main__":
    verify_list()
