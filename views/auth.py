from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse

from functools import wraps
import os
from datetime import datetime, timedelta

from hashlib import sha1
import jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_EXPIRE_IN_MINUTES = os.getenv("TOKEN_EXPIRE_IN_MINUTES")

router = APIRouter(prefix="/auth", tags=["auth"])

def decode_token(token: str) -> str:
    try:
        if not token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token is required.")

        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expired token.")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token.")

def create_token(data: dict, expire: timedelta = timedelta(minutes=TOKEN_EXPIRE_IN_MINUTES)):
    to_encode = data.copy()
    expire_time = datetime.utcnow() + expire
    to_encode.update({"exp": expire_time})
    token = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return token

# TODO: Add autorization for 2 levels. author, participant 

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