from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class WSChat(BaseModel):
    ticket_id: UUID
    sender_id: UUID
    content: str
    timestamp: datetime

class ChatCreate(BaseModel):
    ticket_id: UUID
    content: str

class ChatRead(BaseModel):
    id: UUID
    ticket_id: UUID
    sender_id: UUID
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True