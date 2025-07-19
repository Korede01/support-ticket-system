from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints.tickets import csr, user
from app.api.v1.endpoints.chat import chat

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(csr.router, prefix="/csr", tags=["CSR Ticket"])
api_router.include_router(user.router, prefix="/user", tags=["User Ticket"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
