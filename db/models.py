from pydantic import BaseModel
from enum import Enum

from datetime import datetime

class UserRegister(BaseModel):
    user_id: str
    password: str
    repeat_password: str

class User(BaseModel):
    user_id: str
    password: str | None = None

class LoginRequest(BaseModel):
    user_id: str
    password: str

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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int