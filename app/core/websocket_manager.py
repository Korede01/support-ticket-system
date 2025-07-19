import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # maps ticket_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, ticket_id: str, websocket: WebSocket):
        await websocket.accept()
        conns = self.active_connections.setdefault(str(ticket_id), [])
        conns.append(websocket)

    def disconnect(self, ticket_id: str, websocket: WebSocket):
        conns = self.active_connections.get(str(ticket_id), [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, ticket_id: str, message: dict):
        conns = self.active_connections.get(str(ticket_id), [])
        data = json.dumps(message, default=str)
        for connection in conns:
            await connection.send_text(data)

# singleton
manager = ConnectionManager()