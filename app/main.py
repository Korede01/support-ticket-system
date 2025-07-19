from fastapi import FastAPI
from app.db.session import engine, Base
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from alembic.config import Config
from alembic import command

alembic_cfg = Config("alembic.ini")

command.upgrade(alembic_cfg, "head")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description='STS API',
    version='1.0',
    
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "Development"}