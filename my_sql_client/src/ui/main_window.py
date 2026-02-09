from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTreeWidget, QTreeWidgetItem, QTabWidget, QToolBar, 
                             QMessageBox, QSplitter, QMenu, QFileDialog, QInputDialog)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt
from ui.connection_dialog import ConnectionDialog
from ui.widgets.query_widget import QueryWidget
from database.connector import DatabaseConnector
from database.executor import DatabaseExecutor
from utils.backup_manager import BackupManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MySQL Client")
        self.resize(1200, 800)
        
        self.connector = DatabaseConnector()
        self.executor = DatabaseExecutor()
        
        self.init_ui()
        self.show_connection_dialog()

    def init_ui(self):
        # Central Main Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter for sidebar and content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar (Database/Table Navigation)
        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderLabel("Databases")
        self.sidebar.itemDoubleClicked.connect(self.on_sidebar_item_double_clicked)
        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.open_sidebar_menu)
        
        # Main Content Area (Tabs)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Add initial query tab
        self.add_query_tab()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        connect_action = QAction(QIcon(), "Connect", self)
        connect_action.triggered.connect(self.show_connection_dialog)
        toolbar.addAction(connect_action)
        
        disconnect_action = QAction(QIcon(), "Disconnect", self)
        disconnect_action.triggered.connect(self.disconnect)
        toolbar.addAction(disconnect_action)
        
        refresh_action = QAction(QIcon(), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_sidebar)
        toolbar.addAction(refresh_action)

        new_query_action = QAction(QIcon(), "New Query", self)
        new_query_action.triggered.connect(self.add_query_tab)
        toolbar.addAction(new_query_action)

    def show_connection_dialog(self):
        dialog = ConnectionDialog(self)
        if dialog.exec():
            # If connected, refresh sidebar
            self.refresh_sidebar()
            self.setWindowTitle(f"MySQL Client - Connected to {self.connector.config.get('host')}")

    def disconnect(self):
        self.connector.disconnect()
        self.sidebar.clear()
        self.setWindowTitle("MySQL Client - Disconnected")
        QMessageBox.information(self, "Disconnected", "Disconnected from database.")

    def refresh_sidebar(self):
        if not self.connector.is_connected():
            return

        self.sidebar.clear()
        databases, error = self.executor.get_databases()
        
        if error:
            QMessageBox.critical(self, "Error", f"Failed to fetch databases: {error}")
            return

        for db in databases:
            db_item = QTreeWidgetItem([db])
            db_item.setData(0, Qt.ItemDataRole.UserRole, "database")
            # Create a dummy child so it's expandable
            db_item.addChild(QTreeWidgetItem(["Loading..."]))
            self.sidebar.addTopLevelItem(db_item)
            
        self.sidebar.itemExpanded.connect(self.on_item_expanded)

    def on_item_expanded(self, item):
        if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
            item.removeChild(item.child(0))
            db_name = item.text(0)
            tables, error = self.executor.get_tables(db_name)
            
            if error:
                 QMessageBox.critical(self, "Error", f"Failed to fetch tables for {db_name}: {error}")
                 return

            for table in tables:
                table_item = QTreeWidgetItem([table])
                table_item.setData(0, Qt.ItemDataRole.UserRole, "table")
                item.addChild(table_item)

    def on_sidebar_item_double_clicked(self, item, column):
        if item.data(0, Qt.ItemDataRole.UserRole) == "table":
            table_name = item.text(0)
            db_item = item.parent()
            if db_item:
                db_name = db_item.text(0)
                # self.add_query_tab(f"SELECT * FROM `{db_name}`.`{table_name}` LIMIT 100")
                # Avoid running immediately, just populate
                self.add_query_tab(f"SELECT * FROM `{db_name}`.`{table_name}` LIMIT 100")
                # Wait, add_query_tab runs it if query is passed. That's fine.



    def open_sidebar_menu(self, position):
        item = self.sidebar.itemAt(position)
        if not item:
            return

        menu = QMenu()
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type == "database":
            create_table_action = QAction("Create Table", self)
            create_table_action.triggered.connect(lambda: self.create_table_dialog(item.text(0)))
            menu.addAction(create_table_action)
            
            drop_db_action = QAction("Drop Database", self)
            drop_db_action.triggered.connect(lambda: self.drop_database(item.text(0)))
            menu.addAction(drop_db_action)
            
            menu.addSeparator()

            dump_action = QAction("Dump Database", self)
            dump_action.triggered.connect(lambda: self.dump_database(item.text(0)))
            menu.addAction(dump_action)
            
            restore_action = QAction("Restore Database", self)
            restore_action.triggered.connect(lambda: self.restore_database(item.text(0)))
            menu.addAction(restore_action)

        elif item_type == "table":
            drop_table_action = QAction("Drop Table", self)
            drop_table_action.triggered.connect(lambda: self.drop_table(item.parent().text(0), item.text(0)))
            menu.addAction(drop_table_action)
            
        menu.exec(self.sidebar.viewport().mapToGlobal(position))

    def drop_database(self, db_name):
        reply = QMessageBox.question(self, 'Confirm Drop', 
                                     f"Are you sure you want to drop database '{db_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            _, _, error = self.executor.execute_query(f"DROP DATABASE `{db_name}`")
            if error:
                QMessageBox.critical(self, "Error", f"Failed to drop database: {error}")
            else:
                QMessageBox.information(self, "Success", f"Database '{db_name}' dropped successfully.")
                self.refresh_sidebar()

    def drop_table(self, db_name, table_name):
        reply = QMessageBox.question(self, 'Confirm Drop', 
                                     f"Are you sure you want to drop table '{table_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            _, _, error = self.executor.execute_query(f"DROP TABLE `{db_name}`.`{table_name}`")
            if error:
                QMessageBox.critical(self, "Error", f"Failed to drop table: {error}")
            else:
                QMessageBox.information(self, "Success", f"Table '{table_name}' dropped successfully.")
                self.refresh_sidebar() # Ideally just remove the item but full refresh is safer

    def create_table_dialog(self, db_name):
        # Quick and dirty: open a query tab with a template
        template = f"CREATE TABLE `{db_name}`.`new_table` (\n  `id` INT NOT NULL AUTO_INCREMENT,\n  `name` VARCHAR(45) NULL,\n  PRIMARY KEY (`id`)\n);"
        self.add_query_tab(template)
        
    def dump_database(self, db_name):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Dump", f"{db_name}.sql", "SQL Files (*.sql)")
        if file_path:
            config = self.connector.config
            success, message = BackupManager.dump_database(
                config['host'], config['user'], config['password'], config['port'], db_name, file_path
            )
            if success:
                 QMessageBox.information(self, "Success", message)
            else:
                 QMessageBox.critical(self, "Error", message)

    def restore_database(self, db_name):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Dump", "", "SQL Files (*.sql)")
        if file_path:
            reply = QMessageBox.question(self, 'Confirm Restore', 
                                     f"Are you sure you want to restore '{file_path}' into database '{db_name}'? This works best on empty databases.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                config = self.connector.config
                success, message = BackupManager.restore_database(
                    config['host'], config['user'], config['password'], config['port'], db_name, file_path
                )
                if success:
                    QMessageBox.information(self, "Success", message)
                    self.refresh_sidebar()
                else:
                    QMessageBox.critical(self, "Error", message)

    def add_query_tab(self, query=None):
        query_widget = QueryWidget()
        if query:
            query_widget.query_editor.setPlainText(query)
            # Only run if it's a SELECT, otherwise just show the template
            if query.strip().upper().startswith("SELECT"):
                query_widget.run_query()
        
        index = self.tabs.addTab(query_widget, "Query")
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        if self.tabs.count() > 1:
             self.tabs.removeTab(index)

