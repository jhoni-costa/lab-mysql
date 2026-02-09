from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QSplitter, QLabel, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt
from database.executor import DatabaseExecutor

class QueryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.executor = DatabaseExecutor()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Splitter for editor and results
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Query Editor Area
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        self.query_editor = QPlainTextEdit()
        self.query_editor.setPlaceholderText("Enter SQL query here...")
        
        from ui.syntax_highlighter import SQLHighlighter
        self.highlighter = SQLHighlighter(self.query_editor.document())

        # Start shortcut implementation
        from PyQt6.QtGui import QAction, QKeySequence
        self.run_action = QAction("Run Query", self)
        self.run_action.setShortcut(QKeySequence("Ctrl+Return"))
        self.run_action.triggered.connect(self.run_query)
        self.addAction(self.run_action)
        # End shortcut implementation
        
        # Toolbar for editor
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Query")
        self.run_btn.clicked.connect(self.run_query)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addStretch()

        editor_layout.addWidget(self.query_editor)
        editor_layout.addLayout(btn_layout)
        
        # Results Area
        self.results_table = QTableWidget()
        self.status_label = QLabel("Ready")

        splitter.addWidget(editor_widget)
        splitter.addWidget(self.results_table)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def run_query(self):
        query = self.query_editor.toPlainText().strip()
        if not query:
            self.status_label.setText("Empty query")
            return

        self.status_label.setText("Executing...")
        results, columns, error = self.executor.execute_query(query)

        self.current_query = query
        self.current_db = None
        self.current_table = None
        self.primary_key_col = None
        self.primary_key_idx = -1
        
        # Try to infer table context for editing
        # Simple heuristic: SELECT * FROM `db`.`table` ...
        import re
        match = re.search(r"SELECT\s+\*\s+FROM\s+`?(\w+)`?\.`?(\w+)`?", query, re.IGNORECASE)
        if match:
            self.current_db = match.group(1)
            self.current_table = match.group(2)
            # Fetch primary key for this table to enable editing
            self.fetch_primary_key()

        if error:
            self.status_label.setText(f"Error: {error}")
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
        elif results is not None:
            self.status_label.setText(f"Query executed successfully. {len(results)} rows returned.")
            self.populate_results(results, columns)
        else:
            self.status_label.setText("Query executed successfully. No rows returned.")
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)

    def fetch_primary_key(self):
        if not self.current_db or not self.current_table:
            return
            
        query = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{self.current_db}'
            AND TABLE_NAME = '{self.current_table}'
            AND CONSTRAINT_NAME = 'PRIMARY'
        """
        results, _, error = self.executor.execute_query(query)
        if results and not error:
            self.primary_key_col = results[0][0]

    def populate_results(self, results, columns):
        self.results_table.blockSignals(True) # Prevent triggering changes during population
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        self.results_table.setRowCount(len(results))

        # Find PK index if available
        if self.primary_key_col and self.primary_key_col in columns:
            self.primary_key_idx = columns.index(self.primary_key_col)
        else:
            self.primary_key_idx = -1

        for row_idx, row_data in enumerate(results):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                # Only allow editing if we have a valid PK and context
                if self.primary_key_idx != -1:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Store original valid for comparison/revert if needed (simple version)
                item.setData(Qt.ItemDataRole.UserRole, col_data)
                self.results_table.setItem(row_idx, col_idx, item)
        
        self.results_table.blockSignals(False)
        
        # Connect signal if not already
        try:
             self.results_table.itemChanged.disconnect(self.handle_item_changed)
        except TypeError:
             pass # Was not connected
        
        if self.primary_key_idx != -1:
            self.results_table.itemChanged.connect(self.handle_item_changed)
            self.status_label.setText(self.status_label.text() + " (Editable)")

    def handle_item_changed(self, item):
        row = item.row()
        col = item.column()
        
        new_value = item.text()
        old_value = item.data(Qt.ItemDataRole.UserRole)
        
        if str(new_value) == str(old_value):
            return

        pk_item = self.results_table.item(row, self.primary_key_idx)
        pk_value = pk_item.data(Qt.ItemDataRole.UserRole) # Use original PK value
        
        col_name = self.results_table.horizontalHeaderItem(col).text()
        
        # Generate UPDATE query
        # UPDATE `db`.`table` SET `col` = 'val' WHERE `pk` = 'val'
        
        # Handle quoting for strings, etc. Simple version: always quote
        update_query = f"UPDATE `{self.current_db}`.`{self.current_table}` SET `{col_name}` = %s WHERE `{self.primary_key_col}` = %s"
        
        _, _, error = self.executor.execute_query(update_query, (new_value, pk_value))
        
        if error:
            QMessageBox.critical(self, "Update Failed", f"Failed to update value: {error}")
            # Revert change
            self.results_table.blockSignals(True)
            item.setText(str(old_value))
            self.results_table.blockSignals(False)
        else:
            self.status_label.setText(f"Updated {col_name} for ID {pk_value}")
            item.setData(Qt.ItemDataRole.UserRole, new_value) # Update stored value
