import unittest
from unittest.mock import MagicMock, patch
from database.connector import DatabaseConnector
from database.executor import DatabaseExecutor

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.connector = DatabaseConnector()
        # Reset singleton for testing
        self.connector._instance = None
        self.connector = DatabaseConnector()

    @patch('mysql.connector.connect')
    def test_connection_success(self, mock_connect):
        mock_conn_instance = MagicMock()
        mock_conn_instance.is_connected.return_value = True
        mock_connect.return_value = mock_conn_instance
        
        success, message = self.connector.connect('localhost', 'user', 'pass')
        self.assertTrue(success)
        self.assertEqual(message, "Connected successfully")

    @patch('mysql.connector.connect')
    def test_connection_failure(self, mock_connect):
        from mysql.connector import Error as MySQLError
        # Create a mock error that matches what the connector expects
        mock_connect.side_effect = MySQLError("Connection failed")
        
        success, message = self.connector.connect('localhost', 'user', 'pass')
        self.assertFalse(success)
        self.assertIn("Connection failed", message)

    @patch('database.connector.DatabaseConnector.get_connection')
    @patch('database.connector.DatabaseConnector.is_connected')
    def test_executor_query(self, mock_is_connected, mock_get_conn):
        mock_is_connected.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock SELECT result
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'test')]
        
        executor = DatabaseExecutor()
        results, columns, error = executor.execute_query("SELECT * FROM test")
        
        self.assertIsNone(error)
        self.assertEqual(columns, ['id', 'name'])
        self.assertEqual(results, [(1, 'test')])

if __name__ == '__main__':
    unittest.main()
