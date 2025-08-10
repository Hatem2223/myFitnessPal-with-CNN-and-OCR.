from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List
from datetime import date

from db import init_db, get_session
from models import User, Food, FoodLog
from schemas import UserCreate, UserOut, TokenOut, FoodIn, FoodOut, FoodLogIn, DaySummary
from auth import hash_password, verify_password, create_token, get_current_user
from utils import tdee, macro_targets
from ai import router as ai_router
from catalog import router as catalog_router

app = FastAPI(title="FitPal+ Ultra API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Welcome to FitPal API"}

# ---- Auth ----
@app.post("/auth/register", response_model=UserOut)
def register(data: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing: raise HTTPException(400, "Email already registered")
    user = User(
        email=data.email, full_name=data.full_name, hashed_password=hash_password(data.password),
        sex=data.sex, birth_date=data.birth_date, height_cm=data.height_cm,
        activity_level=data.activity_level, goal=data.goal
    )
    session.add(user); session.commit(); session.refresh(user)
    return user

@app.post("/auth/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(400, "Invalid credentials")
    return TokenOut(access_token=create_token(user.email))

# ---- Foods ----
@app.get("/foods", response_model=List[FoodOut])
def list_foods(q: str = "", session: Session = Depends(get_session)):
    stmt = select(Food)
    if q:
        stmt = stmt.where(Food.name.ilike(f"%{q.lower()}%"))
    return session.exec(stmt).all()

@app.post("/foods", response_model=FoodOut)
def add_food(food: FoodIn, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    f = Food(**food.dict())
    session.add(f); session.commit(); session.refresh(f)
    return f

# ---- Logs ----
@app.post("/logs", response_model=DaySummary)
def add_log(entry: FoodLogIn, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    log = FoodLog(user_id=user.id, **entry.dict())
    session.add(log); session.commit()
    return day_summary(entry.date, user, session)

@app.get("/summary/{day}", response_model=DaySummary)
def summary(day: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    d = date.fromisoformat(day); return day_summary(d, user, session)

def day_summary(d: date, user: User, session: Session) -> DaySummary:
    from sqlmodel import select
    logs = session.exec(select(FoodLog, Food).where(FoodLog.user_id==user.id, FoodLog.date==d).join(Food, FoodLog.food_id==Food.id)).all()
    totals = {"calories":0,"protein_g":0,"carbs_g":0,"fat_g":0,"fiber_g":0,"sodium_mg":0}
    for log, food in logs:
        q = log.quantity
        totals["calories"] += food.calories * q
        totals["protein_g"] += food.protein_g * q
        totals["carbs_g"] += food.carbs_g * q
        totals["fat_g"] += food.fat_g * q
        totals["fiber_g"] += food.fiber_g * q
        totals["sodium_mg"] += food.sodium_mg * q
    return DaySummary(date=d, **{k: round(v,2) for k,v in totals.items()})

@app.get("/targets")
def targets(weight_kg: float, sex: str, height_cm: float, age: int, activity: str, goal: str):
    return macro_targets(tdee(sex, weight_kg, height_cm, age, activity), goal)

# Routers
app.include_router(ai_router)
app.include_router(catalog_router)