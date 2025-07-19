from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ticket import TicketCreate, TicketOut
from app.models.ticket import Ticket
from app.core.security import get_current_user
from app.db.session import get_db
from sqlalchemy.future import select
from typing import List, Optional

router = APIRouter()

@router.post("/tickets", response_model=TicketOut)
async def create_ticket(
    ticket_in: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Instantiate ticket
    ticket = Ticket(
        **ticket_in.dict(),
        user_id=current_user.id,
    )
    # Auto-assign to CSR
    csr_id = await assign_csr_to_ticket(db, strategy="round_robin")
    if csr_id:
        ticket.assigned_to_id = csr_id
    
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket

@router.get("/tickets", response_model=List[TicketOut])
async def get_my_tickets(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10
):
    query = select(Ticket).where(Ticket.user_id == current_user.id)
    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("tickets/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket or ticket.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
