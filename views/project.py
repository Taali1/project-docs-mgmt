from fastapi import Request, HTTPException, status, Response, Depends

from main import app
from views.auth import auth_required, decode_token
from db.db import get_db, Project, insert_project

# TODO: POST /projects - Create project from details (name, description). Automatically gives access to created project to user, making him the owner (admin of the project)

def get_current_user(request: Request):
    token = request.session.get("token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    return decode_token(token)

@auth_required
@app.post("/project")
def post_project(project: Project, user_payload: dict = Depends(get_current_user)):
    login = user_payload["sub"]

    if not project.name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project name is required")

    with get_db() as conn:
        try:
            insert_project(conn, login, project)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return Response("Project added succesfuly", status_code=201)


# TODO: GET /projects - Get all projects, accessible for a user. Returns list of projects full info(details + documents)

# TODO: GET /project/<project_id>/info - Return project’s details, if user has access

# TODO: PUT /project/<project_id>/info - Update projects details - name, description. Returns the updated project’s info

# TODO: DELETE /project/<project_id>- Delete project, can only be performed by the projects’ owner. Deletes the corresponding  documents

# TODO: GET /project/<project_id>/documents- Return all of the project's documents

# TODO: POST /project/<project_id>/documents - Upload document/documents for a specific project

# TODO: POST /project/<project_id>/invite?user=<login> - Grant access to the project for a specific user. If the request is not coming from the owner of the project, results in error. Granting access gives participant permissions to receiving user