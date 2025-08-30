from fastapi import HTTPException, status

from db.models import *

from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from dotenv import load_dotenv
import os

load_dotenv()

REQUIRED_ENV_VARIABLES = {
    "DB_HOST": "host",
    "DB_NAME": "database",
    "DB_USER": "user",
    "DB_PASSWORD": "password",
}

DB_CONFIG = {}

for env_var, config_key in REQUIRED_ENV_VARIABLES.items():
    value = os.getenv(env_var)
    if not value:
        raise ValueError(f"Environment variable '{env_var}' is not set.")
    DB_CONFIG[config_key] = value

# TODO: Refactor. Add `try` stetmant to functions

@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def insert_user(conn, user: User) -> None:
    """Inserting a user to database

    Args:
        conn (psycopg2.connect): Connection to databases.
        user (User): pydantic model, contains `user_id: str` and `password: str` values
    """
    with conn.cursor() as cur:
        cur.execute("INSERT INTO users (user_id, password) VALUES (%s, %s);", (user.user_id, user.password))

def select_user(conn, user_id: str) -> User:
    """
    Queries for user data.

    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (str): ID of the user whose data is queried

    Returns:
        dict: Dictionary with values `user_id` and `password`
    """
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, password FROM users WHERE user_id = %s;", (user_id,))
        user = cur.fetchone()
        if user is not None:
            return User(user_id=user["user_id"], password=user["password"])
        else: 
            return None

def update_user(conn, user_id: str, user: User) -> None:
    """Updating users data

    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (str): ID of a user whose data is updated
        user (User): pydantic model, contains `user_id: str` and `password: str`
    """
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET password = %s WHERE user_id = %s;", (user.password, user_id))

def insert_project(conn, user_id: str, project: Project) -> int:
    """Creates a project and user - project relation with user as an `owner`.
    
    Args:
        conn (psycopg2.connect): Connection to database.
        user (str): ID of as user who is adding a project.
    
    Returns:
        int: ID of a project that has been added.
    
    """

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.cursor() as cur:
        if project.description:
            cur.execute("""
                INSERT INTO projects (name, description, created_at, modified_at)
                VALUES (%s, %s, %s, %s) 
                RETURNING project_id;
                """,
                (project.name, project.description, current_time, current_time))
        else:
            cur.execute("""
                INSERT INTO projects (name, created_at, modified_at)
                VALUES (%s, %s, %s) 
                RETURNING project_id;
                """,
                (project.name, current_time, current_time))

        project_id = cur.fetchone()["project_id"]
        
        cur.execute("""
        INSERT INTO user_project (user_id, project_id, permission) 
        VALUES (%s, %s, %s);
        """, 
        (user_id, project_id, Permission.owner.value))

        return project_id 


