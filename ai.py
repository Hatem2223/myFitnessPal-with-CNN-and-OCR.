from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import numpy as np, cv2, pytesseract, io, base64
from PIL import Image
from pyzbar.pyzbar import decode as zbar_decode
from sqlmodel import Session, select
from db import get_session
from models import Product
import imagehash, math

# Optional: Torch CNN embedding
try:
    import torch
    from torchvision import transforms
    from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
    USE_TORCH = True
    _weights = MobileNet_V3_Small_Weights.DEFAULT
    _preprocess = _weights.transforms()
    _cnn = mobilenet_v3_small(weights=_weights)
    _cnn.classifier = torch.nn.Identity()  # use penultimate features
    _cnn.eval()
except Exception as e:
    USE_TORCH = False
    _cnn = None
    _preprocess = None

router = APIRouter(prefix="/ai", tags=["AI"])

# ---------- Image utils ----------
def deskew(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thr > 0))
    if coords.size == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    angle = (-(90 + angle)) if angle < -45 else -angle
    (h,w) = image.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def warp_largest_quad(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray,(3,3),0), 50, 150)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return image
    cnt = max(cnts, key=cv2.contourArea)
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.02*peri, True)
    if len(approx) != 4: return image
    pts = approx.reshape(4,2).astype("float32")
    s = pts.sum(axis=1); diff = np.diff(pts, axis=1)
    rect = np.zeros((4,2), dtype="float32")
    rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]; rect[3] = pts[np.argmax(diff)]
    (tl,tr,br,bl) = rect
    maxW = int(max(np.linalg.norm(br-bl), np.linalg.norm(tr-tl)))
    maxH = int(max(np.linalg.norm(tr-br), np.linalg.norm(tl-bl)))
    M = cv2.getPerspectiveTransform(rect, np.array([[0,0],[maxW-1,0],[maxW-1,maxH-1],[0,maxH-1]], dtype='float32'))
    return cv2.warpPerspective(image, M, (maxW, maxH))

def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8))
    eq = clahe.apply(gray)
    thr = cv2.threshold(eq, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    clean = cv2.morphologyEx(thr, cv2.MORPH_OPEN, kernel, iterations=1)
    return clean

def pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGB")

def np_from_bytes(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

def parse_nutrition_text(text: str) -> Dict[str, Any]:
    import re
    t = text.lower().replace("\n", " ")
    pats = {
        "calories": r"(calories|energy|السعرات|طاقة)\D+(\d{1,4})",
        "protein_g": r"(protein|بروتين)\D+(\d{1,3}(?:\.\d+)?)",
        "carbs_g": r"(carb|carbohydrate|كربوهيدرات)\D+(\d{1,3}(?:\.\d+)?)",
        "fat_g": r"(fat|دهون)\D+(\d{1,3}(?:\.\d+)?)",
        "fiber_g": r"(fiber|الياف|ألياف)\D+(\d{1,3}(?:\.\d+)?)",
        "sodium_mg": r"(sodium|صوديوم)\D+(\d{1,5})"
    }
    out = {}
    for k,pat in pats.items():
        m = re.search(pat, t)
        if m:
            try: out[k] = float(m.group(2))
            except: pass
    return out

def image_phash(pil_img: Image.Image) -> str:
    img = pil_img.convert("RGB")
    img.thumbnail((256,256))
    return str(imagehash.phash(img, hash_size=16))

def embed_image(pil_img: Image.Image) -> Optional[bytes]:
    if not USE_TORCH: return None
    with torch.no_grad():
        x = _preprocess(pil_img).unsqueeze(0)
        feat = _cnn(x).squeeze(0).numpy().astype("float32")
        # L2 normalize
        norm = np.linalg.norm(feat) + 1e-8
        feat = feat / norm
        return feat.tobytes()

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a)*np.linalg.norm(b) + 1e-9)
    return float(np.dot(a,b)/denom)

