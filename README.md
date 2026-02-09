# MySQL Desktop Client

A lightweight, intuitive, and pleasant MySQL desktop client built with Python and PyQt6.

## Features

-   **Connection Management**: Connect to local or remote MySQL servers.
-   **Database Navigation**: Explore databases and tables via a sidebar tree view.
-   **Query Execution**: Write and run SQL queries in a tabbed interface.
-   **Schema Management**: Create/Drop databases and tables (via context menu).
-   **Backup & Restore**: Dump and restore databases (requires `mysqldump` and `mysql` in PATH).

## Requirements

-   Python 3.10+
-   `mysql-connector-python`
-   `PyQt6`

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r my_sql_client/requirements.txt
    ```

## Usage

Run the application:
```bash
python3 my_sql_client/src/main.py
```

## Packaging (.deb)

To create a `.deb` package for Linux:

1.  Run the packaging script:
    ```bash
    python3 packaging/create_deb.py
    ```
    This will create a directory named `my-sql-desktop-client_1.0.0_all`.

2.  Build the package:
    ```bash
    dpkg-deb --build my-sql-desktop-client_1.0.0_all
    ```

3.  Install the package:
    ```bash
    sudo dpkg -i my-sql-desktop-client_1.0.0_all.deb
    ```
