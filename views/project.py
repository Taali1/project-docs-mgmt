from fastapi import HTTPException, status, Depends, Query
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

@app.put("project/{project_id}/info")
def update_projects_details(project_id: int, project: Project, user_payload: dict = Depends(auth_requierd)):
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")

    with get_db() as conn:
        try:
            result = update_project(conn, project)
            return result
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, e)

# TODO: Add deleting documents
@app.delete("/project/{project_id}")
def remove_project(project_id: int, user_payload: dict = Depends(auth_requierd)):
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")

    with get_db() as conn:
        delete_project(conn, user_payload["user_id"], project_id)

# TODO: GET /project/<project_id>/documents- Return all of the project's documents
@app.get("/project/{project_id}/documents")
def get_documents(project_id: int, user_payload: dict = Depends(auth_requierd)):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Function not yet implemented")


# TODO: POST /project/<project_id>/documents - Upload document/documents for a specific project

@app.post("/project/{project_id}/invite")
def invite_user(project_id: int, user: str = Query(...), user_payload: dict = Depends(auth_requierd), db = Depends(get_db)) -> JSONResponse:
    inviter_id = user_payload["sub"]


    inviter_permission = check_permission(db, inviter_id, project_id)
    if select_user(db, user) == None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User doesn't exist")
    
    
    if inviter_permission == Permission.owner.value:
        insert_permission(db, user, project_id, Permission.participant.value)
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Only owner can add user to project")
    
    return JSONResponse("User succesfully added to project", status.HTTP_201_CREATED)
