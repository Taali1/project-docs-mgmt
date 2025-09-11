import pytest
import pytest_asyncio

from io import BytesIO

from tests.test_data import user_project_test_data
from tests.test_project import create_test_token

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_get_project_documents_success(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.document.check_permission", return_value = "owner")
    mocker.patch("views.document.get_s3_documents_list", return_value = ["test_file.pdf"])
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    project_id = 111

    response = client.get(
        f"/projects/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 200
    assert response.json() == ['test_file.pdf']

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_get_project_documents_fail(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.document.check_permission", return_value = None)
    mocker.patch("views.document.get_s3_documents_list", return_value = ["test_file.pdf"])
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    project_id = 111

    response = client.get(
        f"/projects/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"}
    )

    assert response is not None
    assert response.status_code == 401
    assert response.json()['detail'] == "Unauthorized"

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_upload_project_documents_success(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.document.check_permission", return_value = "owner")  
    mocker.patch("views.document.upload_s3_file", return_value = "test_file.pdf")
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    file = [
    ("files", ("test_file.pdf", b"fake content", "application/pdf"))
    ]
    project_id = 111

    response = client.post(
        f"/projects/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"},
        files = file
    )

    assert response is not None
    assert response.status_code == 200
    assert response.json() == f"Files uploaded successfully: ['{file[0][1][0]}']"

@pytest.mark.asyncio
@pytest.mark.parametrize("user_owner, user_participant", user_project_test_data)
async def test_upload_project_documents_fail(client, mocker, secrets, user_owner, user_participant):
    mocker.patch("views.document.check_permission", return_value = None)
    token = create_test_token(secrets=secrets, subject=user_owner["user_id"])
    project_id = 111
    files = {"files": ("test.pdf", BytesIO(b"file_content"), "text/plain")}

    response = client.post(
        f"/projects/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"},
        files = files
    )

    assert response is not None
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

    files = {"files": ("test.txt", BytesIO(b"file_content"), "text/plain")}

    response = client.post(
        f"/projects/{project_id}/documents",
        headers = {"Authorization": f"Bearer {token}"},
        files = files
    )

    assert response is not None
    assert response.status_code == 406