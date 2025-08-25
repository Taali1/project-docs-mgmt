import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

from db.models import User
from db.db import *
del get_db, DB_CONFIG


from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("host"),
    "database": os.getenv("database"),
    "user": os.getenv("user"),
    "password": os.getenv("password")

}

@pytest.fixture()
def db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        conn.autocommit = False
        yield conn
        conn.rollback()
    finally:
        conn.close()

def test_insert_user(db_connection):
    test_user = User(user_id="mike", password="wazowski")
    
    insert_user(db_connection, test_user)
    
    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=%s;", (test_user.user_id,))
        user_in_db = cur.fetchone()
        assert user_in_db is not None
        assert user_in_db["user_id"] == "mike"

def test_select_user(db_connection):
    test_user = User(user_id="mike", password="wazowski")

    insert_user(db_connection, test_user)

    result = select_user(db_connection, test_user.user_id)

    assert result != None
    assert result["user_id"] == "mike"
    assert result["password"] == "wazowski"

def test_update_user(db_connection):
    test_user = User(user_id="mike", password="wazowski")
    test_user_update_to = User(user_id="mike", password="sullivan")

    insert_user(db_connection, test_user)

    update_user(db_connection, test_user.user_id, test_user_update_to)

    result = select_user(db_connection, test_user.user_id)
    assert result["password"] == test_user_update_to.password

def test_insert_project(db_connection):
    test_project = Project(name="Monster INC.", description="Cool movie")
    test_user = User(user_id="mike", password="wazowski")

    insert_user(db_connection, test_user)

    project_id = insert_project(db_connection, test_user.user_id, test_project)

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id=%s;", (project_id,))
        result = cur.fetchone()
        assert result is not None
        assert result["name"] == "Monster INC."
        assert result["description"] == "Cool movie"

def test_project_update(db_connection):
    test_project = Project(name="Monster INC.", description="Cool movie")
    test_project_update_to = Project(name="Cars", description="Nice movie")
    test_user = User(user_id="mike", password="wazowski")

    insert_user(db_connection, test_user)

    test_project_update_to.project_id = insert_project(db_connection, test_user.user_id, test_project)

    update_project(db_connection, test_project_update_to)

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id=%s;", (test_project_update_to.project_id,))
        result = cur.fetchone()
        assert result is not None
        assert result["name"] == "Cars"
        assert result["description"] == "Nice movie"



