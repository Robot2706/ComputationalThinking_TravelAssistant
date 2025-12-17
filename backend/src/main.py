import os
import json
import random
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# --- Import modules ---
# Ưu tiên cấu trúc import từ branch 'demo' (có src.)
from src.utils.file_helper import get_project_root, load_json
from src.utils.logger import get_logger
from src.services import recommender as recmod

# Import Chatbot Service (Từ branch 'chatbot')
# Lưu ý: Hãy đảm bảo đường dẫn import chatbot là đúng với cấu trúc thư mục của bạn
try:
    from chatbot.rag_service import HotelChatbot
except ImportError:
    # Fallback nếu chatbot nằm trong src
    from src.chatbot.rag_service import HotelChatbot

# --- Logging ---
logger = get_logger("API")

# --- CORS (cho frontend local/dev) ---
# Lấy biến môi trường hoặc mặc định localhost:3000
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# --- Global Variables ---
chatbot_instance: Optional[HotelChatbot] = None

# --- Path Setup ---
BASE_DIR = get_project_root()
HOTELS_JSON_PATH = str(BASE_DIR / "data" / "processed" / "hotels_parsed.json")
CLICKS_JSON_PATH = str(BASE_DIR / "data" / "processed" / "hotel_clicks.json")

# Kiểm tra data
if not os.path.exists(HOTELS_JSON_PATH):
    logger.warning(f"⚠️ DATA NOT FOUND at: {HOTELS_JSON_PATH}")
else:
    logger.info(f"✅ Data loaded from: {HOTELS_JSON_PATH}")

# Tạo file tracking clicks nếu chưa có
if not os.path.exists(CLICKS_JSON_PATH):
    with open(CLICKS_JSON_PATH, 'w') as f:
        json.dump({"weekly_clicks": {}}, f)
    logger.info(f"✅ Created clicks tracking file at: {CLICKS_JSON_PATH}")


# --- Pydantic Models ---

# [DEMO] Model phụ cho reviews
class ReviewItem(BaseModel):
    title: str
    score: float

# [BOTH] Search Request (Lấy bản gọn gàng từ demo)
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
    
    # Giữ lại validator check date từ chatbot nếu cần thiết, 
    # nhưng ở đây ta dùng bản demo cho gọn, logic validation có thể nằm ở service.

# [DEMO] HotelOut mở rộng (Fix lỗi hiển thị ảnh)
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
    # Các trường mới từ branch demo
    images: List[str] = []          
    address: Optional[str] = None   
    stars: Optional[int] = 0        
    reviews_count: Optional[int] = 0 
    category_reviews: List[ReviewItem] = [] 

# [CHATBOT] Model request cho Chatbot
class ChatRequest(BaseModel):
    question: str = Field(..., description="Câu hỏi của người dùng cho chatbot.")

class RecommendResponse(BaseModel):
    results: List[HotelOut]
    meta: dict

# [CLICK TRACKING] Model request cho tracking hotel clicks
class HotelClickRequest(BaseModel):
    hotel_id: int = Field(..., description="ID của hotel được click")

class TopHotelsResponse(BaseModel):
    hotels: List[int] = Field(..., description="Danh sách hotel ID top clicked")
    meta: dict

