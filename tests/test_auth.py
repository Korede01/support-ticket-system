import pytest
from uuid import UUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserLogin

@pytest.mark.anyio
async def test_signup_and_login_success(async_client: AsyncClient):
    # Signup new user
    signup_data = {"email": "test@example.com", "password": "strongpass", "full_name": "Test UserName"}
    resp = await async_client.post("/auth/signup", json=signup_data)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == signup_data["email"]
    assert UUID(body["id"])  # valid UUID
    assert body["role"] == "user"

    # Login with created user
    login_data = {"email": "test@example.com", "password": "strongpass"}
    resp = await async_client.post("/auth/login", json=login_data)
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.anyio
async def test_signup_duplicate(async_client: AsyncClient):
    # Create initial user
    data = {"email": "dup@example.com", "password": "strongpass", "full_name": "Duplicate User"}
    resp = await async_client.post("/auth/signup", json=data)
    assert resp.status_code == 201

    # Attempt to signup again
    resp = await async_client.post("/auth/signup", json=data)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "User already registered"

@pytest.mark.anyio
async def test_login_invalid(async_client: AsyncClient):
    # Login with nonexistent user
    login_data = {"email": "noone@example.com", "password": "nopass"}
    resp = await async_client.post("/auth/login", json=login_data)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"

@pytest.mark.anyio
async def test_refresh_and_logout(async_client: AsyncClient):
    # Signup & login
    signup = {"email": "refresh@example.com", "password": "strongpass", "full_name": "Refresh User"}
    await async_client.post("/auth/signup", json=signup)
    login = {"email": signup["email"], "password": signup["password"]}
    resp = await async_client.post("/auth/login", json=login)
    tokens = resp.json()
    refresh_token = tokens["refresh_token"]

    # Refresh tokens
    resp = await async_client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != refresh_token

    # Logout (revoke) new refresh_token
    resp = await async_client.post("/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert resp.status_code == 200
    assert resp.json()["msg"] == "Successfully logged out"

    # Using revoked refresh_token should fail
    resp = await async_client.post("/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Refresh token has been revoked"