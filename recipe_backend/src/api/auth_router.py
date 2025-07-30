from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import UserCreate, UserLogin, UserResponse, Token
from .db import get_db
from .db_models import User
from .auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# PUBLIC_INTERFACE
@router.post("/register", response_model=UserResponse, summary="Register new user", status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user and return user info."""
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserResponse(id=db_user.id, email=db_user.email, is_active=db_user.is_active)


# PUBLIC_INTERFACE
@router.post("/login", response_model=Token, summary="User login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return an access token."""
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(data={"sub": db_user.id})
    return Token(access_token=token, token_type="bearer")


# PUBLIC_INTERFACE
@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get info about current authenticated user."""
    return UserResponse(id=current_user.id, email=current_user.email, is_active=current_user.is_active)

