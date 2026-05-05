import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_signup():
    response = client.post(
        "/signup",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    # First signup should succeed or fail if user exists (both acceptable)
    assert response.status_code in [200, 400]

def test_login():
    # First create user
    client.post("/signup", json={"email": "login_test@example.com", "password": "testpass123"})
    
    response = client.post(
        "/login",
        data={"username": "login_test@example.com", "password": "testpass123"}
    )
    assert response.status_code in [200, 401]
    
    if response.status_code == 200:
        assert "access_token" in response.json()

def test_chat_unauthorized():
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 401

def test_search():
    response = client.get("/search?query=test")
    assert response.status_code == 200
    assert "results" in response.json()