# ---------- API ----------
@router.post("/parse-nutrition-label")
async def parse_nutrition_label(file: UploadFile = File(...)):
    b = await file.read()
    img = np_from_bytes(b)
    if img is None: raise HTTPException(400, "Invalid image")
    warped = warp_largest_quad(deskew(img))
    pre = preprocess_for_ocr(warped)
    text = pytesseract.image_to_string(pre, config="--oem 3 --psm 6 -l ara+eng")
    return {"raw_text": text, "parsed": parse_nutrition_text(text)}

@router.post("/scan-barcode")
async def scan_barcode(file: UploadFile = File(...)):
    b = await file.read()
    pil = pil_from_bytes(b)
    codes = zbar_decode(pil)
    return {"barcodes": [{"type":c.type, "data": c.data.decode("utf-8","ignore")} for c in codes]}

@router.post("/guess-product")
async def guess_product(file: UploadFile = File(...), session: Session = Depends(get_session)):
    b = await file.read()
    pil = pil_from_bytes(b)
    img = np_from_bytes(b)
    if img is None: raise HTTPException(400, "Invalid image")

    # 1) Barcode
    codes = zbar_decode(pil)
    if codes:
        code = codes[0].data.decode("utf-8", "ignore")
        # Try direct match in catalog by name containing suffix of code (simple heuristic)
        prod = session.exec(select(Product).where(Product.name.ilike(f"%{code[-6:]}%"))).first()
        return {"match_by":"barcode","barcode":code,"product":prod}

    # 2) OCR token match
    warped = warp_largest_quad(deskew(img))
    text = pytesseract.image_to_string(preprocess_for_ocr(warped), config="--oem 3 --psm 6 -l ara+eng")
    tokens = [t for t in text.lower().split() if len(t)>=3]
    for token in tokens[:8]:
        prod = session.exec(select(Product).where(Product.name.ilike(f"%{token}%"))).first()
        if prod:
            return {"match_by":"text","text":token,"product":prod,"raw_text":text}

    # 3) pHash nearest
    qhash = image_phash(pil)
    products = session.exec(select(Product).where(Product.phash != None)).all()
    best = None; best_dist = 1e9
    qh = imagehash.hex_to_hash(qhash)
    for p in products:
        try:
            ph = imagehash.hex_to_hash(p.phash)
            dist = qh - ph
            if dist < best_dist:
                best, best_dist = p, dist
        except: continue
    if best:
        max_bits = len(qh.hash.flatten())
        sim = 1.0 - (best_dist/max_bits)
        # If we have CNN embeddings for both, refine with cosine sim
        if USE_TORCH and best.emb_b64:
            try:
                import numpy as _np, base64 as _b64
                qemb = embed_image(pil)
                if qemb is not None:
                    qvec = _np.frombuffer(qemb, dtype=_np.float32)
                    bvec = _np.frombuffer(_b64.b64decode(best.emb_b64), dtype=_np.float32)
                    sim = max(sim, cosine_sim(qvec, bvec))
            except: pass
        return {"match_by":"phash","score": round(float(sim),3), "product": best}

    # 4) CNN-only search if catalog has embeddings
    if USE_TORCH:
        try:
            import numpy as _np, base64 as _b64
            qemb = embed_image(pil)
            if qemb is not None:
                qvec = _np.frombuffer(qemb, dtype=_np.float32)
                candidates = session.exec(select(Product).where(Product.emb_b64 != None)).all()
                if candidates:
                    sims = []
                    for p in candidates:
                        try:
                            bvec = _np.frombuffer(_b64.b64decode(p.emb_b64), dtype=_np.float32)
                            sims.append((cosine_sim(qvec, bvec), p))
                        except: pass
                    if sims:
                        sims.sort(key=lambda x: x[0], reverse=True)
                        top = sims[0]
                        return {"match_by":"cnn","score": round(float(top[0]),3), "product": top[1]}
        except Exception as e:
            pass

    return {"match_by":"none","product": None}