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
-   For Backup/Restore: MySQL client tools (`mysqldump` and `mysql`) available in PATH

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r my_sql_client/requirements.txt
    ```

## Usage

Run the application:
```bash
python my_sql_client/src/main.py
```

On Linux/macOS, if your system uses `python3`, run:
```bash
python3 my_sql_client/src/main.py
```

## Windows Notes

-   The desktop app runs on Windows with Python 3.10+.
-   Backup/Restore requires MySQL client tools in PATH.
-   Typical PATH entry example:
    - `C:\Program Files\MySQL\MySQL Server 8.0\bin`

## Packaging (Windows .exe)

To create a Windows executable with PyInstaller:

1. Install build dependency:
    ```bash
    pip install pyinstaller
    ```

2. Run the packaging script:
    ```bash
    python packaging/create_windows_exe.py
    ```

3. The executable will be generated at:
    - `dist/my-sql-desktop-client/my-sql-desktop-client.exe`

Notes:
- Build on Windows to produce a native `.exe`.
- If your antivirus flags unsigned binaries, this is common for local test builds.

## Packaging (.deb)

This section is Linux-only. To create a `.deb` package:

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
