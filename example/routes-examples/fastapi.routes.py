"""
FastAPI Routes Example
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    name: str
    email: str


class ProductCreate(BaseModel):
    name: str
    price: float


# User endpoints
@router.get("/api/v1/users")
async def get_users():
    """Get all users"""
    return {"message": "Get all users"}


@router.post("/api/v1/users")
async def create_user(user: UserCreate):
    """Create a new user"""
    return {"message": "User created"}


@router.get("/api/v1/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID"""
    return {"message": f"Get user {user_id}"}


@router.put("/api/v1/users/{user_id}")
async def update_user(user_id: int, user: UserCreate):
    """Update user"""
    return {"message": f"User {user_id} updated"}


@router.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: int):
    """Delete user"""
    return {"message": f"User {user_id} deleted"}


# Product endpoints
@router.get("/api/v1/products")
async def get_products():
    """Get all products"""
    return {"message": "Get all products"}


@router.post("/api/v1/products")
async def create_product(product: ProductCreate):
    """Create product"""
    return {"message": "Product created"}


# Category endpoints
@router.get("/api/v1/categories")
async def get_categories():
    """Get all categories"""
    return {"message": "Get all categories"}
