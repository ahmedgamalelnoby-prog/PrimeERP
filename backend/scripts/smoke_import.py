import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

# The smoke test must be independent of a developer's local .env database
# driver. Use SQLite so importing the application does not require psycopg2
# or a running PostgreSQL instance.
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./release_gate_smoke.db"

import main

print("Application import OK:", main.app.title)
