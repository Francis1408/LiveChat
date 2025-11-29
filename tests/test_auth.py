import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.auth_service import app
from services.common import decode_token

from unittest.mock import MagicMock, patch

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    @patch('services.auth_service.get_db_connection')
    def test_register_and_login(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock Register: User does not exist
        mock_cursor.fetchone.return_value = None 

        username = "testuser_mock"
        email = "test@example.com"
        password = "password123"

        response = self.app.post('/register', data=dict(
            username=username,
            email=email,
            password=password
        ), follow_redirects=True)
        self.assertIn(b'You have sucessfully registered!', response.data)

        # Mock Login: User exists and password matches
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(password)
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'username': username,
            'password': hashed,
            'email': email
        }

        response = self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('sso?token=', response.location)
        
        # Verify Token
        token = response.location.split('token=')[1]
        payload = decode_token(token)
        self.assertEqual(payload['username'], username)

if __name__ == '__main__':
    unittest.main()
