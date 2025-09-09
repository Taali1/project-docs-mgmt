from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from views import auth, document, project


from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.include_router(auth.router)
app.include_router(project.router)
app.include_router(document.router)