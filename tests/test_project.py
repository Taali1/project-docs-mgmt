import pytest

from io import BytesIO
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


@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_post_project_success(mocker, client, secrets, user_owner, user_participant):
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


@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_post_project_fail(client, secrets, user_owner, user_participant):
    token = create_test_token(secrets, user_owner["user_id"])
    project = {"name": "", "description": user_owner["description"]}

    response = client.post(
        "/project", 
        headers = {"Authorization": f"Bearer {token}"},
        json = project
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Project name is required"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_get_all_projects(client, mocker, secrets, user_owner, user_participant):
    mocker.patch(
        "views.project.select_project_info", 
        return_value = {"project_id": {
                "name": user_owner["name"], 
                "description": user_owner["description"]
            }})
    token = create_test_token(secrets, user_owner["user_id"])

    response = client.get(
        "/projects",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert isinstance(response.json(), dict)
    assert 0 < len(response.json()) < 2

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_get_project_info(client, mocker, secrets, user_owner, user_participant):
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
        f"/project/{project['project_id']}/info",
        headers = {"Authorization": f"Bearer {token}"}
    )

    response_project = response.json()[str(project["project_id"])]
    project.pop("project_id")
    assert response_project == project


@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def update_projects_details(client, mocker, user_owner, user_participant, secrets):
    project_id = 121
    project = {
        "name": user_owner["name"],
        "description": user_owner["description"]
    }
    mocker.patch("views.project.update_project", return_value = project)    
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    response = client.put(
        f"/project/{project['project_id']}/info",
        headers = {"Authorization": f"Bearer {token}"},
        json = {project}
    )

    assert response == project

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_remove_project(client, mocker, secrets, user_owner, user_participant):
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    mocker.patch("views.project.delete_project", return_value = None)
    mocker.patch("views.project.delete_s3_folder", return_value = None)
    mocker.patch("views.project.check_permission", return_value = "owner")
    project_id = 111

    response = client.delete(
        f"/project/{project_id}",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 204
    assert response.json() == "Deleted project"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_get_project_documents_success(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.project.check_permission", return_value = "owner")
    mocker.patch("views.project.get_s3_documents_list", return_value = ["test_file.pdf"])
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    project_id = 111

    response = client.get(
        f"/project/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 200
    assert response.json() == ['test_file.pdf']

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_get_project_documents_fail(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.project.check_permission", return_value = None)
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    project_id = 111

    response = client.get(
        f"/project/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 401
    assert response.json()['detail'] == "Unauthorized"


@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_upload_project_documents_success(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.project.check_permission", return_value = None)  
    mocker.patch("views.project.upload_s3_file", return_value = None)
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    upload_files = ["test_file.txt", "test_image.png"]
    project_id = 111

    response = client.post(
        f"/project/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"},
        json = upload_files
    )

    assert response is not None
    assert response.status_code == 200
    assert response.json() == f"Files uploaded successfully: {upload_files}"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_upload_project_documents_success(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.project.check_permission", return_value = None)
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    project_id = 111
    files = {"files": ("test.txt", BytesIO(b"file_content"), "text/plain")}

    response = client.post(
        f"/project/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"},
        files = files
    )

    assert response is not None
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_invite_user_fail(db_connection, client, mocker, user_owner, secrets, user_participant):
    mocker.patch("views.project.check_permission", return_value = Permission.owner.value)
    with db_connection.cursor() as cur:
        cur.execute("INSERT INTO users (user_id, password) VALUES (%s, %s) RETURNING user_id", (user_owner["user_id"], user_owner["password"]))
        user = cur.fetchone()
        assert user_owner["user_id"] == user["user_id"]
        cur.execute("""
            INSERT INTO projects (name, description, created_at, modified_at) 
            VALUES (%s, %s, %s, %s) 
            RETURNING project_id
        """, 
        (
            user_owner["name"], 
            user_owner["description"],
            "12.12.2012 12:12", 
            "12.12.2012 12:12"
        ))
        project_id = cur.fetchone()["project_id"]
        assert project_id

    user_id = user_owner["user_id"]
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    response = client.post(
        f"/project/{project_id}/invite?user={user_id}",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response.json() == "User succesfully added to project"

@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
def test_invite_user_fail(db_connection, client, mocker, user_owner, secrets, user_participant):
    mocker.patch("views.project.select_project_info", return_value = Permission.participant.value)
    with db_connection.cursor() as cur:
        cur.execute("INSERT INTO users (user_id, password) VALUES (%s, %s)", (user_owner["user_id"], user_owner["password"]))
        cur.execute("""
            INSERT INTO projects (name, description, created_at, modified_at) 
            VALUES (%s, %s, %s, %s) 
            RETURNING project_id
        """, 
        (
            user_owner["name"], 
            user_owner["description"],
            "12.12.2012 12:12", 
            "12.12.2012 12:12"
        ))
        project_id = cur.fetchone()["project_id"]

    user_id = user_owner["user_id"]
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])

    client.post(
        f"/project/{project_id}/invite?user={user_id}",
        headers = {"Authorization": f"Bearer {token}"},
        json = {"user_id": user_owner["user_id"], "project_id": project_id}
    )