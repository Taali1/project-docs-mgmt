from fastapi import HTTPException, status, Response, Depends
from fastapi.responses import JSONResponse

from main import app
from views.auth import auth_requierd
from db.db import *


@app.post("/project")
def post_project(project: Project, user_payload: dict = Depends(auth_requierd)) -> JSONResponse:
    user_id = user_payload["sub"]

    if not project.name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project name is required")

    with get_db() as conn:
        try:
            project_id = insert_project(conn, user_id, project)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return JSONResponse(
        {
            "msg": f"Project added succesfully with ID: {project_id}", 
            "project_id": project_id
        },
        status_code=201)


# TODO: Add documents in Response
@app.get("/projects")
def get_all_projects(user_payload: dict = Depends(auth_requierd)) -> JSONResponse:
    with get_db() as conn:
        try:
            result = select_project_info(conn, user_payload["sub"])
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
        return JSONResponse(result, status_code=200)

# TODO: Add documents in Response
@app.get("/project/{project_id}/info")
def get_project_info(project_id: int, user_payload: dict = Depends(auth_requierd)):
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")
    
    with get_db() as conn:
        try:
            project_info = select_project_info(conn, user_payload["sub"], project_id=project_id)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    return JSONResponse({
        project_info["project_id"]: 
            {
                "name": project_info["name"], 
                "description": project_info["description"], 
                "created_at": project_info["created_at"], 
                "modified_at": project_info["modified_at"]
            }  
        }, 
        status_code=200
    )

# TODO: PUT /project/<project_id>/info - Update projects details - name, description. Returns the updated project’s info

# TODO: DELETE /project/<project_id>- Delete project, can only be performed by the projects’ owner. Deletes the corresponding  documents

# TODO: GET /project/<project_id>/documents- Return all of the project's documents

# TODO: POST /project/<project_id>/documents - Upload document/documents for a specific project

# TODO: POST /project/<project_id>/invite?user=<user_id> - Grant access to the project for a specific user. If the request is not coming from the owner of the project, results in error. Granting access gives participant permissions to receiving user