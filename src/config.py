import os
from pathlib import Path

# Get the project root directory (2 levels up from this file)
BASE_DIR = Path(__file__).parent.parent

# Paths to credentials
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'  
]

DEBUG_MODE = True  # Set to True to enable debug logging