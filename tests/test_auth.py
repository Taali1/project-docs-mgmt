import pytest
from tests.test_data import users_test_data
import jwt



@pytest.mark.parametrize("user_id, password", users_test_data)
def test_auth_success(client, mocker, user_id, password):
    mocker.patch("main.select_user", return_value=None)
    mocker.patch("main.insert_user", return_value=None)

    response = client.post("/auth", json={"user_id": user_id, "password": password, "repeat_password": password})
    
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

@pytest.mark.parametrize("user_id, password", users_test_data)
def test_login_success(client, db_connection, mocker, user_id, password, secrets):
    mocker.patch("main.select_user", return_value=None)

    with db_connection.cursor() as cur:
        cur.execute("INSERT INTO users VALUES (%s, %s)", (user_id, password))

    response = client.post("/login", json={"user_id": user_id, "password": password})

    assert response.status_code == 200
    assert response.json()["token"] is not None
    assert response.json()["expires_in_minutes"] == secrets["TOKEN_EXPIRE_IN_MINUTES"]

    token = response.json()["token"]
    payload = jwt.decode(token, secrets["SECRET_KEY"], algorithms=secrets["ALGORITHM"])
    user = payload.get("sub")
    assert user == user_id

@pytest.mark.parametrize("user_id, password", users_test_data)
def test_login_fail(client, db_connection, mocker, user_id, password):
    mocker.patch("views.auth.insert_user", return_value=None)
    
    with db_connection.cursor() as cur:
        cur.execute("INSERT INTO users VALUES (%s, %s)", (user_id, password))
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        assert cur.fetchone()["user_id"] == user_id

    response = client.post("/login", json={"user_id": "", "password": password})
    assert response.status_code == 400
    assert response.json()["detail"] == "Login is required"

    response = client.post("/login", json={"user_id": user_id, "password": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is required"

    response = client.post("/login", json={"user_id": "non-existent_user", "password": password})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

    response = client.post("/login", json={"user_id": user_id, "password": "wrong_password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    