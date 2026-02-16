from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QSplitter, QLabel, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from database.executor import DatabaseExecutor
from ui.widgets.insert_record_dialog import InsertRecordDialog

class QueryWidget(QWidget):
    # Signal emitted when a USE <db> is executed from the editor
    database_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.executor = DatabaseExecutor()
        
        # Track changes for update operations
        self.changed_rows = {}  # {row_idx: {col_idx: new_value}}
        self.current_columns = []
        
        # Context variables for edit/insert
        self.current_db = None
        self.current_table = None
        self.current_query = None
        self.primary_key_col = None
        self.primary_key_idx = -1
        
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
        self.run_btn = QPushButton("▶ Executar")
        self.run_btn.setToolTip("Executar query (Ctrl+Return)")
        self.run_btn.setMinimumHeight(35)
        self.run_btn.clicked.connect(self.run_query)
        btn_layout.addWidget(self.run_btn)
        
        self.save_btn = QPushButton("💾 Salvar")
        self.save_btn.setToolTip("Salvar alterações")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        
        self.insert_btn = QPushButton("➕ Novo")
        self.insert_btn.setToolTip("Inserir novo registro")
        self.insert_btn.setMinimumHeight(35)
        self.insert_btn.clicked.connect(self.insert_new_record)
        self.insert_btn.setEnabled(False)
        btn_layout.addWidget(self.insert_btn)
        
        btn_layout.addStretch()

        editor_layout.addWidget(self.query_editor)
        editor_layout.addLayout(btn_layout)
        
        # Results Area
        self.results_table = QTableWidget()
        self.results_table.itemDoubleClicked.connect(self.on_item_double_clicked)
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
        self.current_columns = columns or []
        self.changed_rows = {}  # Reset changed rows tracking
        
        # Try to infer table context for editing
        # Support multiple formats:
        # SELECT * FROM db.table
        # SELECT * FROM `db`.`table`
        # SELECT * FROM table_name (single table name)
        import re
        
        # Pattern 1: Try to find db.table pattern
        match = re.search(r"FROM\s+[`\"]?(\w+)[`\"]?\s*\.\s*[`\"]?(\w+)[`\"]?", query, re.IGNORECASE)
        if match:
            self.current_db = match.group(1)
            self.current_table = match.group(2)
            print(f"✅ Query context found (Format: db.table): {self.current_db}.{self.current_table}")
            self.fetch_primary_key()
        else:
            # Pattern 2: Try to find just table name (without db prefix)
            match = re.search(r"FROM\s+[`\"]?(\w+)[`\"]?(?:\s|;|WHERE|JOIN|ORDER|LIMIT|$)", query, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                # Try to detect current database from main_window or use a simple approach
                # For now, we'll try to introspect by using SHOW TABLES
                print(f"✅ Query context found (Format: table_only): {table_name}")
                self.current_table = table_name
                # Try to find the database this table belongs to
                self.try_find_database_for_table(table_name)
            else:
                print(f"❌ Query context NOT found in: {query[:100]}")

        if error:
            # Special-case: some non-SELECT successful statements return a success message string
            import re
            if re.match(r"^\s*USE\s+`?\w+`?\s*;?$", query, re.IGNORECASE):
                # consider as success and notify parent
                m = re.search(r"^\s*USE\s+`?(\w+)`?", query, re.IGNORECASE)
                if m:
                    dbname = m.group(1)
                    self.database_changed.emit(dbname)
                    self.status_label.setText(f"Database changed to {dbname}")
                    return

            self.status_label.setText(f"Error: {error}")
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            self.save_btn.setEnabled(False)
            self.insert_btn.setEnabled(False)
        elif results is not None:
            self.status_label.setText(f"Query executed successfully. {len(results)} rows returned.")
            self.populate_results(results, columns)
            
            # Enable buttons ONLY if PK was found during populate_results
            if self.primary_key_idx != -1:
                print(f"✅ PK found! Enabling save and insert buttons")
                self.save_btn.setEnabled(True)
                self.insert_btn.setEnabled(True)
            else:
                print(f"❌ No primary key found. Buttons disabled")
                self.save_btn.setEnabled(False)
                self.insert_btn.setEnabled(False)
        else:
            self.status_label.setText("Query executed successfully. No rows returned.")
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            self.save_btn.setEnabled(False)
            self.insert_btn.setEnabled(False)

    def try_find_database_for_table(self, table_name):
        """Try to find which database contains the given table."""
        if not table_name:
            return
        
        print(f"🔍 Searching for table '{table_name}' in available databases...")
        
        # Get list of all databases
        databases_query = "SHOW DATABASES"
        results, _, error = self.executor.execute_query(databases_query)
        
        if error or not results:
            print(f"❌ Could not fetch databases list")
            return
        
        # Search each database for the table
        for (db_name,) in results:
            if db_name in ('information_schema', 'mysql', 'performance_schema', 'sys'):
                continue  # Skip system databases
            
            check_table_query = f"SHOW TABLES FROM `{db_name}` LIKE '{table_name}'"
            table_results, _, table_error = self.executor.execute_query(check_table_query)
            
            if table_results and not table_error:
                self.current_db = db_name
                print(f"✅ Table found in database: {db_name}")
                self.fetch_primary_key()
                return
        
        print(f"❌ Table '{table_name}' not found in any database")

    def fetch_primary_key(self):
        """Fetch the primary key column name for the current table."""
        if not self.current_db or not self.current_table:
            print(f"❌ Cannot fetch PK: DB={self.current_db}, Table={self.current_table}")
            return
        
        # Try method 1: INFORMATION_SCHEMA
        query1 = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{self.current_db}'
            AND TABLE_NAME = '{self.current_table}'
            AND CONSTRAINT_NAME = 'PRIMARY'
            LIMIT 1
        """
        results, _, error = self.executor.execute_query(query1)
        if results and not error:
            self.primary_key_col = results[0][0]
            print(f"✅ PK found (Method 1): {self.primary_key_col}")
            return
        
        # Try method 2: SHOW KEYS FROM table
        query2 = f"SHOW KEYS FROM `{self.current_db}`.`{self.current_table}` WHERE Key_name = 'PRIMARY'"
        results, _, error = self.executor.execute_query(query2)
        if results and not error and len(results) > 0:
            self.primary_key_col = results[0][4]  # Column_name is at index 4
            print(f"✅ PK found (Method 2): {self.primary_key_col}")
            return
        
        # Try method 3: DESC table (DESCRIBE)
        query3 = f"DESCRIBE `{self.current_db}`.`{self.current_table}`"
        results, _, error = self.executor.execute_query(query3)
        if results and not error:
            for row in results:
                # Check if Key column contains 'PRI'
                if len(row) > 3 and row[3] == 'PRI':  # row[0] is name, row[3] is Key
                    self.primary_key_col = row[0]
                    print(f"✅ PK found (Method 3): {self.primary_key_col}")
                    return
        
        print(f"❌ Primary key not found for {self.current_db}.{self.current_table}")

    def populate_results(self, results, columns):
        self.results_table.blockSignals(True) # Prevent triggering changes during population
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        self.results_table.setRowCount(len(results))

        print(f"📋 Populate: PK col={self.primary_key_col}, Columns={columns}")
        
        # Find PK index if available
        if self.primary_key_col and self.primary_key_col in columns:
            self.primary_key_idx = columns.index(self.primary_key_col)
            print(f"✅ PK index found: {self.primary_key_idx} (column: {self.primary_key_col})")
        else:
            self.primary_key_idx = -1
            print(f"❌ PK not found in columns. PK col: {self.primary_key_col}, Columns: {columns}")

        for row_idx, row_data in enumerate(results):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data) if col_data is not None else "")
                
                # Only allow editing if we have a valid PK and context
                if self.primary_key_idx != -1:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Store original value for comparison/revert if needed
                item.setData(Qt.ItemDataRole.UserRole, col_data)
                self.results_table.setItem(row_idx, col_idx, item)
        
        self.results_table.blockSignals(False)
        self.changed_rows = {}  # Reset tracking
        
        # Connect signal if not already
        try:
             self.results_table.itemChanged.disconnect(self.handle_item_changed)
        except TypeError:
             pass # Was not connected
        
        if self.primary_key_idx != -1:
            self.results_table.itemChanged.connect(self.handle_item_changed)
            self.status_label.setText(self.status_label.text() + " (Duplo clique para editar)")
            print(f"✅ Edit mode enabled")
        else:
            print(f"❌ Edit mode disabled")
        
        # Restore changed rows highlighting
        self.highlight_changed_rows()

    def handle_item_changed(self, item):
        """Track changes to table items without immediately saving."""
        if item is None:
            return
            
        row = item.row()
        col = item.column()
        
        new_value = item.text()
        old_value = item.data(Qt.ItemDataRole.UserRole)
        
        # If value hasn't actually changed, do nothing
        if str(new_value) == str(old_value):
            if row in self.changed_rows and col in self.changed_rows.get(row, {}):
                del self.changed_rows[row][col]
                if not self.changed_rows[row]:
                    del self.changed_rows[row]
            self.highlight_changed_rows()
            return

        # Track the change
        if row not in self.changed_rows:
            self.changed_rows[row] = {}
        
        self.changed_rows[row][col] = new_value
        self.highlight_changed_rows()

    def on_item_double_clicked(self, item):
        """Handle double click on table item to enable editing."""
        print(f"🖱️  Duplo click: PK idx={self.primary_key_idx}, PK col={self.primary_key_col}")
        
        if item is None:
            print(f"❌ Item is None")
            return
        
        # Only allow editing if PK is available
        if self.primary_key_idx == -1:
            print(f"❌ Edit disabled: No primary key")
            QMessageBox.warning(
                self,
                "Edição não disponível",
                f"A tabela não possui chave primária detectada.\n\n"
                f"Banco: {self.current_db}\n"
                f"Tabela: {self.current_table}\n\n"
                f"Verifique se a tabela tem uma chave primária (PRIMARY KEY)."
            )
            return
        
        print(f"✅ Abrindo editor para edição")
        # Set the item to be editable and open editor
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.results_table.editItem(item)

    def highlight_changed_rows(self):
        """Highlight rows that have been modified."""
        # Light yellow for changed rows
        light_yellow = QColor(255, 255, 200)
        
        for row in range(self.results_table.rowCount()):
            for col in range(self.results_table.columnCount()):
                item = self.results_table.item(row, col)
                if item:
                    if row in self.changed_rows:
                        item.setBackground(light_yellow)
                    else:
                        # Reset to default styling
                        item.setBackground(QColor())

    def save_changes(self):
        """Save all tracked changes to the database."""
        print(f"💾 Save clicked. Changed rows: {len(self.changed_rows)}")
        if not self.changed_rows:
            QMessageBox.information(self, "Nenhuma alteração", "Nenhuma alteração para salvar")
            return

        if not (self.current_db and self.current_table and self.primary_key_idx != -1):
            QMessageBox.warning(self, "Erro", "Contexto de tabela não disponível")
            return

        # Confirm before saving
        reply = QMessageBox.question(
            self,
            "Confirmar salvamento",
            f"Salvar {len(self.changed_rows)} linha(s) modificada(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return

        errors = []
        saved_count = 0

        # Process each changed row
        for row_idx, col_changes in self.changed_rows.items():
            try:
                pk_item = self.results_table.item(row_idx, self.primary_key_idx)
                pk_value = pk_item.data(Qt.ItemDataRole.UserRole)

                # Build UPDATE query with all changed columns
                set_clauses = []
                params = []

                for col_idx, new_value in col_changes.items():
                    col_name = self.results_table.horizontalHeaderItem(col_idx).text()
                    set_clauses.append(f"`{col_name}` = %s")
                    params.append(new_value)

                params.append(pk_value)

                update_query = (
                    f"UPDATE `{self.current_db}`.`{self.current_table}` "
                    f"SET {', '.join(set_clauses)} "
                    f"WHERE `{self.primary_key_col}` = %s"
                )

                _, _, error = self.executor.execute_query(update_query, tuple(params))

                if error:
                    errors.append(f"Linha {row_idx + 1}: {error}")
                else:
                    saved_count += 1
                    # Update stored values after successful save
                    for col_idx, new_value in col_changes.items():
                        item = self.results_table.item(row_idx, col_idx)
                        if item:
                            item.setData(Qt.ItemDataRole.UserRole, new_value)

            except Exception as e:
                errors.append(f"Linha {row_idx + 1}: {str(e)}")

        # Clear changed rows tracking and refresh highlighting
        self.changed_rows = {}
        self.highlight_changed_rows()

        # Show result message
        if errors:
            error_msg = "\n".join(errors)
            QMessageBox.warning(
                self,
                "Erros durante salvamento",
                f"Salvo: {saved_count} linha(s)\n\nErros:\n{error_msg}"
            )
        else:
            self.status_label.setText(f"Salvas com sucesso: {saved_count} linha(s) modificada(s)")
            QMessageBox.information(self, "Sucesso", f"Salvas {saved_count} linha(s) com sucesso")
    def insert_new_record(self):
        """Open dialog to insert a new record into the table."""
        print(f"➕ Insert clicked. DB={self.current_db}, Table={self.current_table}, Columns={self.current_columns}")
        if not (self.current_db and self.current_table):
            QMessageBox.warning(self, "Erro", "Contexto de tabela não disponível")
            return

        if not self.current_columns:
            QMessageBox.warning(self, "Erro", "Nenhuma coluna disponível")
            return

        # Show insert dialog
        dialog = InsertRecordDialog(
            parent=self,
            column_names=self.current_columns,
            primary_key_col=self.primary_key_col
        )

        if dialog.exec():
            # Validate inputs
            is_valid, error_msg = dialog.validate_inputs()
            if not is_valid:
                QMessageBox.warning(self, "Validação", error_msg)
                return

            # Get values from dialog
            values = dialog.get_values()

            try:
                # Build INSERT query
                column_names = list(values.keys())
                placeholders = ", ".join(["%s"] * len(column_names))
                columns_str = ", ".join([f"`{col}`" for col in column_names])

                insert_query = (
                    f"INSERT INTO `{self.current_db}`.`{self.current_table}` "
                    f"({columns_str}) VALUES ({placeholders})"
                )

                params = tuple(values[col] for col in column_names)

                _, _, error = self.executor.execute_query(insert_query, params)

                if error:
                    QMessageBox.critical(self, "Erro ao inserir", f"Erro: {error}")
                else:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        "Novo registro inserido com sucesso!"
                    )
                    # Refresh results by running the current query again
                    self.run_query()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao inserir: {str(e)}")
