import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

from datetime import datetime

from tests.test_data import users_test_data, projects_test_data, user_project_test_data
from db.db import *
del get_db, DB_CONFIG


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

@pytest.fixture(autouse=True)
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


def create_user_in_db(cur, user_id, password):
    user = User(user_id=user_id, password=password)
    cur.execute("INSERT INTO users VALUES (%s, %s);", (user.user_id, user.password))
    return user

def create_project_in_db(cur, name, description):
    project = Project(name=name, description=description)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO projects (name, description, created_at, modified_at) VALUES (%s, %s, %s, %s) RETURNING project_id;", 
        (project.name, project.description, current_time, current_time))
    project.project_id = cur.fetchone()["project_id"]
    return project

def create_relation_in_db(cur, user_id, project_id, permission):
        cur.execute("INSERT INTO user_project VALUES (%s, %s, %s)", 
            (user_id, project_id, permission))


@pytest.mark.parametrize("user_id, password", users_test_data)
def test_insert_user(db_connection, user_id, password):
    test_user = User(user_id=user_id, password=password)

    insert_user(db_connection, test_user)
    
    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=%s;", (test_user.user_id,))
        user_in_db = cur.fetchone()
        assert user_in_db is not None
        assert user_in_db["user_id"] == user_id

@pytest.mark.parametrize("user_id, password", users_test_data)
def test_select_user(db_connection, user_id, password):
    with db_connection.cursor() as cur:
        test_user = create_user_in_db(cur, user_id=user_id, password=password)
    

    result = select_user(db_connection, test_user.user_id)

    assert result is not None
    assert result["user_id"] == user_id
    assert result["password"] == password

@pytest.mark.parametrize("user_id, password", users_test_data)
def test_update_user(db_connection, user_id, password):
    with db_connection.cursor() as cur:
        test_user = create_user_in_db(cur, user_id=user_id, password=password)

    test_user.password = password + "_changed"

    update_user(db_connection, test_user.user_id, test_user)

    result = select_user(db_connection, test_user.user_id)
    assert result["password"] == password + "_changed"

@pytest.mark.parametrize("name, description", projects_test_data)
def test_insert_project(db_connection, name, description):
    with db_connection.cursor() as cur:
        test_user = create_user_in_db(cur, user_id="mike", password="wazowski")
    test_project = Project(name=name, description=description)
    
    project_id = insert_project(db_connection, test_user.user_id, test_project)

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id=%s;", (project_id,))
        result = cur.fetchone()
        assert result is not None
        assert result["name"] == name
        assert result["description"] == description

