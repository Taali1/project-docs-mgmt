from pydantic import BaseModel
from datetime import datetime
from enum import Enum

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

class User(BaseModel):
    login: str
    password: str | None = None
class Permission(str, Enum):
    owner: str = "owner"
    participant: str = "participant"
class User_Project(BaseModel):
    user_id: str
    project_id: int
    permission: Permission
class Project(BaseModel):
    project_id: int | None = None
    name: str
    description: str | None = None
    created_at: datetime | None = None
    modified_at: datetime  | None = None

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
        cur.execute("INSERT INTO users (login, password) VALUES (%s, %s);", (user.login, user.password))
        return 0

def select_user(conn, login: str) -> tuple:
    with conn.cursor() as cur:
        cur.execute("SELECT login, password FROM users WHERE login = %s;", (login))
        return cur.fetchall()

def update_user(conn, login: str, user: User) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET password = %s WHERE login = %s;", (user.password, login))
        return 0

def insert_project(conn, login: str, project: Project) -> None:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.cursor() as cur:
        if project.description:
            cur.execute("""
                INSERT INTO projects (title, description, created_at)
                VALUES (%s, %s,%s) 
                RETURNING project_id;
                """,
                (project.name, project.description, current_time))
        else:
            cur.execute("""
                INSERT INTO projects (title, created_at)
                VALUES (%s, %s) 
                RETURNING project_id;
                """,
                (project.name, current_time))

        project_id = cur.fetchone()["project_id"]
        
        cur.execute("INSERT INTO user_project (login, project_id, permission) VALUES (%s, %s, %s);", (login, project_id, Permission.owner.value))

def update_project(conn, project: Project):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.cursor() as cur:
        fields = []
        values = []

        if project.name:
            fields.append("title = %s")
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

def delete_permission(conn, login: str, project_id: int):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM user_project WHERE user_id = %s AND project_id = %s;", (login, project_id))
        return 0
