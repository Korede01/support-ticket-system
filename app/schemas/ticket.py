from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from uuid import UUID
from datetime import datetime

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TicketBase(BaseModel):
    title: str
    description: str
    category: str
    type: str

class TicketCreate(TicketBase):
    pass  # User can't set priority

class TicketUpdateStatus(BaseModel):
    status: TicketStatus

class TicketAssign(BaseModel):
    assignee_id: UUID
    priority: Optional[TicketPriority] = None

class TicketOut(TicketBase):
    id: UUID
    status: TicketStatus
    priority: Optional[TicketPriority]
    user_id: UUID
    assigned_to_id: Optional[UUID]
    created_at: datetime

    class Config:
        orm_mode = True
