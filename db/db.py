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
    project_id: int
    title: str
    description: str | None = None
    created_at: datetime
    modified_at: datetime

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
        cur.execute(f"SELECT login, password FROM users WHERE login = {login};")
        return cur.fetchall()

def update_user(conn, login: str, user: User) -> None:
    with conn.cursor() as cur:
        cur.execute(f"UPDATE users SET password = {user.password} WHERE login = {login};")
        return 0

def insert_project(conn, login: str, project: Project, user_project: User_Project) -> None:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.cursor() as cur:
        if project.description:
            cur.execute(f"""
                INSERT INTO projects VALUES (
                {project.project_id}, 
                {project.title}, 
                {project.description},
                {current_time},
                {current_time}
                );""")
        else:
            cur.execute(f"""
                INSERT INTO projects VALUES (
                {project.project_id}, 
                {project.title}, 
                {current_time},
                {current_time}
                );""")
        
        cur.execute(f"INSERT INTO user_project VALUES ({login}, {project.project_id}, {user_project.permission});")
        
        return 0

def update_project(conn, project: Project):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn.cursor() as cur:
        cur.execute(f"""
        UPDATE projects SET 
        {"title = " + project.title + "," if project.title else ""}
        {"description = " + project.description + "," if project.description else ""}
        modified_at = {current_time} 
        WHERE project_id = {project.project_id}
        ;""")

def insert_permission(conn, login: str, project_id: int, permission: Permission) -> None:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO user_project VALUES ({login}, {project_id}, {permission});", (login, project_id, permission))
        return 0

def delete_permission(conn, login: str, project_id: int):
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM user_project WHERE user_id = {login} AND project_id = {project_id};")
        return 0
