from fastapi import HTTPException, status, Depends, Query, APIRouter, Path, File, UploadFile, Response
from fastapi.responses import JSONResponse

import asyncio

from views.auth import auth_requierd
from db.db import *
from views.document import get_s3_documents_list, upload_s3_file, delete_s3_folder, check_file_extension

router = APIRouter(tags=["Projects"])

@router.post("/project")
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
@router.get("/projects")
async def get_all_projects(user_payload: dict = Depends(auth_requierd)) -> JSONResponse:
    with get_db() as conn:
        try:
            result = select_project_info(conn, user_payload["sub"])
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

    for project_id in result:
        documents = await get_s3_documents_list(project_id)
        result[project_id]["documents"] = documents
    return JSONResponse(result, status_code=200)

@router.get("/projects/{project_id}")
async def get_project(project_id: int, user_payload: dict = Depends(auth_requierd)):
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")
    with get_db() as conn:
        try:
            user_perm = check_permission(conn, user_payload["sub"], project_id)
            if user_perm is not None:
                project_info = select_project_info(conn, user_payload["sub"], project_id=project_id)
                documents_list = await get_s3_documents_list(project_id)
            else:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    
    return JSONResponse({
        project_info["project_id"]: 
            {
                "name": project_info["name"], 
                "description": project_info["description"], 
                "created_at": project_info["created_at"], 
                "modified_at": project_info["modified_at"],
                "documents": documents_list
            }  
        }, 
        status_code=200
    )

@router.put("projects/{project_id}")
def update_projects_details(project_id: int, project: Project, user_payload: dict = Depends(auth_requierd)):
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")

    with get_db() as conn:
        try:
            result = update_project(conn, project)
            return JSONResponse({'msg': 'Project details updated succesfully', 'update': result}, status.HTTP_202_ACCEPTED)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, e)

@router.delete("/projects/{project_id}")
async def remove_project(project_id: int, user_payload: dict = Depends(auth_requierd)) -> JSONResponse:
    if not project_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project ID is required")

    with get_db() as conn:
        user_permission = check_permission(conn, user_payload["sub"], project_id)

        if user_permission == Permission.owner.value:
            delete_project(conn, user_payload["sub"], project_id)

            await delete_s3_folder(project_id)
        
            return JSONResponse("Deleted project", status.HTTP_204_NO_CONTENT)
        else:
            raise HTTPException("Unauthorized", status.HTTP_401_UNAUTHORIZED)

@router.get("/projects/{project_id}/documents")
async def get_project_documents(project_id: str = Path(...), user_payload: dict = Depends(auth_requierd)) -> JSONResponse:
    user_id = user_payload["sub"]
    project_id = int(project_id)
    with get_db() as conn:
        user_premission = check_permission(conn, user_id, project_id)
    
    if user_premission is not None:
        response = await get_s3_documents_list(project_id)
        return JSONResponse(response, status.HTTP_200_OK)
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")

@router.post("/projects/{project_id}/documents")
async def upload_project_documents(files: list[UploadFile] = File(...), project_id: str = Path(...), user_payload: dict = Depends(auth_requierd)) -> JSONResponse:
    
    await check_file_extension(files)
    
    with get_db() as conn:
        user_permission = check_permission(conn, user_payload["sub"], project_id)
    
    if user_permission is not None:
        uploaded_files = await asyncio.gather(*(upload_s3_file(file) for file in files))
        return JSONResponse(f"Files uploaded successfully: {uploaded_files}", status.HTTP_200_OK)
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")

@router.post("/projects/{project_id}/invite")
async def invite_user(project_id: int, user: str = Query(...), user_payload: dict = Depends(auth_requierd), db = Depends(get_db)) -> JSONResponse:
    inviter_id = user_payload["sub"]

    inviter_permission = check_permission(db, inviter_id, project_id)
    if select_user(db, user) == None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User doesn't exist")
    
    if inviter_permission == Permission.owner.value:
        insert_permission(db, user, project_id, Permission.participant.value)
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Only owner can add user to project")
    
    return JSONResponse("User succesfully added to project", status.HTTP_201_CREATED)
