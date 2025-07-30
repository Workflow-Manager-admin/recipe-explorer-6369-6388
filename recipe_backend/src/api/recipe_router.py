from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import Optional

from .models import (
    RecipeCreate, RecipeUpdate, RecipeResponse, RecipeListResponse, FavoriteRequest
)
from .db import get_db
from .db_models import Recipe, User
from .auth import get_current_user

router = APIRouter(prefix="/recipes", tags=["recipes"])


# PUBLIC_INTERFACE
@router.post("/", response_model=RecipeResponse, status_code=201, summary="Create recipe")
async def create_recipe(
    recipe: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new recipe owned by current user."""
    db_recipe = Recipe(
        title=recipe.title,
        description=recipe.description,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        owner_id=current_user.id
    )
    db.add(db_recipe)
    await db.commit()
    await db.refresh(db_recipe)
    return RecipeResponse(
        id=db_recipe.id,
        title=db_recipe.title,
        description=db_recipe.description,
        ingredients=db_recipe.ingredients,
        instructions=db_recipe.instructions,
        owner_id=current_user.id,
        is_favorite=False
    )


# PUBLIC_INTERFACE
@router.get("/", response_model=RecipeListResponse, summary="Browse & search recipes")
async def browse_recipes(
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Search string"),
    skip: int = 0,
    limit: int = 20,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Browse or search recipes.
    - If q is provided, search by title, description, or ingredient.
    - Returns paginated results.
    - Add 'is_favorite' field if user is logged in.
    """
    query = select(Recipe)
    if q:
        query = query.where(or_(
            Recipe.title.ilike(f"%{q}%"),
            Recipe.description.ilike(f"%{q}%"),
            Recipe.ingredients.any(q)
        ))
    query = query.offset(skip).limit(limit)
    results = await db.execute(query)
    recipes = results.scalars().all()
    # Annotate with is_favorite if user is logged in
    recipe_objs = []
    total = len(recipes)
    fav_ids = set()
    if current_user:
        fav = await db.execute(
            select(Recipe.id).join(Recipe.favorited_by).where(User.id == current_user.id)
        )
        fav_ids = {fid for fid, in fav.all()}
    for r in recipes:
        recipe_objs.append(
            RecipeResponse(
                id=r.id,
                title=r.title,
                description=r.description,
                ingredients=r.ingredients,
                instructions=r.instructions,
                owner_id=r.owner_id,
                is_favorite=(r.id in fav_ids)
            )
        )
    return RecipeListResponse(recipes=recipe_objs, total=total)


# PUBLIC_INTERFACE
@router.get("/{recipe_id}", response_model=RecipeResponse, summary="Get recipe details")
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get recipe details by id."""
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    is_favorite = False
    if current_user:
        fav = await db.execute(
            select(Recipe.id).join(Recipe.favorited_by).where(
                User.id == current_user.id, Recipe.id == recipe_id
            )
        )
        is_favorite = bool(fav.scalar())
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        owner_id=recipe.owner_id,
        is_favorite=is_favorite
    )


# PUBLIC_INTERFACE
@router.put("/{recipe_id}", response_model=RecipeResponse, summary="Edit recipe")
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit an existing recipe (only owner can edit)."""
    db_recipe = await db.get(Recipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if db_recipe.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    for k, v in recipe_update.dict(exclude_unset=True).items():
        setattr(db_recipe, k, v)
    db.add(db_recipe)
    await db.commit()
    await db.refresh(db_recipe)
    return RecipeResponse(
        id=db_recipe.id,
        title=db_recipe.title,
        description=db_recipe.description,
        ingredients=db_recipe.ingredients,
        instructions=db_recipe.instructions,
        owner_id=db_recipe.owner_id,
        is_favorite=False
    )


# PUBLIC_INTERFACE
@router.delete("/{recipe_id}", status_code=204, summary="Delete recipe")
async def delete_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a recipe (only owner can delete)."""
    db_recipe = await db.get(Recipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if db_recipe.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.delete(db_recipe)
    await db.commit()
    return


# PUBLIC_INTERFACE
@router.post("/favorite", status_code=201, summary="Add recipe to favorites")
async def add_favorite(
    fav_req: FavoriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a recipe to user's favorites."""
    recipe = await db.get(Recipe, fav_req.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    # Attach if not already favorite
    if recipe not in current_user.favorites:
        current_user.favorites.append(recipe)
        db.add(current_user)
        await db.commit()
    return {"detail": "Recipe added to favorites"}


# PUBLIC_INTERFACE
@router.delete("/favorite/{recipe_id}", status_code=204, summary="Remove recipe from favorites")
async def remove_favorite(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a recipe from user's favorites."""
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe in current_user.favorites:
        current_user.favorites.remove(recipe)
        db.add(current_user)
        await db.commit()
    return


# PUBLIC_INTERFACE
@router.get("/favorites", response_model=RecipeListResponse, summary="List my favorite recipes")
async def list_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all favorite recipes for the current user."""
    await db.refresh(current_user)  # ensure up to date
    recipe_objs = [
        RecipeResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            ingredients=r.ingredients,
            instructions=r.instructions,
            owner_id=r.owner_id,
            is_favorite=True
        )
        for r in current_user.favorites
    ]
    return RecipeListResponse(recipes=recipe_objs, total=len(recipe_objs))

