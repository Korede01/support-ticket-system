from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional

from app.schemas.ticket import TicketOut, TicketAssign, TicketUpdateStatus, TicketStatus
from app.models.ticket import Ticket
from app.core.security import require_csr, get_current_user
from app.db.session import get_db

router = APIRouter()

@router.get("/tickets", response_model=List[TicketOut])
async def get_all_tickets(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_csr),
    unassigned: Optional[bool] = False,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    query = select(Ticket)
    if unassigned:
        query = query.where(Ticket.assigned_to_id.is_(None))
    if status:
        query = query.where(Ticket.status == status)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.post("tickets/{ticket_id}/assign", response_model=TicketOut)
async def assign_ticket(
    ticket_id: UUID,
    assign_data: TicketAssign,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_csr)
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.assigned_to_id = assign_data.assignee_id
    if assign_data.priority:
        ticket.priority = assign_data.priority
    await db.commit()
    await db.refresh(ticket)
    return ticket

@router.patch("tickets/{ticket_id}", response_model=TicketOut)
async def update_ticket_status(
    ticket_id: UUID,
    update: TicketUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_csr)
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = update.status
    await db.commit()
    await db.refresh(ticket)
    return ticket
