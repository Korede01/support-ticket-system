from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.message import WSMessage, MessageCreate, MessageRead
from app.models.message import Message
from app.core.websocket_manager import manager
from app.models.ticket import Ticket
import asyncio

router = APIRouter()

@router.websocket("/ws/tickets/{ticket_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    ticket_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # Authenticate user via token query param
    user = await get_current_user(token, db)
    # Verify ticket exists and user is participant (owner or assigned CSR)
    ticket = await db.get(Ticket, ticket_id)
    if not ticket or (user.id != ticket.user_id and user.id != ticket.assigned_to_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(ticket_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # parse inbound
            payload = MessageCreate.parse_raw(data)
            # persist message
            msg = Message(
                ticket_id=payload.ticket_id,
                sender_id=user.id,
                content=payload.content
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            ws_msg = WSMessage(
                ticket_id=msg.ticket_id,
                sender_id=msg.sender_id,
                content=msg.content,
                timestamp=msg.timestamp
            )
            # broadcast
            await manager.broadcast(ticket_id, ws_msg.dict())
    except WebSocketDisconnect:
        manager.disconnect(ticket_id, websocket)