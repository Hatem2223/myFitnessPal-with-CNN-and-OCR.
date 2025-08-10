from sqlmodel import Session
from db import engine, init_db
from models import Food
import json

def run():
    init_db()
    with open("seed_foods.json","r") as f:
        items = json.load(f)
    with Session(engine) as s:
        for it in items:
            s.add(Food(**it))
        s.commit()
    print("Seeded foods.")

if __name__ == "__main__":
    run()