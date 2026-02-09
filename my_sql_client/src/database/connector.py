import mysql.connector
from mysql.connector import Error

class DatabaseConnector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._instance.connection = None
            cls._instance.config = {}
        return cls._instance

    def connect(self, host, user, password, port=3306, database=None):
        """Establishes a connection to the MySQL database."""
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'port': port
        }
        if database:
            self.config['database'] = database

        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                return True, "Connected successfully"
        except Error as e:
            self.connection = None
            return False, str(e)
        
        return False, "Unknown error"

    def disconnect(self):
        """Closes the current connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None

    def is_connected(self):
        """Checks if there is an active connection."""
        return self.connection is not None and self.connection.is_connected()

    def get_connection(self):
        """Returns the active connection object."""
        return self.connection
