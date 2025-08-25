import pytest
from fastapi.testclient import TestClient
from main import app, SECRET_KEY, ALGORITHM
import jwt


client = TestClient(app)

def test_auth_success():
    response = client.post("/auth", params={"username": "login", "password": "password"})
    assert response.status_code == 201

def test_auth_fail():
    response = client.post("/auth", params={"username": "login", "password": ""})
    assert response.status_code == 400

    response = client.post("/auth", params={"username": "", "password": "password"})
    assert response.status_code == 400

    response = client.post("/auth", params={"username": "login", "password": ""})
    assert response.status_code == 400
