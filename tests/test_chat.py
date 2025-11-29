import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.chat_service import app, socketio
from services.common import generate_token

from unittest.mock import MagicMock, patch

class ChatTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        # We need to mock socketio too if we want to test it fully without running server
        # But Flask-SocketIO test_client handles it.
        
        self.user_id = 9999
        self.username = "testuser_chat"
        self.token = generate_token(self.user_id, self.username)

    @patch('services.chat_service.get_db_connection')
    def test_sso_login(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.app.get(f'/sso?token={self.token}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Join a Room', response.data)

    @patch('services.chat_service.get_db_connection')
    def test_create_room_and_chat(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock Room Check (Room exists when checking in /room)
        mock_cursor.fetchone.return_value = {'id': 1, 'code': 'ABCD', 'owner_id': 9999}
        mock_cursor.fetchall.return_value = [] # For generate_unique_code (no existing rooms)

        with self.app.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = self.user_id
            sess['username'] = self.username

        response = self.app.post('/', data=dict(create='true'), follow_redirects=True)
        self.assertIn(b'Active Users', response.data)
        
        self.assertTrue(mock_cursor.execute.called)


if __name__ == '__main__':
    unittest.main()
