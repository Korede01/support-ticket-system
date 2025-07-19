from pydantic_settings import BaseSettings, Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Support Ticketing System"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int         # 15 minutes for access‐tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int # 30 days for refresh‐tokens
    ALGORITHM: str
    
    # === App Settings ===
    API_BASE_URL: str = Field(..., env="API_BASE_URL")
    FRONTEND_BASE_URL: str = Field(..., env="FRONTEND_BASE_URL")
    
    class Config:
        env_file = ".env"

settings = Settings()