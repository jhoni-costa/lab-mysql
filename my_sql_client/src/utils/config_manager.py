import json
import os
from pathlib import Path
import keyring


def _get_config_dir():
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "my_sql_client"
        return Path.home() / "AppData" / "Roaming" / "my_sql_client"
    return Path.home() / ".config" / "my_sql_client"


CONFIG_DIR = _get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
KEYRING_SERVICE = "my_sql_client"


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_connection(host, user, port, database, password=None, save_password=False):
    _ensure_dir()
    data = {
        "host": host,
        "user": user,
        "port": port,
        "database": database,
        "save_password": bool(save_password),
    }
    # save non-sensitive data to file
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

    # save password securely using keyring if requested
    if save_password and password:
        keyring.set_password(KEYRING_SERVICE, user, password)
    else:
        try:
            # attempt to remove any previously stored password for this user
            keyring.delete_password(KEYRING_SERVICE, user)
        except Exception:
            pass


def load_connection():
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    result = {
        "host": data.get("host", "localhost"),
        "user": data.get("user", "root"),
        "port": data.get("port", 3306),
        "database": data.get("database"),
        "save_password": data.get("save_password", False),
        "password": None,
    }

    if result["save_password"]:
        try:
            pw = keyring.get_password(KEYRING_SERVICE, result["user"])
            result["password"] = pw
        except Exception:
            result["password"] = None

    return result
