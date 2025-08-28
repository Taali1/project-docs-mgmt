import pytest
from tests.test_data import users_test_data


@pytest.mark.parametrize("user_id, password", users_test_data)
def test_auth_success(client, mocker, user_id, password):
    mocker.patch("main.select_user", return_value=None)
    mocker.patch("main.insert_user", return_value=None)

    payload = {
        "user_id": user_id,
        "password": password,
        "repeat_password": password
    }

    response = client.post("/auth", json=payload)
    
    assert response.status_code == 201
    assert response.text == "Registerd succesfuly"

@pytest.mark.parametrize("user_id, password", users_test_data)
def test_auth_fail(client, mocker, user_id, password):
    mocker.patch("main.select_user", return_value=None)
    mocker.patch("main.insert_user", return_value=None)

    response = client.post("/auth", json={"user_id": user_id, "password": "", "repeat_password": password})
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is required"

    response = client.post("/auth", json={"user_id": "", "password": password, "repeat_password": password})
    assert response.status_code == 400
    assert response.json()["detail"] == "Login is required"

    response = client.post("/auth", json={"user_id": user_id, "password": password, "repeat_password": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Repeat password is required"

    response = client.post("/auth", json={"user_id": user_id, "password": password + "_changed", "repeat_password": password})
    assert response.status_code == 400
    assert response.json()["detail"] == "Password and Repeat password are not the same"




