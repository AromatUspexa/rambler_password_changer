from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / 'data'
PATH_CONFIG = DATA_DIR / "config.py"
PATH_NEW_LIST = DATA_DIR / "new_password.txt"
PATH_LIST = DATA_DIR / "old_password.txt"
PROXY_LIST = DATA_DIR / "proxy.txt"
JS_DIR = BASE_DIR / 'js' / 'hcaptcha.js'
