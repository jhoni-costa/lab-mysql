from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFormLayout)
from database.connector import DatabaseConnector

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to MySQL")
        self.setFixedSize(400, 250)
        self.connector = DatabaseConnector()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        
        self.host_input = QLineEdit("localhost")
        self.user_input = QLineEdit("root")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.port_input = QLineEdit("3306")
        self.db_input = QLineEdit()

        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("User:", self.user_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Port:", self.port_input)
        # database is optional for initial connection
        form_layout.addRow("Database (Optional):", self.db_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.handle_connect)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def handle_connect(self):
        host = self.host_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        port = int(self.port_input.text()) if self.port_input.text().isdigit() else 3306
        database = self.db_input.text() or None

        success, message = self.connector.connect(host, user, password, port, database)
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Connection Error", message)
