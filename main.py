from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

from views.auth import *
from views.project import *
from views.document import *
