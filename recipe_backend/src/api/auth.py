import os
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .db import get_db
from .db_models import User

JWT_SECRET = os.environ.get("JWT_SECRET", "SECRET_KEY_CHANGE_ME")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pwd_context.verify(password, hashed)

# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

# PUBLIC_INTERFACE
async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    """Get user from JWT token or raise HTTPException(401)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    q = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

