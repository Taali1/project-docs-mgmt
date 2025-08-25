import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

from fastapi import HTTPException, status

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

test_project = Project(name="Monster INC.", description="Cool movie")
test_user = User(user_id="mike", password="wazowski")
test_user_2 = User(user_id="james", password="sullivan")
test_project = Project(name="Monster INC.", description="Cool movie")
test_project_2 = Project(name="Cars", description="Nice movie")

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
    
    insert_user(db_connection, test_user)
    
    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=%s;", (test_user.user_id,))
        user_in_db = cur.fetchone()
        assert user_in_db is not None
        assert user_in_db["user_id"] == "mike"

def test_select_user(db_connection):

    insert_user(db_connection, test_user)

    result = select_user(db_connection, test_user.user_id)

    assert result is not None
    assert result["user_id"] == "mike"
    assert result["password"] == "wazowski"

def test_update_user(db_connection):

    insert_user(db_connection, test_user)

    test_user.password = test_user_2.password

    update_user(db_connection, test_user.user_id, test_user)

    result = select_user(db_connection, test_user.user_id)
    assert result["password"] == test_user_2.password

def test_insert_project(db_connection):

    insert_user(db_connection, test_user)

    project_id = insert_project(db_connection, test_user.user_id, test_project)

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id=%s;", (project_id,))
        result = cur.fetchone()
        assert result is not None
        assert result["name"] == "Monster INC."
        assert result["description"] == "Cool movie"

def test_project_update(db_connection):

    insert_user(db_connection, test_user)

    test_project_2.project_id = insert_project(db_connection, test_user.user_id, test_project)

    update_project(db_connection, test_project_2)

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id=%s;", (test_project_2.project_id,))
        result = cur.fetchone()
        assert result is not None
        assert result["name"] == "Cars"
        assert result["description"] == "Nice movie"

def test_select_projects_with_permissions(db_connection):

    insert_user(db_connection, test_user)

    project_id = insert_project(db_connection, test_user.user_id, test_project)

    result = select_projects_with_permissions(db_connection, test_user.user_id)

    assert result is not None
    assert project_id in result

def test_select_project_info(db_connection):
    # User with permissions
    insert_user(db_connection, test_user)
    project_id = insert_project(db_connection, test_user.user_id, test_project)

    # User without permissions
    insert_user(db_connection, test_user_2)
    insert_project(db_connection, test_user_2.user_id, test_project_2)
    
    # Checking all projects for user with premission
    project_data = select_project_info(db_connection, test_user.user_id)
    assert project_id in project_data
    
    # Cheking all projects to user without permission
    project_data = select_project_info(db_connection, test_user_2.user_id)
    assert project_id not in project_data

    # Checking singular project for user with permission
    project_data = select_project_info(db_connection, test_user.user_id, project_id)
    assert project_id == project_data["project_id"]

    # Checkin singular project for user without permissions
    with pytest.raises(HTTPException) as exc_info:
        project_data = select_project_info(db_connection, test_user_2.user_id, project_id)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


