import pytest
from uuid import UUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate

@pytest.mark.anyio
async def test_user_ticket_crud(async_client: AsyncClient):
    # Sign up user
    signup = {"email": "user1@example.com", "password": "strongpass", "full_name": "User OneName"}
    res = await async_client.post("/auth/signup", json=signup)
    assert res.status_code == 201
    # Login user
    login = {"email": signup["email"], "password": signup["password"]}
    res = await async_client.post("/auth/login", json=login)
    tokens = res.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Create a ticket without any CSRs -> unassigned
    ticket_data = {"title": "Help", "description": "Need help", "category": "general", "type": "issue"}
    res = await async_client.post("/api/v1/users/tickets", json=ticket_data, headers=headers)
    assert res.status_code == 200
    ticket = res.json()
    assert ticket["title"] == ticket_data["title"]
    ticket_id = ticket["id"]
    assert ticket.get("assigned_to_id") is None

    # List my tickets
    res = await async_client.get("/api/v1/users/tickets", headers=headers)
    assert res.status_code == 200
    tickets = res.json()
    assert any(t["id"] == ticket_id for t in tickets)

    # Get ticket detail
    res = await async_client.get(f"/api/v1/users/tickets/{ticket_id}", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == ticket_id

@pytest.mark.anyio
async def test_csr_ticket_management(async_client: AsyncClient, db_session: AsyncSession):
    # Create CSR directly in DB
    pwd = get_password_hash("csrpass")
    csr = User(email="csr@example.com", hashed_password=pwd, full_name="CSR Person", role=UserRole.CSR)
    db_session.add(csr)
    await db_session.commit()
    await db_session.refresh(csr)

    # Login CSR to get token
    login_data = {"email": csr.email, "password": "csrpass"}
    res = await async_client.post("/auth/login", json=login_data)
    tokens = res.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Ensure at least one ticket exists: create as user
    # Sign up another user
    signup = {"email": "user2@example.com", "password": "strongpass", "full_name": "User TwoName"}
    await async_client.post("/auth/signup", json=signup)
    login2 = {"email": signup["email"], "password": signup["password"]}
    res2 = await async_client.post("/auth/login", json=login2)
    tokens2 = res2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    ticket_data = {"title": "Issue2", "description": "Issue description", "category": "tech", "type": "bug"}
    res_ticket = await async_client.post("/api/v1/users/tickets", json=ticket_data, headers=headers2)
    ticket = res_ticket.json()
    ticket_id = ticket["id"]

    # CSR lists unassigned tickets
    res = await async_client.get("/api/v1/csr/tickets?unassigned=true", headers=headers)
    assert res.status_code == 200
    csrtickets = res.json()
    assert any(t["id"] == ticket_id for t in csrtickets)

    # CSR assigns the ticket to self with priority
    assign_payload = {"assignee_id": csr.id, "priority": "high"}
    res = await async_client.post(f"/api/v1/csr/tickets/{ticket_id}/assign", json=assign_payload, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["assigned_to_id"] == str(csr.id)
    assert updated["priority"] == "high"

    # CSR updates ticket status
    status_payload = {"status": "in_progress"}
    res = await async_client.patch(f"/api/v1/csr/tickets/{ticket_id}", json=status_payload, headers=headers)
    assert res.status_code == 200
    upd = res.json()
    assert upd["status"] == "in_progress"

    # Test 404 on non-existent ticket
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await async_client.post(f"/api/v1/csr/tickets/{fake_id}/assign", json=assign_payload, headers=headers)
    assert res.status_code == 404
    res = await async_client.patch(f"/api/v1/csr/tickets/{fake_id}", json=status_payload, headers=headers)
    assert res.status_code == 404
