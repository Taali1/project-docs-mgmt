from fastapi import Request, HTTPException, status, Response, Depends

from main import app
from views.auth import auth_requierd
from db.db import *


@app.post("/project")
def post_project(project: Project, user_payload: dict = Depends(auth_requierd)):
    user_id = user_payload["sub"]

    if not project.name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project name is required")

    with get_db() as conn:
        try:
            insert_project(conn, user_id, project)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return Response("Project added succesfuly", status_code=201)


# TODO: Add documents in Response
@app.get("/projects")
def get_all_projects(user_payload: dict = Depends(auth_requierd)):
    with get_db() as conn:
        try:
            result = select_project_info(conn, "login")
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
        return Response(result)

# TODO: GET /project/<project_id>/info - Return project’s details, if user has access
@app.get("/project/{project_id}/info")
def get_project_info(project_id: int, user_payload: dict = Depends(auth_requierd)):
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")
    
    with get_db() as conn:
        try:
            pass
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

# TODO: PUT /project/<project_id>/info - Update projects details - name, description. Returns the updated project’s info

# TODO: DELETE /project/<project_id>- Delete project, can only be performed by the projects’ owner. Deletes the corresponding  documents

# TODO: GET /project/<project_id>/documents- Return all of the project's documents

# TODO: POST /project/<project_id>/documents - Upload document/documents for a specific project

# TODO: POST /project/<project_id>/invite?user=<user_id> - Grant access to the project for a specific user. If the request is not coming from the owner of the project, results in error. Granting access gives participant permissions to receiving user