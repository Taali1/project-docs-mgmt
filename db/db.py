from fastapi import HTTPException, status

from db.models import *

from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

import os

DB_CONFIG = {
    "host": os.getenv("host"),
    "database": os.getenv("database"),
    "user": os.getenv("user"),
    "password": os.getenv("password")

}

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
    with conn.cursor() as cur:
        cur.execute("INSERT INTO users (user_id, password) VALUES (%s, %s);", (user.user_id, user.password))
        return 0

def select_user(conn, user_id: str) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, password FROM users WHERE user_id = %s;", (user_id,))
        return cur.fetchone()

def update_user(conn, user_id: str, user: User) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET password = %s WHERE user_id = %s;", (user.password, user_id))
        return 0

def insert_project(conn, user_id: str, project: Project) -> int:
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
    try:
        if check_permission(conn, user_id, project_id) == "owner":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM projects WHERE user_id = %s AND project_id = %s", (user_id, project_id))
        else:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authorized for this action")
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, e)

def select_projects_with_permissions(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT project_id
            FROM user_project
            WHERE user_id = %s
            """, 
            (user_id,))
        result = cur.fetchall()
    return (row["project_id"] for row in result)

def select_project_info(conn, user_id: str, project_id: int = None) -> dict:
    """


    """

    if not accessible_projects:
        return {}

    if project_id is not None:
        if check_permission() is not None:
            cur.execute("SELECT * FROM projects WHERE project_id = %s", (accessible_projects,))
            return cur.fetchone()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    else:
        accessible_projects = select_projects_with_permissions(conn, user_id)

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects WHERE project_id IN %s", (tuple(accessible_projects),))
            
            rows = cur.fetchall()
            result = {}

            for row in rows:
                result[row["project_id"]] = {
                    "project_id": row["project_id"], 
                    "name": row["name"], 
                    "description": row["description"], 
                    "created_at": row["created_at"], 
                    "modified_at": row["modified_at"]
                    }

            return result

def check_permission(conn, user_id: str, project_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM user_project WHERE user_id = %s AND project_id = %s", (user_id, project_id))

    result = cur.fetchone()

    if result:
        return None
    else:
        return result["permission"]

def delete_permission(conn, requester: str, user_id: str, project_id: int) -> None:
    requester_permission = check_permission(conn, requester, project_id)

    if requester_permission == "owner" or requester == user_id:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_project WHERE user_id = %s AND project_id = %s;", (user_id, project_id))
