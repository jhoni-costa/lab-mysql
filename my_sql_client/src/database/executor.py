from database.connector import DatabaseConnector
import mysql.connector

class DatabaseExecutor:
    def __init__(self):
        self.connector = DatabaseConnector()

    def execute_query(self, query, params=None):
        """Executes a query and returns the results and columns."""
        if not self.connector.is_connected():
            return None, None, "Not connected to a database"

        connection = self.connector.get_connection()
        try:
            # Use buffered=True to ensure results are fetched and prevent "Commands out of sync"
            cursor = connection.cursor(buffered=True)
            cursor.execute(query, params)
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                results = cursor.fetchall()
                cursor.close()
                return results, columns, None
            else:
                connection.commit()
                cursor.close()
                return None, None, "Query executed successfully"
                
        except mysql.connector.Error as err:
            return None, None, str(err)

    def get_databases(self):
        """Retrieves a list of all databases."""
        results, _, error = self.execute_query("SHOW DATABASES")
        if error:
            return [], error
        return [row[0] for row in results], None

    def get_tables(self, database_name):
        """Retrieves a list of tables in a specific database."""
        # Switch database first or use fully qualified name? Better to switch context or use FROM
        # Let's try switching context for now, or just SHOW TABLES FROM
        results, _, error = self.execute_query(f"SHOW TABLES FROM `{database_name}`")
        if error:
            return [], error
        return [row[0] for row in results], None
