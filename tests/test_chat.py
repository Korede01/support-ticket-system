import json
import pytest
from fastapi.testclient import TestClient
from uuid import UUID
from app.schemas.message import MessageCreate, WSMessage
from app.schemas.user import UserCreate, UserLogin

@pytest.fixture
def client(app_override):
    # sync TestClient for WebSocket testing
    return TestClient(app_override)

@pytest.fixture
def user_and_ticket(client):
    # 1. Sign up a user
    signup = {"email": "chatuser@example.com", "password": "strongpass", "full_name": "Chat UserName"}
    res = client.post("/auth/signup", json=signup)
    assert res.status_code == 201

    # 2. Login the user
    login = {"email": signup["email"], "password": signup["password"]}
    res = client.post("/auth/login", json=login)
    assert res.status_code == 200
    token = res.json()["access_token"]

    # 3. Create a ticket
    headers = {"Authorization": f"Bearer {token}"}
    ticket_data = {"title": "Chat Test", "description": "Testing chat", "category": "support", "type": "question"}
    res = client.post("/api/v1/users/tickets", json=ticket_data, headers=headers)
    assert res.status_code == 200
    ticket = res.json()

    return token, ticket["id"]

def test_websocket_chat_flow(client, user_and_ticket):
    token, ticket_id = user_and_ticket
    # Open WebSocket connection
    with client.websocket_connect(f"/ws/tickets/{ticket_id}?token={token}") as ws:
        # Send a chat message
        incoming = MessageCreate(ticket_id=UUID(ticket_id), content="Hello CSR").json()
        ws.send_text(incoming)
        # Receive broadcasted message
        data = ws.receive_text()
        payload = json.loads(data)

        # Validate message structure
        assert payload["ticket_id"] == ticket_id
        assert payload["content"] == "Hello CSR"
        assert UUID(payload["sender_id"])  # valid sender UUID
        assert "timestamp" in payload

def test_websocket_unauthorized(client):
    # Attempt to connect with invalid token
    fake_ticket_id = "00000000-0000-0000-0000-000000000000"
    with pytest.raises(Exception):
        client.websocket_connect(f"/ws/tickets/{fake_ticket_id}?token=invalidtoken")
