from fastapi import HTTPException, status, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

import os
from datetime import datetime, timedelta

from main import app 
from db.db import select_user, get_db, insert_user, TokenResponse
from db.models import *

import jwt

# Getting environmental variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_EXPIRE_IN_MINUTES = int(os.getenv("TOKEN_EXPIRE_IN_MINUTES"))
TIME_ZONE_UTC_OFFSET = int(os.getenv("TIME_ZONE_UTC_OFFSET"))

# Creating scheams for authentication
auth_scheme = HTTPBearer()  

def auth_requierd(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Checks if user is logged in
    
    Args:
        credentials (HTTPAuthorizationCredentials): The parsed Authorization header (scheme + credentials). 

    Returns:
        dict: The decoded JWT payload (must contain a "sub" field).

    Raises:
        HTTPException: 
            - 401 if the token is missing "sub"
            - 401 if the token is expired
            - 401 if the token is invalid
    
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user = payload.get("sub")

        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token - missing subject")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expired token")

    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


def create_token(user_id: dict, expire: timedelta = timedelta(minutes=TOKEN_EXPIRE_IN_MINUTES)) -> str:
    """Creates token for user session from it's user_id and encodes it by using choosen algorithm and secret key using JWT

    Args:
        user_id (str): ID of a user that requests a token
        expire (timedelta): Difference between two timestamps. Optional with TOKEN_EXPIRE_IN_MINUTES default

    Returns:
        str: Encoded JWT token that contains:
            "sub": Username
            "exp": Expiration timestamp
    """
    to_encode = {"sub": user_id}
    expire_time = datetime.utcnow() + expire
    to_encode.update({"exp": expire_time})
    token = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return token

@app.post("/auth")
def post_user(user: UserRegister, db = Depends(get_db)) -> Response:
    """Registers user to data base
    
    Args:
        user (User): Pydantic model, contains 'login' (str) and 'password' (str)
        request: (Request): FastAPI request object, used to access user's session data 
    
    Returns:
        Response: FastAPI Response object with status code 201 (Created)

    Raises:
        HTTPException 400: If 'login', 'password' or 'repeat_password' is not provided or 'password' and 'repeat_password' are not the same
        HTTPException 500: If theres a database error
    """
    if not user.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Login is required")
    if not user.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password is required")
    if not user.repeat_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Repeat password is required")
    if user.password != user.repeat_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password and Repeat password are not the same")
    

    with db as conn:
        result = select_user(conn, user.user_id)
        if result:
            raise HTTPException(status.HTTP_409_CONFLICT, "User with the same username already in registered")

        try:
            insert_user(conn, user)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return Response("Registerd succesfuly", status.HTTP_201_CREATED)

@app.post("/login", response_model=TokenResponse)
def post_login(credentials: LoginRequest, db = Depends(get_db)) -> Response:
    """
    Logs in user and creates JWT session token

    Args:
        request: (Request): FastAPI request object, used to access user's session data
        user (User): Pydantic model, contains 'user_id' (str) and 'password' (str)

    Returns:
        Response: FastAPI Response object with 202 status (Accepted)

    Raises:
        HTTPException 400: If 'login' or 'password' are not provided
    """
    if not credentials.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Login is required")
    if not credentials.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password is required")

    with db as conn:
        user = select_user(conn, credentials.user_id)
        
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        
        if credentials.password != user.password:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = create_token(credentials.user_id)

    return JSONResponse({
        "token": token,
        "expires_in_minutes": TOKEN_EXPIRE_IN_MINUTES
    }, 
        status.HTTP_200_OK
    )
        