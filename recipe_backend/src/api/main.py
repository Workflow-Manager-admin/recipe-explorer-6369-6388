from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth_router import router as auth_router
from .recipe_router import router as recipe_router

app = FastAPI(
    title="Recipe Explorer API",
    description="API for managing recipes and users, with authentication and favorites",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication & user ops"},
        {"name": "recipes", "description": "Recipe management and favorites"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["health"])
def health_check():
    """Health check."""
    return {"message": "Healthy"}

# Register routers
app.include_router(auth_router)
app.include_router(recipe_router)
