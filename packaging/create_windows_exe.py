import importlib.util
import os
import subprocess
import sys
from pathlib import Path

APP_NAME = "my-sql-desktop-client"


def _ensure_pyinstaller_installed():
    return importlib.util.find_spec("PyInstaller") is not None


def _preflight_imports_ok():
    required_modules = [
        "PyQt6.QtWidgets",
        "mysql.connector",
        "pandas",
        "keyring",
    ]

    for module_name in required_modules:
        try:
            __import__(module_name)
        except Exception as exc:
            print(f"Preflight failed: cannot import '{module_name}': {exc}")
            if module_name.startswith("PyQt6"):
                print("Try repairing PyQt6 in user scope:")
                print("  python -m pip install --user --force-reinstall --no-cache-dir PyQt6 PyQt6-Qt6 PyQt6-sip")
            else:
                print("Try installing project requirements in user scope:")
                print("  python -m pip install --user -r my_sql_client/requirements.txt")
            return False

    return True


def build_windows_exe():
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "my_sql_client" / "src"
    entry_point = src_dir / "main.py"

    if not entry_point.exists():
        print(f"Entry point not found: {entry_point}")
        return 1

    if os.name != "nt":
        print("This script targets Windows builds. You can still run it elsewhere, but output may not be a native Windows executable.")

    if not _ensure_pyinstaller_installed():
        print("PyInstaller is not installed in this environment.")
        print("Install it with: pip install pyinstaller")
        return 1

    if not _preflight_imports_ok():
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--paths",
        str(src_dir),
        "--collect-all",
        "PyQt6",
        "--hidden-import",
        "mysql.connector",
        "--hidden-import",
        "pandas",
        "--hidden-import",
        "keyring",
        str(entry_point),
    ]

    print("Running:", " ".join(command))
    result = subprocess.run(command, cwd=str(project_root), check=False)

    if result.returncode != 0:
        print("Build failed.")
        return result.returncode

    exe_path = project_root / "dist" / APP_NAME / f"{APP_NAME}.exe"
    print("Build completed.")
    print(f"Executable path: {exe_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_windows_exe())
