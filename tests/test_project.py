import pytest
import pytest_asyncio

import asyncio

from datetime import datetime, timedelta
import jwt

from db.models import Permission
from tests.test_data import user_project_test_data

def create_test_token(secrets, subject, expiration_minutes = None):
    if expiration_minutes is None:
        expire_time = datetime.utcnow() + timedelta(minutes=secrets["TOKEN_EXPIRE_IN_MINUTES"])
    else:
        expire_time = datetime.utcnow() + timedelta(minutes=expiration_minutes)
    return jwt.encode({"sub": subject, "exp": expire_time}, secrets["SECRET_KEY"], secrets["ALGORITHM"])

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_post_project_success(mocker, client, secrets, user_owner, user_participant):
    project_id = 12012
    mocker.patch("views.project.insert_project", return_value=project_id)
    token = create_test_token(secrets, user_owner["user_id"])
    project = {"name": user_owner["name"], "description": user_owner["description"]}

    response = client.post(
        "/project", 
        headers = {"Authorization": f"Bearer {token}"},
        json = project
    )

    assert response.status_code == 201
    assert response.json()["msg"] == f"Project added succesfully with ID: {project_id}"

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_post_project_fail(client, secrets, user_owner, user_participant):
    token = create_test_token(secrets, user_owner["user_id"])
    project = {"name": "", "description": user_owner["description"]}

    response = client.post(
        "/project", 
        headers = {"Authorization": f"Bearer {token}"},
        json = project
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Project name is required"

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_get_all_projects(client, mocker, secrets, user_owner, user_participant):
    mocker.patch(
        "views.project.select_project_info", 
        return_value = {"project_id": {
                "name": user_owner["name"], 
                "description": user_owner["description"]
            }})
    mocker.patch("views.project.get_s3_documents_list", return_value = ["file.pdf"])

    token = create_test_token(secrets, user_owner["user_id"])

    response = client.get(
        "/projects",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert isinstance(response.json(), dict)
    assert 0 < len(response.json()) < 2

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_get_project(client, mocker, secrets, user_owner, user_participant):
    project = {
            "project_id": 121,
            "name": user_owner["name"],
            "description": user_owner["description"], 
            "created_at": "12.12.2012 12:12",
            "modified_at": "12.12.2012 12:12",
            "documents": ["doc.pdf"]
            }
    mocker.patch("views.project.select_project_info", return_value = project)    
    mocker.patch("views.project.check_permission", return_value = "owner")
    mocker.patch("views.project.get_s3_documents_list", return_value = ["doc.pdf"])
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    response = client.get(
        f"/projects/{project['project_id']}",
        headers = {"Authorization": f"Bearer {token}"}
    )

    response_project = response.json()[str(project["project_id"])]
    project.pop("project_id")
    assert response_project == project

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_update_projects_details(client, mocker, user_owner, user_participant, secrets):
    project_id = 121
    project = {
        "name": user_owner["name"],
        "description": user_owner["description"]
    }
    mocker.patch("views.project.update_project", return_value = project)    
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    response = client.put(
        f"/projects/{project_id}",
        headers = {"Authorization": f"Bearer {token}"},
        json = project
    )

    assert response is not None
    assert response.status_code == 202
    assert response.json()["msg"] == "Project details updated succesfully"

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_remove_project(client, mocker, secrets, user_owner, user_participant):
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    mocker.patch("views.project.delete_project", return_value = None)
    mocker.patch("views.project.delete_s3_folder", return_value = None)
    mocker.patch("views.project.check_permission", return_value = "owner")
    
    project_id = 111

    response = client.delete(
        f"/projects/{project_id}",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 204

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_invite_user_success(db_connection, client, mocker, user_owner, secrets, user_participant):
    mocker.patch("views.project.check_permission", return_value = Permission.owner.value)
    mocker.patch("views.project.select_user", return_value = "user")
    mocker.patch("views.project.insert_permission", return_value = None)

    project_id = 101

    user_id = user_owner["user_id"]
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    response = client.post(
        f"/projects/{project_id}/invite?user={user_id}",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 201
    assert response.json() == "User succesfully added to project"

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_invite_user_fail(client, mocker, user_owner, secrets, user_participant):
    mocker.patch("views.project.check_permission", return_value = Permission.participant.value)
    mocker.patch("views.project.select_user", return_value = "user")
    mocker.patch("views.project.insert_permission", return_value = None)
    project_id = 101

    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    response = client.post(
        f"/projects/{project_id}/invite?user={user_owner['user_id']}",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 401
    assert response.json()['detail'] == "Only owner can add user to project"