# --- Lifespan Manager (Từ branch Chatbot) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý vòng đời: Khởi tạo Chatbot khi server start.
    """
    # --- STARTUP ---
    global chatbot_instance
    try:
        logger.info("Initializing Chatbot Service...")
        chatbot_instance = HotelChatbot()
        logger.info("✅ Chatbot Service initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Chatbot Service: {e}")
        # Không raise lỗi để server vẫn chạy được tính năng recommend
    
    yield # Server chạy tại đây
    
    # --- SHUTDOWN ---
    logger.info("Application shutting down.")


# --- App Definition ---
app = FastAPI(
    title="Hotel Recommender POC", 
    version="0.2-merged",
    lifespan=lifespan
)

# --- CORS ---
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CLICK TRACKING HELPER FUNCTIONS ---
def get_current_week_key():
    """Lấy key tuần hiện tại (Monday-based)"""
    now = datetime.now()
    day_of_week = now.weekday()  # Monday = 0
    start_of_week = now - timedelta(days=day_of_week)
    return start_of_week.strftime('%Y-%m-%d')

def load_clicks_data():
    """Load dữ liệu clicks từ file JSON"""
    try:
        with open(CLICKS_JSON_PATH, 'r') as f:
            return json.load(f)
    except:
        return {"weekly_clicks": {}}

def save_clicks_data(data):
    """Lưu dữ liệu clicks vào file JSON"""
    try:
        with open(CLICKS_JSON_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving clicks data: {e}")

def track_hotel_click(hotel_id: int):
    """Ghi nhận một click cho hotel"""
    week_key = get_current_week_key()
    data = load_clicks_data()
    
    if week_key not in data["weekly_clicks"]:
        data["weekly_clicks"][week_key] = {}
    
    hotel_id_str = str(hotel_id)
    if hotel_id_str not in data["weekly_clicks"][week_key]:
        data["weekly_clicks"][week_key][hotel_id_str] = 0
    
    data["weekly_clicks"][week_key][hotel_id_str] += 1
    save_clicks_data(data)
    logger.info(f"📍 Tracked click for hotel {hotel_id} (week: {week_key})")

def get_top_hotels_this_week(limit: int = 2):
    """Lấy top N hotels được click nhiều nhất tuần này"""
    week_key = get_current_week_key()
    data = load_clicks_data()
    
    clicks = data.get("weekly_clicks", {}).get(week_key, {})
    
    # Sort theo click count
    sorted_hotels = sorted(
        [(int(hotel_id), count) for hotel_id, count in clicks.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    return [hotel_id for hotel_id, count in sorted_hotels[:limit]]

def get_random_fallback_hotels(limit: int = 2):
    """Lấy random fallback hotels cho tuần này (random 1 lần per week, rồi cố định)"""
    week_key = get_current_week_key()
    data = load_clicks_data()
    
    if "random_fallback" not in data:
        data["random_fallback"] = {}
    
    # Nếu tuần này chưa có random fallback, tạo mới
    if week_key not in data["random_fallback"]:
        try:
            hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
            hotel_ids = [h.id for h in hotels]
            random_hotels = random.sample(hotel_ids, min(limit, len(hotel_ids)))
            data["random_fallback"][week_key] = random_hotels
            save_clicks_data(data)
            logger.info(f"✨ Generated random fallback hotels for week {week_key}: {random_hotels}")
        except Exception as e:
            logger.error(f"Error generating random fallback: {e}")
            return []
    
    return data["random_fallback"][week_key]

# --- Endpoints ---

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

# [CHATBOT] Endpoint Chat
@app.post("/api/chat", summary="Gửi câu hỏi và nhận câu trả lời từ chatbot")
async def chat_endpoint(req: ChatRequest):
    global chatbot_instance
    if chatbot_instance is None:
        logger.error("Chatbot instance is not available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Chatbot service is currently unavailable or still initializing."
        )
    
    logger.info(f"Received chat question: {req.question[:50]}...")
    
    try:
        answer = chatbot_instance.chat(req.question)
        return {
            "question": req.question,
            "answer": answer
        }
    except Exception as ex:
        logger.exception(f"Chatbot processing error: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An error occurred while processing your request in the chatbot."
        )

# [DEMO] Endpoint Districts (Fix logic sort/get)
@app.get("/api/districts", response_model=List[str])
def get_districts():
    try:
        hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
        # Branch demo dùng dot notation và filter kỹ hơn
        districts = sorted({h.district for h in hotels if h.district})
        return districts
    except Exception as e:
        logger.error(f"Error loading districts: {e}")
        raise HTTPException(status_code=500, detail="Error loading data")

# [CLICK TRACKING] Endpoint Get Top Hotels (MUST be before /{hotel_id} route)
@app.get("/api/hotels/top-clicked", response_model=TopHotelsResponse)
def get_top_clicked_hotels():
    try:
        top_hotels = get_top_hotels_this_week(limit=2)
        week_key = get_current_week_key()
        
        # Nếu không đủ 2 hotels clicked, dùng random fallback
        if len(top_hotels) < 2:
            fallback_hotels = get_random_fallback_hotels(limit=2 - len(top_hotels))
            top_hotels.extend(fallback_hotels)
            meta_type = "mixed"  # top + fallback
        else:
            meta_type = "clicked"  # all from clicks
        
        return TopHotelsResponse(
            hotels=top_hotels,
            meta={"week": week_key, "count": len(top_hotels), "type": meta_type}
        )
    except Exception as e:
        logger.error(f"Error getting top hotels: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
# [NEW] Endpoint Get All Hotels (for chatbot name matching)
@app.get("/api/hotels", response_model=List[dict])
def get_all_hotels():
    """Return simplified list of all hotels (id, name only) for chatbot matching"""
    try:
        hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
        # Chỉ trả về id và name để giảm payload
        return [{"id": h.id, "name": str(h.name or "")} for h in hotels]
    except Exception as e:
        logger.error(f"Error loading all hotels: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading hotels: {str(e)}")

# [DEMO] Endpoint Get Hotel Details (Fix mapping fields mới)
@app.get("/api/hotels/{hotel_id}", response_model=HotelOut)
def get_hotel(hotel_id: int):
    try:
        hotels = recmod.load_hotels_from_json(HOTELS_JSON_PATH)
        for h in hotels:
            if h.id == hotel_id:
                return HotelOut(
                    id=h.id,
                    name=str(h.name or ""),
                    district=str(h.district or ""),
                    price=float(h.price or 0.0),
                    rating=float(h.rating or 0.0),
                    amenities=h.amenities or [],
                    score=None,
                    
                    details=str(h.details or ""),
                    image=str(h.image or ""),
                    
                    # Mapping các trường mới từ branch Demo
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

# [DEMO] Endpoint Recommend (Fix mapping fields trong vòng lặp kết quả)
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
        results, meta = recmod.recommend_from_json(user_input, HOTELS_JSON_PATH, topN=user_input["topN"])
    except Exception as ex:
        logger.exception(f"Recommendation error: {ex}")
        # Trả về lỗi trong meta thay vì 500 nếu muốn frontend handle
        return RecommendResponse(results=[], meta={"error": str(ex)})

    if not results:
        return RecommendResponse(results=[], meta=meta)

    out_results = []
    for r in results:
        # recommend_from_json trả về List[Dict], dùng .get()
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
            
            # Mapping các trường mới từ branch Demo
            images=r.get("images") or [],
            address=str(r.get("address") or ""),
            stars=int(r.get("stars") or 0),
            reviews_count=int(r.get("reviews_count") or 0),
            category_reviews=r.get("category_reviews") or []
        ))

    return RecommendResponse(results=out_results, meta=meta)

# [CLICK TRACKING] Endpoint Track Hotel Click
@app.post("/api/hotels/track-click", summary="Ghi nhận click cho một hotel")
def track_click(req: HotelClickRequest):
    try:
        track_hotel_click(req.hotel_id)
        return {"status": "ok", "message": f"Click tracked for hotel {req.hotel_id}"}
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# [CLICK TRACKING] Endpoint Get Top Hotels
@app.get("/api/hotels/top-clicked", response_model=TopHotelsResponse)
def get_top_clicked_hotels():
    try:
        top_hotels = get_top_hotels_this_week(limit=2)
        week_key = get_current_week_key()
        
        # Nếu không đủ 2 hotels clicked, dùng random fallback
        if len(top_hotels) < 2:
            fallback_hotels = get_random_fallback_hotels(limit=2 - len(top_hotels))
            top_hotels.extend(fallback_hotels)
            meta_type = "mixed"  # top + fallback
        else:
            meta_type = "clicked"  # all from clicks
        
        return TopHotelsResponse(
            hotels=top_hotels,
            meta={"week": week_key, "count": len(top_hotels), "type": meta_type}
        )
    except Exception as e:
        logger.error(f"Error getting top hotels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Server starting... Docs at http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)