def update_project(conn, project: Project):
    """Updates a project with provided values.
    Automatically changes `modified_at` to current time.

    Args:
        conn (psycopg2.connect): Connection to database.
        project (Project): pydantic model, contains 
            `poroject_id: int` (optional), 
            `name: str`,
            `description: str` (optional),
            `created_at: datetime` (optional),
            `modified_at: datetime` (optional)

    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.cursor() as cur:
        fields = []
        values = []

        if project.name:
            fields.append("name = %s")
            values.append(project.name)

        if project.description:
            fields.append("description = %s")
            values.append(project.description)

        fields.append("modified_at = %s")
        values.append(current_time)

        values.append(project.project_id)

        query = f"""
            UPDATE projects
            SET {", ".join(fields)}
            WHERE project_id = %s;
        """

        cur.execute(query, values)

def delete_project(conn, user_id: str, project_id: int):
    """Deletes a project if users have such permissions.

    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (str): ID of a user whose permissions are checked
        project_id (int): ID of a project for deletion

    Raises:
        HTTPException 401: If user is not a "owner" and have no premission for deleting
        HTTPException 500: If server error occures
    """
    try:
        if check_permission(conn, user_id, project_id) == "owner":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM projects WHERE user_id = %s AND project_id = %s", (user_id, project_id))
        else:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authorized for this action")
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, e)

def select_projects_with_permissions(conn, user_id):
    """Returns all projects that user have permission to.
    
    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (int): ID of a user whose projects are queried.

    Returns:
        tuple: IDs of a project that user have access to.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT project_id
            FROM user_project
            WHERE user_id = %s
            """, 
            (user_id,))
        result = cur.fetchall()
    return [row["project_id"] for row in result]

def select_project_info(conn, user_id: str, project_id: int = None) -> dict:
    """Queries database for project's info that user has access to.
    If project_id is provided than queries only for singular requested project.
    If project_id is NOT provided than returns all accessible projects.

    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (str): ID of a user whose permissions are checked.
        project_id (int, optional): If provided than queries only one project. Defaults to None.

    Raises:
        HTTPException 401: If user has no permissions.
        HTTPException 500: If server error occures

    Returns:
        dict: Dictionarty with key `project_id` and values:
            (name, description, created_at, modified_at)
    """
    if project_id is not None:
        if check_permission(conn, user_id, project_id) is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM projects WHERE project_id = %s", (project_id,))
                result = cur.fetchone()
                return {
                    "project_id": result["project_id"],
                    "name": result["name"], 
                    "description": result["description"], 
                    "created_at": str(result["created_at"]),
                    "modified_at": str(result["modified_at"])
                    }
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    else:
        accessible_projects = select_projects_with_permissions(conn, user_id)

        if not accessible_projects:
            return {}

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects WHERE project_id IN %s", (tuple(accessible_projects),))
            
            rows = cur.fetchall()
            result = {}

            for row in rows:
                result[row["project_id"]] = {
                    "name": row["name"], 
                    "description": row["description"], 
                    "created_at": str(row["created_at"]),
                    "modified_at": str(row["modified_at"])
                    }

            return result

def check_permission(conn, user_id: str, project_id: int) -> str:
    """Checks if user have permissions to project and of which type.

    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (str): ID of a user whose permission is checked.
        project_id (int): ID of a project where permission is checked.

    Returns:
        str: If user have a permission to project and of what type (here "participant" or "owner").
        None: If user doesn't have any permissions to project.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM user_project WHERE user_id = %s AND project_id = %s", (user_id, project_id))
        result = cur.fetchone()

    if result:
        return result["permission"]
    else:
        return None

def delete_permission(conn, requester_id: str, user_id: str, project_id: int) -> None:
    """Deleting permission if user is an 'owner' or user himself is requesting for revoking his permissions
    

    Args:
        conn (psycopg2.connect): Connection to database.
        requester (str): ID of a user who is requesting for deletion.
        user_id (str): ID of a user whose permission have to be deleted.
        project_id (int): ID of a project to which user have to lose permissions.

    Raises:
        HTTPException 403: If 'owner' of a project wants to revoke his own permissions 
        or user who isn't an owner wants to revoke someone's pemissions
    """
    requester_permission = check_permission(conn, requester_id, project_id)

    if requester_permission == "owner" and requester_id == user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner can't delete his own permission")

    if requester_permission == "owner" or requester_id == user_id:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_project WHERE user_id = %s AND project_id = %s;", (user_id, project_id))
            return True
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have permission")

def delete_user(conn, user_id: str) -> None:
    """Deleting user

    Args:
        conn (psycopg2.connect): Connection to database.
        user_id (str): ID of user to be deleted.
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

def delete_project(conn, requester_id: str, project_id: int) -> None:
    """Deleting project, if requester have permissions to do so

    Args:
        conn (psycopg2.connect): Connection to database.
        requester_id (str): ID of a user who is requesting for deletion.
        project_id (int): ID of a project for deletion.

    Raises:
        HTTPException 403: If user doesn't have permission for project deleting, only owner can do so.
    """
    requester_permission = check_permission(conn, requester_id, project_id)

    if requester_permission == "owner":
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have permission")




