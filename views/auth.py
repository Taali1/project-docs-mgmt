from fastapi import APIRouter, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse

from typing import Any, Dict
from functools import wraps
import os
from datetime import datetime, timedelta

from main import app 
from db.db import *

from hashlib import sha1
import jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_EXPIRE_IN_MINUTES = int(os.getenv("TOKEN_EXPIRE_IN_MINUTES"))
user_tokens = {}

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes token for verifiction if user is logged in

    Args:
        token (str): JWT token from user session

    Returns:
        Dict[str, Any]: Dictionary contains decoded payload 

    Rasises:
        HTTPException: If the token is missing, expired, or invalid.
    """

    try:
        if not token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token is required, but is required.")

        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expired token.")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token.")

def create_token(data: dict, expire: timedelta = timedelta(minutes=TOKEN_EXPIRE_IN_MINUTES)) -> dict:
    """
    Creates token for user session from it's username and encodes it by using choosen algorithm and secret key using JWT

    Args:
        data (dict): Dictionary with  username as "sub" key
        expire (timedelta): Difference between two timestamps. Optional with TOKEN_EXPIRE_IN_MINUTES default

    Returns:
        str: Encoded JWT token that contains:
            "sub": Username
            "exp": Expiration timestamp
    """
    to_encode = data.copy()
    expire_time = datetime.utcnow() + expire
    to_encode.update({"exp": expire_time})
    token = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return token

def auth_required(func):
    @wraps(func)
    def wrapper(*args, request: Request, **kwargs):
        token = request.session.get("token")

        if not token:
            return RedirectResponse("/login", status_code=303)
        
        try:
            decode_token(token)
        except HTTPException:
            return RedirectResponse("/login", status_code=303)

        return func(*args, request=request, **kwargs)
    return wrapper

@app.post("/auth")
def regiser_user(user: User, repeat_password: str):
    if user.password != repeat_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Password and Repeat Password are not the same")

    with get_db() as conn:
        try:
            insert_user(conn, user)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



        