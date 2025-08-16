from fastapi import Request

from main import app
from auth import auth_required
from db.db import Project

# TODO: POST /projects - Create project from details (name, description). Automatically gives access to created project to user, making him the owner (admin of the project)
@app.post("/project")
def post_project(requset: Request, project: Project):
    pass

# TODO: GET /projects - Get all projects, accessible for a user. Returns list of projects full info(details + documents)

# TODO: GET /project/<project_id>/info - Return project’s details, if user has access

# TODO: PUT /project/<project_id>/info - Update projects details - name, description. Returns the updated project’s info

# TODO: DELETE /project/<project_id>- Delete project, can only be performed by the projects’ owner. Deletes the corresponding  documents

# TODO: GET /project/<project_id>/documents- Return all of the project's documents

# TODO: POST /project/<project_id>/documents - Upload document/documents for a specific project

# TODO: POST /project/<project_id>/invite?user=<login> - Grant access to the project for a specific user. If the request is not coming from the owner of the project, results in error. Granting access gives participant permissions to receiving user