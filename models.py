from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    hashed_password: str
    sex: str = Field(default="male")
    birth_date: date
    height_cm: float
    activity_level: str = Field(default="moderate")
    goal: str = Field(default="maintain")
    logs: List["FoodLog"] = Relationship(back_populates="user")

class Food(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    brand: Optional[str] = None
    serving_size_g: float = 100.0
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    barcode: Optional[str] = None

class FoodLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    food_id: int = Field(foreign_key="food.id")
    date: date
    meal: str
    quantity: float = 1.0
    user: Optional[User] = Relationship(back_populates="logs")

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    brand: Optional[str] = None
    image_b64: Optional[str] = None     # preview thumb
    phash: Optional[str] = Field(default=None, index=True)
    emb_b64: Optional[str] = None       # CNN embedding (base64 of float32)
    # nutrition (standardized per 100g or per serving)
    calories: Optional[float] = 0
    protein_g: Optional[float] = 0
    carbs_g: Optional[float] = 0
    fat_g: Optional[float] = 0
    fiber_g: Optional[float] = 0
    sodium_mg: Optional[float] = 0