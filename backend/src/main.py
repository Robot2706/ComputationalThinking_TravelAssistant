import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# Các module tự viết
from src.utils.file_helper import get_project_root, load_json
from src.utils.logger import get_logger
from src.services import recommender as recmod

# ... (Phần còn lại giữ nguyên)

# Import modules từ src
from src.utils.file_helper import get_project_root, load_json
from src.utils.logger import get_logger
from src.services import recommender as recmod

app = FastAPI(title="Hotel Recommender POC", version="0.1")

# --- Logging ---
logger = get_logger("API")

# --- CORS (cho frontend local/dev) ---
# Lấy biến môi trường hoặc mặc định localhost:3000
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev mode: cho phép tất cả (cẩn thận khi production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Path Setup ---
BASE_DIR = get_project_root()
# [FIX 2] Ép kiểu về string để tránh lỗi nếu module recommender không hỗ trợ Path object
HOTELS_JSON_PATH = str(BASE_DIR / "data" / "processed" / "hotels_parsed.json")

# Kiểm tra file data ngay khi khởi động
if not os.path.exists(HOTELS_JSON_PATH):
    logger.warning(f"⚠️ DATA NOT FOUND at: {HOTELS_JSON_PATH}")
else:
    logger.info(f"✅ Data loaded from: {HOTELS_JSON_PATH}")


# --- Pydantic models ---
class SearchRequest(BaseModel):
    # frontend may send a single `budget` (number) OR budget_min & budget_max (legacy)
    # We therefore make all budget fields optional and normalize in endpoint.
    district: str = Field(...)
    budget: Optional[float] = Field(None, ge=0)
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    purpose: Optional[str] = Field(None)
    check_in: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    check_out: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    topN: Optional[int] = Field(5, ge=1, le=50)

    @field_validator("district", "purpose", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("check_out")
    @classmethod
    def check_dates(cls, v, info):
        from datetime import datetime
        if "check_in" in info.data:
            ci = datetime.strptime(info.data["check_in"], "%Y-%m-%d")
            co = datetime.strptime(v, "%Y-%m-%d")
            if co < ci:
                raise ValueError("check_out must be >= check_in")
        return v


# ...
class HotelOut(BaseModel):
    id: int
    name: str
    district: str
    price: float
    rating: float
    amenities: List[str]
    score: Optional[float] = None
    
    # --- THÊM 2 DÒNG NÀY ---
    details: Optional[str] = None  # Để chứa mô tả chi tiết
    image: Optional[str] = None    # Để chứa link ảnh
# ...

class RecommendResponse(BaseModel):
    results: List[HotelOut]
    meta: dict


# --- Endpoints ---
@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/districts", response_model=List[str])
def get_districts():
    # Sử dụng hàm load_json từ utils (nếu bạn đã viết trong file_helper.py)
    # Hoặc dùng hàm của recmod nếu logic phức tạp
    # Ở đây giả sử recmod.load_hotels_from_json vẫn hoạt động
    try:
        hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
        districts = sorted({h.district for h in hotels})
        return districts
    except Exception as e:
        logger.error(f"Error loading districts: {e}")
        raise HTTPException(status_code=500, detail="Error loading data")

@app.get("/api/hotels/{hotel_id}", response_model=HotelOut)
def get_hotel(hotel_id: int):
    hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
    for h in hotels:
        if h.id == hotel_id:
            return HotelOut(
                id=h.id,
                name=h.name,
                district=h.district,
                price=h.price,
                rating=h.rating,
                amenities=h.amenities,
                score=None,
                
                details=getattr(h, "details", None),
                image=getattr(h, "image", None) or getattr(h, "photo", None) 
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="hotel not found")

@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(req: SearchRequest):
    # Build flexible user_input for recommender.recommend_from_json
    # priority:
    # 1) if req.budget provided -> pass "budget"
    # 2) elif both budget_min/budget_max provided -> pass them
    # 3) else fallback to reasonable defaults (same as recommender fallback)
    user_input = {
        "district": req.district,
        "check_in": req.check_in,
        "check_out": req.check_out,
        "topN": int(req.topN) if req.topN is not None else 5
    }

    # prefer single budget if provided
    if req.budget is not None:
        user_input["budget"] = float(req.budget)
    elif req.budget_min is not None and req.budget_max is not None:
        user_input["budget_min"] = float(req.budget_min)
        user_input["budget_max"] = float(req.budget_max)
    
    if req.purpose:
        user_input["purpose"] = req.purpose

    try:
        results, meta = recmod.recommend_from_json(user_input, HOTELS_JSON_PATH, topN=user_input["topN"])
    except FileNotFoundError as fnf:
        logger.error(f"Hotels JSON not found: {fnf}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Data file missing")
    except ValueError as ve:
        logger.error(f"Bad user input: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as ex:
        logger.exception(f"Recommendation error: {ex}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal recommendation error")

    if not results:
        return RecommendResponse(results=[], meta=meta)

    out_results = []
    for r in results:
        id_val = r.get("id")
        if id_val is None:
            continue

        out_results.append(HotelOut(
            id=int(id_val),
            name=str(r.get("name") or ""),
            district=str(r.get("district") or ""),
            price=float(r.get("price") or 0.0),
            rating=float(r.get("rating") or 0.0),
            amenities=r.get("amenities") or [],
            score=r.get("score"),
            
            # --- THÊM CÁC DÒNG NÀY ---
            details=str(r.get("details") or ""), # Lấy trường details
            image=str(r.get("image") or r.get("photo") or "") # Lấy trường image
        ))

    return RecommendResponse(results=out_results, meta=meta)