from pathlib import Path



SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
API_FILE = BASE_DIR / 'extension' / '1.11.16_0' /'defaultSettings.json'
DATA_DIR = BASE_DIR / 'data'
PATH_CONFIG = DATA_DIR / "config.toml"
PATH_NEW_LIST = DATA_DIR / "new_password.txt"
PATH_LIST = DATA_DIR / "old_password.txt"
PROXY_LIST = DATA_DIR / "proxy.txt"
PATH_EXTENSION = BASE_DIR / 'extension' / '1.11.16_0'
