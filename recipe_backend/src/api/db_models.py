from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.types import Text
from sqlalchemy.dialects.postgresql import ARRAY
from .db import Base


# Association table for favorites
favorites_table = Table(
    "favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("recipe_id", Integer, ForeignKey("recipes.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    recipes = relationship("Recipe", back_populates="owner")
    favorites = relationship(
        "Recipe",
        secondary=favorites_table,
        back_populates="favorited_by"
    )

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    ingredients = Column(ARRAY(String))
    instructions = Column(ARRAY(String))
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="recipes")
    favorited_by = relationship(
        "User",
        secondary=favorites_table,
        back_populates="favorites"
    )

