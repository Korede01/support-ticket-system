import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.logging import logger

from app.schemas.user import (
    UserRole,
    UserCreate,
    UserLogin,
    UserOut,
    Token,
    RefreshTokenRequest,
    LogoutRequest
)
from app.models.user import User, UserRole as DBUserRole
from app.models.token_blacklist import TokenBlacklist
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_blacklisted,
)
from app.db.session import get_db

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered",
        )

    # Create user with only necessary fields
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=DBUserRole.USER,
        is_active=True
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user"
        )

@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin, db: AsyncSession = Depends(get_db)
):
    # 1. Verify email/password
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token_req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request body: { "refresh_token": "<the_refresh_token_jwt>" }
    Returns a brand-new access token AND a brand-new refresh token,
    while revoking (blacklisting) the old refresh token.
    """
    # 1. Decode & validate structure
    payload = decode_token(token_req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    old_jti = payload.get("jti")
    if old_jti is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed refresh token: missing JTI",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check if that refresh_token's jti is already blacklisted
    if await is_token_blacklisted(old_jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Revoke (blacklist) the old refresh token immediately
    black_entry = TokenBlacklist(jti=old_jti, token_type="refresh")
    db.add(black_entry)
    await db.commit()

    # 4. Extract user ID ("sub") and ensure user still exists
    try:
        user_id = uuid.UUID(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token subject is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. Issue new tokens
    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )

@router.post("/logout")
async def logout(
    logout_req: LogoutRequest, db: AsyncSession = Depends(get_db)
):
    """
    Revoke a refresh token. Client should send the refresh_token they want
    to invalidate. This will prevent further refreshes, and we can also
    optionally blacklist any access token jti if the client passes it.
    """
    payload = decode_token(logout_req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token format",
        )

    jti = payload.get("jti")
    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed token: no JTI",
        )

    # 1. If it’s already blacklisted, nothing to do
    if await is_token_blacklisted(jti, db):
        return {"msg": "Token already revoked"}

    # 2. Blacklist this refresh token
    black_entry = TokenBlacklist(jti=jti, token_type="refresh")
    db.add(black_entry)
    await db.commit()

    return {"msg": "Successfully logged out"}
