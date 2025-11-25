# main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import os
import logging

# import module recommender từ services
from services import recommender as recmod

app = FastAPI(title="Hotel Recommender POC", version="0.1")

# --- CORS (cho frontend local/dev) ---
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # dev: cho mọi origin để test
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recommender-api")

# --- Pydantic models (request / response) ---
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


class HotelOut(BaseModel):
    id: int
    name: str
    district: str
    price: float
    rating: float
    amenities: List[str]
    score: Optional[float] = None

class RecommendResponse(BaseModel):
    results: List[HotelOut]
    meta: dict

# --- Load hotels from JSON file via recommender ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOTELS_JSON_PATH = os.path.join(BASE_DIR, "services", "hotels_parsed.json")  # chỉnh path nếu cần

# --- Simple utility endpoints ---
@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/districts", response_model=List[str])
def get_districts():
    hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
    districts = sorted({h.district for h in hotels})
    return districts

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
                score=None
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
    else:
        # no budget fields provided: you can choose defaults or return 400.
        # We'll pass no explicit budget and rely on recommender's fallback defaults.
        pass

    # purpose optional: recommender will default to 'leisure' if missing,
    # but pass through if provided.
    if req.purpose:
        user_input["purpose"] = req.purpose

    try:
        results, meta = recmod.recommend_from_json(user_input, HOTELS_JSON_PATH, topN=user_input["topN"])
    except FileNotFoundError as fnf:
        logger.error("Hotels JSON not found: %s", fnf)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(fnf))
    except ValueError as ve:
        logger.error("Bad user input: %s", ve)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as ex:
        logger.exception("Recommendation error: %s", ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal recommendation error")

    if not results:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="no results found")

    out_results = []
    for r in results:
        # đảm bảo id có mặt
        id_val = r.get("id")
        if id_val is None:
            # chọn cách xử lý: bỏ item hoặc raise; ở đây ta raise để dễ debug
            raise ValueError(f"Result item missing 'id': {r}")

        out_results.append(HotelOut(
            id=int(id_val),
            name=str(r.get("name") or ""),
            district=str(r.get("district") or ""),
            price=float(r.get("price") or 0.0),
            rating=float(r.get("rating") or 0.0),
            amenities=r.get("amenities") or [],
            score=r.get("score")
        ))


    return RecommendResponse(results=out_results, meta=meta)

