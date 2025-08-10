from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from models import Product
from schemas import ProductIn, ProductOut
from db import get_session
from PIL import Image
import io, base64, imagehash
import numpy as np

from ai import image_phash, embed_image

router = APIRouter(prefix="/catalog", tags=["Catalog"])

def normalize_image_b64(image_b64: str) -> str:
    img_bytes = base64.b64decode(image_b64.split(",")[-1])
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_small = img.copy(); img_small.thumbnail((256,256))
    out = io.BytesIO(); img_small.save(out, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("utf-8")

@router.post("/items", response_model=ProductOut)
def add_item(data: ProductIn, session: Session = Depends(get_session)):
    image_b64 = data.image_b64
    phash = None
    emb_b64 = None
    if image_b64:
        image_b64 = normalize_image_b64(image_b64)
        # compute pHash + CNN embedding
        img_bytes = base64.b64decode(image_b64.split(",")[-1])
        pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        phash = image_phash(pil)
        emb = embed_image(pil)
        if emb is not None:
            emb_b64 = base64.b64encode(emb).decode("utf-8")
    item = Product(
        name=data.name, brand=data.brand, image_b64=image_b64, phash=phash, emb_b64=emb_b64,
        calories=data.calories, protein_g=data.protein_g, carbs_g=data.carbs_g,
        fat_g=data.fat_g, fiber_g=data.fiber_g, sodium_mg=data.sodium_mg
    )
    session.add(item); session.commit(); session.refresh(item)
    return item

@router.get("/items", response_model=List[ProductOut])
def list_items(q: Optional[str] = None, session: Session = Depends(get_session)):
    stmt = select(Product)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q.lower()}%"))
    return session.exec(stmt).all()