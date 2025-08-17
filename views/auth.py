from fastapi import HTTPException, status, Request, Response

from typing import Any, Dict
from functools import wraps
import os
from datetime import datetime, timedelta

from main import app 
from db.db import *

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
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token is required, please log in")

        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expired token, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

def create_token(data: dict, expire: timedelta = timedelta(minutes=TOKEN_EXPIRE_IN_MINUTES)) -> str:
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
    """
    Checks authorization for user

    Args:
        request: (Request): FastAPI request object, used to access user's session data 

    Raises:
        HTTPException 401: If user is not logged in or token is invalid
    """
    @wraps(func)
    def wrapper(*args, request: Request, **kwargs):
        token = request.session.get("token")

        if not token:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
        
        try:
            decode_token(token)
        except HTTPException:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Provided token is invalid")

        return func(*args, request=request, **kwargs)
    return wrapper

@app.post("/auth")
def post_user(user: User, repeat_password: str) -> Response:
    """
    Registers user to data base
    
    Args:
        user (User): Pydantic model, contains 'login' (str) and 'password' (str)
        request: (Request): FastAPI request object, used to access user's session data 
    
    Returns:
        Response: FastAPI Response object with status code 201 (Created)

    Raises:
        HTTPException 400: If 'login', 'password' or 'repeat_password' is not provided or 'password' and 'repeat_password' are not the same
        HTTPException 500: If theres a database error
    """
    if not user.login:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Login is required")
    if not user.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password is required")
    if not repeat_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Repeat password is required")
    if user.password != repeat_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Password and Repeat password are not the same")

    with get_db() as conn:
        try:
            insert_user(conn, user)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return Response("Registerd succesfuly", status_code=201)

@app.post("/login")
def post_login(request: Request, user: User) -> Response:
    """
    Logs in user and creates JWT session token

    Args:
        request: (Request): FastAPI request object, used to access user's session data
        user (User): Pydantic model, contains 'login' (str) and 'password' (str)

    Returns:
        Response: FastAPI Response object with 202 status (Accepted)

    Raises:
        HTTPException 400: If 'login' or 'password' are not provided
        HTTPException 409: If user is already logged in
    """
    if not user.login:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Login is required")
    if not user.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password is required")
    if request.session.get("token"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Already logged in")

    token = create_token({"sub": user.login})
    request.session["token"] = token

    user_tokens[user.login] = token

    return Response("Logged successfuly", status_code=202)
        