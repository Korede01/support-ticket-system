import random
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.ticket import Ticket

async def assign_csr_to_ticket(
    db: AsyncSession,
    strategy: str = "round_robin"
) -> str:
    """
    Select a CSR to assign a ticket, using either 'random' or 'round_robin'.
    Returns the chosen CSR's user_id (UUID).
    """
    # Fetch all CSRs
    result = await db.execute(
        select(User).where(User.role == UserRole.CSR)
    )
    csrs = result.scalars().all()
    if not csrs:
        return None

    if strategy == "random":
        return random.choice(csrs).id

    # Round-robin: look at last assigned ticket
    result = await db.execute(
        select(Ticket.assigned_to_id)
        .where(Ticket.assigned_to_id.is_not(None))
        .order_by(Ticket.created_at.desc())
        .limit(1)
    )
    last_assigned_id = result.scalars().first()

    # Build list of CSR IDs
    csr_ids = [csr.id for csr in csrs]
    if last_assigned_id in csr_ids:
        idx = csr_ids.index(last_assigned_id)
        next_idx = (idx + 1) % len(csr_ids)
    else:
        next_idx = 0

    return csr_ids[next_idx]