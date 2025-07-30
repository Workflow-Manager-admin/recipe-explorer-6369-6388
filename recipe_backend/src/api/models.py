from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


# PUBLIC_INTERFACE
class UserResponse(BaseModel):
    """Schema returned after user registration or login."""
    id: int
    email: EmailStr
    is_active: bool = True


# PUBLIC_INTERFACE
class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"


# PUBLIC_INTERFACE
class RecipeBase(BaseModel):
    """Base recipe model."""
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]


# PUBLIC_INTERFACE
class RecipeCreate(RecipeBase):
    """Schema for creating a recipe."""
    pass


# PUBLIC_INTERFACE
class RecipeUpdate(RecipeBase):
    """Schema for updating a recipe."""
    pass


# PUBLIC_INTERFACE
class RecipeResponse(RecipeBase):
    """Recipe model with additional fields."""
    id: int
    owner_id: int
    is_favorite: Optional[bool] = False


# PUBLIC_INTERFACE
class RecipeListResponse(BaseModel):
    """Paginated recipe list."""
    recipes: List[RecipeResponse]
    total: int


# PUBLIC_INTERFACE
class FavoriteRequest(BaseModel):
    """For adding/removing favorites."""
    recipe_id: int

