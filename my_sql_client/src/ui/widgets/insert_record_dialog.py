"""Dialog for inserting a new record into a table."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt


class InsertRecordDialog(QDialog):
    """Dialog to insert a new record with input fields for each column."""

    def __init__(self, parent=None, column_names=None, primary_key_col=None):
        """
        Initialize the insert record dialog.

        Args:
            parent: Parent widget
            column_names: List of column names
            primary_key_col: Name of primary key column (usually auto-increment)
        """
        super().__init__(parent)
        self.setWindowTitle("Inserir novo registro")
        self.setMinimumWidth(500)
        
        self.column_names = column_names or []
        self.primary_key_col = primary_key_col
        self.input_fields = {}
        
        self.init_ui()

    def init_ui(self):
        """Initialize the UI with input fields for each column."""
        layout = QVBoxLayout()

        # Scroll area for many columns
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        # Create input fields for each column
        for col_name in self.column_names:
            # Skip primary key if it's auto-increment
            if col_name == self.primary_key_col:
                continue

            label = QLabel(f"{col_name}:")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {col_name}")
            
            form_layout.addRow(label, input_field)
            self.input_fields[col_name] = input_field

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Button layout
        btn_layout = QHBoxLayout()
        
        insert_btn = QPushButton("Inserir")
        insert_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(insert_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_values(self):
        """
        Get the values entered in the dialog.

        Returns:
            Dictionary mapping column names to values
        """
        values = {}
        for col_name, input_field in self.input_fields.items():
            value = input_field.text().strip()
            values[col_name] = value if value else None
        
        return values

    def validate_inputs(self):
        """
        Validate that all required fields are filled.

        Returns:
            Tuple (is_valid, error_message)
        """
        for col_name, input_field in self.input_fields.items():
            value = input_field.text().strip()
            if not value:
                return False, f"Campo '{col_name}' não pode estar vazio"
        
        return True, ""
