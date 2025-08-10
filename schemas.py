from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    sex: str
    birth_date: date
    height_cm: float
    activity_level: str
    goal: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    sex: str
    birth_date: date
    height_cm: float
    activity_level: str
    goal: str
    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class FoodIn(BaseModel):
    name: str
    brand: Optional[str] = None
    serving_size_g: float = 100.0
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    barcode: Optional[str] = None

class FoodOut(FoodIn):
    id: int
    class Config:
        from_attributes = True

class FoodLogIn(BaseModel):
    food_id: int
    date: date
    meal: str
    quantity: float = 1.0

class DaySummary(BaseModel):
    date: date
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float

class ProductIn(BaseModel):
    name: str
    brand: Optional[str] = None
    image_b64: Optional[str] = None
    calories: Optional[float] = 0
    protein_g: Optional[float] = 0
    carbs_g: Optional[float] = 0
    fat_g: Optional[float] = 0
    fiber_g: Optional[float] = 0
    sodium_mg: Optional[float] = 0

class ProductOut(ProductIn):
    id: int
    phash: Optional[str] = None
    class Config:
        from_attributes = True