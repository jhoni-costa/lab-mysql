import os
import shutil
import subprocess

APP_NAME = "my-sql-desktop-client"
VERSION = "1.0.0"
ARCH = "all"
MAINTAINER = "Jhoni <jhoni@example.com>"
DESCRIPTION = "A lightweight MySQL desktop client."

def create_deb_structure():
    base_dir = f"{APP_NAME}_{VERSION}_{ARCH}"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    
    os.makedirs(f"{base_dir}/DEBIAN")
    os.makedirs(f"{base_dir}/usr/share/{APP_NAME}")
    os.makedirs(f"{base_dir}/usr/bin")
    os.makedirs(f"{base_dir}/usr/share/applications")
    
    # Copy source code
    shutil.copytree("my_sql_client", f"{base_dir}/usr/share/{APP_NAME}/my_sql_client")
    
    # Create control file
    with open(f"{base_dir}/DEBIAN/control", "w") as f:
        f.write(f"Package: {APP_NAME}\n")
        f.write(f"Version: {VERSION}\n")
        f.write(f"Section: utils\n")
        f.write(f"Priority: optional\n")
        f.write(f"Architecture: {ARCH}\n")
        f.write(f"Maintainer: {MAINTAINER}\n")
        f.write(f"Description: {DESCRIPTION}\n")
        f.write("Depends: python3, python3-pyqt6, python3-mysql.connector\n")
    
    # Create wrapper script
    wrapper_script = f"""#!/bin/bash
export PYTHONPATH=/usr/share/{APP_NAME}/
python3 /usr/share/{APP_NAME}/my_sql_client/src/main.py "$@"
"""
    with open(f"{base_dir}/usr/bin/{APP_NAME}", "w") as f:
        f.write(wrapper_script)
    os.chmod(f"{base_dir}/usr/bin/{APP_NAME}", 0o755)

    # Create desktop entry
    desktop_entry = f"""[Desktop Entry]
Name=MySQL Desktop Client
Comment=Manage MySQL databases
Exec=/usr/bin/{APP_NAME}
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;Database;
"""
    with open(f"{base_dir}/usr/share/applications/{APP_NAME}.desktop", "w") as f:
        f.write(desktop_entry)
        
    print(f"Structure created in {base_dir}")
    print("To build .deb, run: dpkg-deb --build " + base_dir)

if __name__ == "__main__":
    create_deb_structure()
