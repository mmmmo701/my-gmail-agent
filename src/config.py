import os
from pathlib import Path

# Get the project root directory (2 levels up from this file)
BASE_DIR = Path(__file__).parent.parent

# Paths to credentials
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

# API Scopes
# "modify" allows reading, writing, and sending. 
# We need this now so we don't have to re-authenticate later when adding "Draft" features.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

