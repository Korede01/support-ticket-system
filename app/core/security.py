import bcrypt
import jwt
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User, UserRole

ALGORITHM = settings.ALGORITHM
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a plaintext password against the hashed version.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token (short‐lived). Includes:
      - sub: user ID
      - exp: expiration (now + ACCESS_TOKEN_EXPIRE_MINUTES)
      - jti: unique identifier for this token
      - type: "access"
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid4())
    to_encode = data.copy()
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token (longer‐lived). Includes:
      - sub: user ID
      - exp: expiration (now + REFRESH_TOKEN_EXPIRE_MINUTES)
      - jti: unique identifier
      - type: "refresh"
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid4())
    to_encode = data.copy()
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token: str) -> dict | None:
    """
    Decode a JWT (access or refresh). Returns payload or None if invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

async def is_token_blacklisted(jti: str, db: AsyncSession) -> bool:
    """
    Check the TokenBlacklist table to see if this jti has been revoked.
    """
    result = await db.execute(
        select(TokenBlacklist).where(TokenBlacklist.jti == jti)
    )
    return result.scalars().first() is not None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that:
      1. Decodes the access‐token
      2. Verifies its type is "access"
      3. Checks that its jti is not blacklisted
      4. Loads the user from DB
    Raises 401 if anything is invalid.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if await is_token_blacklisted(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

async def require_csr(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has CSR role.
    """
    if current_user.role != UserRole.CSR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSR privileges required")
    return current_user