@pytest.mark.parametrize("name, description", projects_test_data)
def test_project_update(db_connection, name, description):
    with db_connection.cursor() as cur:
        test_project = create_project_in_db(cur, name=name, description=description)


    test_project.name = name + "_changed"
    test_project.description = description + "_changed"

    update_project(db_connection, test_project)

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id=%s;", (test_project.project_id,))
        result = cur.fetchone()
        assert result is not None
        assert result["name"] == name + "_changed"
        assert result["description"] == description + "_changed"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_select_projects_with_permissions(db_connection, user_owner, user_participant):
    with db_connection.cursor() as cur:
        test_user = create_user_in_db(cur, user_id=user_owner["user_id"], password=user_owner["password"])
        test_project = create_project_in_db(cur, name=user_owner["name"], description=user_owner["description"])
        create_relation_in_db(cur, test_user.user_id, test_project.project_id, permission="owner")

    result = select_projects_with_permissions(db_connection, test_user.user_id)

    assert len(result) >= 1

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_select_project_info(db_connection, user_owner, user_participant):
    with db_connection.cursor() as cur:
        test_user_owner = create_user_in_db(cur, user_id=user_owner["user_id"], password=user_owner["password"])
        test_user_no_access = create_user_in_db(cur, user_id=user_participant["user_id"], password=user_participant["password"])
        test_project = create_project_in_db(cur, name=user_owner["name"], description=user_owner["description"])
        create_relation_in_db(cur, test_user_owner.user_id, test_project.project_id, permission="owner")

    # Checking all projects for user with premission
    project_data = select_project_info(db_connection, test_user_owner.user_id)
    assert test_project.project_id in project_data
    
    # Cheking all projects to user without permission
    project_data = select_project_info(db_connection, test_user_no_access.user_id)
    assert test_project.project_id not in project_data

    # Checking singular project for user with permission
    project_data = select_project_info(db_connection, test_user_owner.user_id, test_project.project_id)
    assert test_project.project_id == project_data["project_id"]

    # Checkin singular project for user without permissions
    with pytest.raises(HTTPException) as exc_info:
        project_data = select_project_info(db_connection, test_user_no_access.user_id, test_project.project_id)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_check_permission(db_connection, user_owner, user_participant):
    with db_connection.cursor() as cur:
        test_user_owner = create_user_in_db(cur, user_id=user_owner["user_id"], password=user_owner["password"])
        test_user_no_access = create_user_in_db(cur, user_id=user_participant["user_id"], password=user_participant["password"])
        test_project = create_project_in_db(cur, name=user_owner["name"], description=user_owner["description"])
        create_relation_in_db(cur, test_user_owner.user_id, test_project.project_id, permission="owner")

    result = check_permission(db_connection, test_user_owner.user_id, test_project.project_id)
    assert result == "owner"

    result = check_permission(db_connection, test_user_no_access.user_id, test_project.project_id)
    assert result is None

    with db_connection.cursor() as cur:
        create_relation_in_db(cur, test_user_no_access.user_id, test_project.project_id, permission="participant")

    result = check_permission(db_connection, test_user_no_access.user_id, test_project.project_id)
    assert result == "participant"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_delete_permission(db_connection, user_owner, user_participant):
    with db_connection.cursor() as cur:
        test_user_owner = create_user_in_db(cur, user_id=user_owner["user_id"], password=user_owner["password"])
        test_user_participant = create_user_in_db(cur, user_id=user_participant["user_id"], password=user_participant["password"])
        test_project = create_project_in_db(cur, name=user_owner["name"], description=user_owner["description"])
        create_relation_in_db(cur, test_user_owner.user_id, test_project.project_id, permission="owner")
        create_relation_in_db(cur, test_user_participant.user_id, test_project.project_id, permission="participant")

    # Owner deleting his own permission
    with pytest.raises(HTTPException) as exc_info:
        delete_permission(db_connection, test_user_owner.user_id, test_user_owner.user_id, test_project.project_id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    # Participant deleting someones permission
    with pytest.raises(HTTPException) as exc_info:
        delete_permission(db_connection, test_user_participant.user_id, test_user_owner.user_id, test_project.project_id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    # Participant deleting his own pemission
    result = delete_permission(db_connection, test_user_participant.user_id, test_user_participant.user_id, test_project.project_id)
    assert result

    # Owner deleting participant's permission
    with db_connection.cursor() as cur:
        create_relation_in_db(cur, test_user_participant.user_id, test_project.project_id, permission="participant")
    result = delete_permission(db_connection, test_user_owner.user_id, test_user_participant.user_id, test_project.project_id)
    assert result

@pytest.mark.parametrize("user_id, password", users_test_data)
def test_delete_user(db_connection, user_id, password):
    with db_connection.cursor() as cur:
        test_user = create_user_in_db(cur, user_id=user_id, password=password)

    delete_user(db_connection, user_id)
    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id = %s", (test_user.user_id,))
        result = cur.fetchone()
    assert result is None

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_delete_project(db_connection, user_owner, user_participant):
    with db_connection.cursor() as cur:
        test_user_owner = create_user_in_db(cur, user_id=user_owner["user_id"], password=user_owner["password"])
        test_user_participant = create_user_in_db(cur, user_id=user_participant["user_id"], password=user_participant["password"])
        test_project = create_project_in_db(cur, name=user_owner["name"], description=user_owner["description"])
        create_relation_in_db(cur, test_user_owner.user_id, test_project.project_id, permission="owner")
        create_relation_in_db(cur, test_user_participant.user_id, test_project.project_id, permission="participant")

    with pytest.raises(HTTPException) as exc_info:
        delete_project(db_connection, test_user_participant.user_id, test_project.project_id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    delete_project(db_connection, test_user_owner.user_id, test_project.project_id)
    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id = %s", (test_project.project_id,))
        result = cur.fetchone()
    assert result is None


