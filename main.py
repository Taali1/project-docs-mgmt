from fastapi import FastAPI

from views.auth import router as router_auth
from views.project import router as router_project
from views.document import router as router_document


app = FastAPI()

if __name__ == "__main__":
    app.include_router(router_auth)
    app.include_router(router_project)
    app.include_router(router_document)