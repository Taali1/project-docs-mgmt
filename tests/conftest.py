import pytest

import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv
import os


load_dotenv()

REQUIRED_ENV_VARIABLES = {
"TEST_DB_HOST": "host",
"TEST_DB_NAME": "database",
"TEST_DB_USER": "user",
"TEST_DB_PASSWORD": "password"
}

DB_CONFIG = {}

for env_var, config_key in REQUIRED_ENV_VARIABLES.items():
    value = os.getenv(env_var)
    if not value:
        raise ValueError(f"Environment variable '{env_var}' is not set.")
    DB_CONFIG[config_key] = value

@pytest.fixture(autouse=True, scope="function")
def db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn        
    finally:
        cleanup_conn = psycopg2.connect(**DB_CONFIG)
        try:
            with cleanup_conn, cleanup_conn.cursor() as cur:
                cur.execute("DELETE FROM user_project;")
                cur.execute("DELETE FROM users;")
                cur.execute("DELETE FROM projects;")
        finally:
            cleanup_conn.close()
            conn.close()