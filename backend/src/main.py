import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Import modules từ src
from src.utils.file_helper import get_project_root, load_json
from src.utils.logger import get_logger
from src.services import recommender as recmod

app = FastAPI(title="Hotel Recommender POC", version="0.1")
logger = get_logger("API")

# Setup CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path Setup
BASE_DIR = get_project_root()
HOTELS_JSON_PATH = str(BASE_DIR / "data" / "processed" / "hotels_parsed.json")

if not os.path.exists(HOTELS_JSON_PATH):
    logger.warning(f"⚠️ DATA NOT FOUND at: {HOTELS_JSON_PATH}")
else:
    logger.info(f"✅ Data loaded from: {HOTELS_JSON_PATH}")

# --- Models ---

class ReviewItem(BaseModel):
    title: str
    score: float

class SearchRequest(BaseModel):
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
        return v.strip() if isinstance(v, str) else v

class HotelOut(BaseModel):
    id: int
    name: str
    district: str
    price: float
    rating: float
    amenities: List[str]
    score: Optional[float] = None
    
    details: Optional[str] = None
    image: Optional[str] = None
    images: List[str] = []          
    address: Optional[str] = None   
    stars: Optional[int] = 0        
    reviews_count: Optional[int] = 0 
    category_reviews: List[ReviewItem] = [] 

class RecommendResponse(BaseModel):
    results: List[HotelOut]
    meta: dict

# --- Endpoints ---

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/districts", response_model=List[str])
def get_districts():
    try:
        # load_hotels_from_json trả về List[Hotel Object]
        hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
        # [FIX] Dùng dot notation (h.district) thay vì .get()
        districts = sorted({h.district for h in hotels if h.district})
        return districts
    except Exception as e:
        logger.error(f"Error loading districts: {e}")
        raise HTTPException(status_code=500, detail="Error loading data")

@app.get("/api/hotels/{hotel_id}", response_model=HotelOut)
def get_hotel(hotel_id: int):
    try:
        # load_hotels_from_json trả về List[Hotel Object]
        hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
        for h in hotels:
            # [FIX] Dùng dot notation (h.id) vì h là Object class Hotel
            if h.id == hotel_id:
                return HotelOut(
                    id=h.id,
                    name=str(h.name or ""),
                    district=str(h.district or ""),
                    price=float(h.price or 0.0),
                    rating=float(h.rating or 0.0),
                    amenities=h.amenities or [],
                    score=None, # Detail không có score gợi ý
                    details=str(h.details or ""),
                    image=str(h.image or ""),
                    
                    # Các trường mới (truy cập bằng dấu chấm)
                    images=h.images or [],
                    address=str(h.address or ""),
                    stars=int(h.stars or 0),
                    reviews_count=int(h.reviews_count or 0),
                    category_reviews=h.category_reviews or []
                )
    except Exception as e:
        logger.error(f"Error getting hotel {hotel_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(req: SearchRequest):
    user_input = {
        "district": req.district,
        "check_in": req.check_in,
        "check_out": req.check_out,
        "topN": int(req.topN) if req.topN is not None else 5
    }

    if req.budget is not None:
        user_input["budget"] = float(req.budget)
    elif req.budget_min is not None and req.budget_max is not None:
        user_input["budget_min"] = float(req.budget_min)
        user_input["budget_max"] = float(req.budget_max)
    
    if req.purpose:
        user_input["purpose"] = req.purpose

    try:
        # recommend_from_json trả về List[Dict] -> Dùng .get() là đúng
        results, meta = recmod.recommend_from_json(user_input, HOTELS_JSON_PATH, topN=user_input["topN"])
    except Exception as ex:
        logger.exception(f"Recommendation error: {ex}")
        return RecommendResponse(results=[], meta={"error": str(ex)})

    if not results:
        return RecommendResponse(results=[], meta=meta)

    out_results = []
    for r in results:
        # r là Dictionary -> Dùng .get()
        id_val = r.get("id")
        if id_val is None: continue

        out_results.append(HotelOut(
            id=int(id_val),
            name=str(r.get("name") or ""),
            district=str(r.get("district") or ""),
            price=float(r.get("price") or 0.0),
            rating=float(r.get("rating") or 0.0),
            amenities=r.get("amenities") or [],
            score=r.get("score"),
            details=str(r.get("details") or ""),
            image=str(r.get("image") or ""),
            
            images=r.get("images") or [],
            address=str(r.get("address") or ""),
            stars=int(r.get("stars") or 0),
            reviews_count=int(r.get("reviews_count") or 0),
            category_reviews=r.get("category_reviews") or []
        ))

    return RecommendResponse(results=out_results, meta=meta)