"""
Recommender module for Hotel Recommendation POC
(Updated to support new data fields: images, stars, reviews, etc.)
"""

from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Dict, Any
from datetime import datetime, date
import json
import os

# --------------------------- Utilities ---------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def parse_date(d: str) -> date:
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except:
        return date.today()

# --------------------------- Data classes ---------------------------
@dataclass
class UserInput:
    district: str
    budget_min: float
    budget_max: float
    purpose: str 
    check_in: str
    check_out: str
    topN: int = 5

@dataclass
class Hotel:
    id: int
    name: str
    district: str
    price: float
    rating: float
    capacity: int = 1
    amenities: List[str] = field(default_factory=list)
    details: str = ""
    image: str = ""
    # --- CÁC TRƯỜNG MỚI ---
    images: List[str] = field(default_factory=list)
    address: str = ""
    stars: int = 0
    reviews_count: int = 0
    category_reviews: List[Dict] = field(default_factory=list)
    
    available_from: str = "2025-01-01"
    available_to: str = "2025-12-31"

# --------------------------- Default parameters ---------------------------
DEFAULT_LAMBDA = 0.25
DEFAULT_TAU_LOW = 200000.0   
DEFAULT_TAU_HIGH = 200000.0  

PURPOSE_WEIGHT = {
    "leisure": (0.4, 0.6),
    "family":  (0.4, 0.6),
    "premium": (0.4, 0.6),
    "business":(0.6, 0.4),
    "budget":  (0.7, 0.3),
    "long_term":(0.7, 0.3),
}

RATING_FLOOR = {
    "leisure": 7.0,
    "family": 7.0,
    "premium": 7.5,
    "business": 7.0,
    "budget": 6.0,
    "long_term": 6.0,
}

# --------------------------- Core algorithm functions ---------------------------
def is_available(h: Hotel, check_in: str, check_out: str) -> bool:
    # Logic check ngày (giữ nguyên)
    return True 

def hard_filter(hotels: List[Hotel], inp: UserInput) -> List[Hotel]:
    results = []
    floor = RATING_FLOOR.get(inp.purpose, 6.0)
    for h in hotels:
        # So sánh district không phân biệt hoa thường
        if h.district.lower() != inp.district.lower():
            continue
        if h.rating < floor:
            continue
        results.append(h)
    return results

def compute_price_fit(price: float, budget_min: float, budget_max: float,
                      lam: float = DEFAULT_LAMBDA,
                      tau_low: float = DEFAULT_TAU_LOW,
                      tau_high: float = DEFAULT_TAU_HIGH) -> float:
    mid = (budget_min + budget_max) / 2.0
    W = max(1.0, budget_max - budget_min)
    if budget_min <= price <= budget_max:
        val = 1.0 - lam * (2.0 * abs(price - mid) / W)
    elif price < budget_min:
        val = 1.0 - (budget_min - price) / tau_low
    else:
        val = 1.0 - (price - budget_max) / tau_high
    return clamp(val, 0.0, 1.0)

def compute_rating_fit(rating: float) -> float:
    if rating is None: return 0.0
    return clamp(rating / 10.0, 0.0, 1.0)

def compute_score(h: Hotel, inp: UserInput,
                  lam: float = DEFAULT_LAMBDA,
                  tau_low: float = DEFAULT_TAU_LOW,
                  tau_high: float = DEFAULT_TAU_HIGH) -> float:
    w_price, w_rating = PURPOSE_WEIGHT.get(inp.purpose, (0.5, 0.5))
    pf = compute_price_fit(h.price, inp.budget_min, inp.budget_max, lam, tau_low, tau_high)
    rf = compute_rating_fit(h.rating)
    return w_price * pf + w_rating * rf

# --------------------------- Search with bucket expansion ---------------------------
def search_with_expansion(hotels: List[Hotel], inp: UserInput, topN: int = 5,
                          lam: float = DEFAULT_LAMBDA,
                          tau_low: float = DEFAULT_TAU_LOW,
                          tau_high: float = DEFAULT_TAU_HIGH,
                          max_attempts: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    
    attempt = 0
    expanded = False
    W = max(1.0, inp.budget_max - inp.budget_min)
    current_min = inp.budget_min
    current_max = inp.budget_max
    current_tau_high = tau_high

    while True:
        candidates = hard_filter(hotels, inp)
        scored = []
        for h in candidates:
            temp_input = UserInput(inp.district, current_min, current_max, inp.purpose, inp.check_in, inp.check_out)
            sc = compute_score(h, temp_input, lam=lam, tau_low=tau_low, tau_high=current_tau_high)
            if sc > 0:
                scored.append((h, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:topN]

        if top:
            results = []
            for h, sc in top:
                # Trả về Dict đầy đủ các trường
                results.append(asdict(h) | {"score": round(sc, 4)})

            meta = {"attempts": attempt+1, "expanded": expanded, "current_min": current_min, "current_max": current_max}
            return results, meta

        if attempt >= max_attempts:
            return [], {"attempts": attempt, "expanded": expanded, "reason": "no_results"}

        if attempt == 0:
            delta = 0.5 * W
            current_min = max(0.0, inp.budget_min - delta)
            current_max = inp.budget_max + delta
            expanded = True
        elif attempt == 1:
            current_tau_high = current_tau_high * 1.5
        attempt += 1

# --------------------------- JSON Load Functions ---------------------------

def load_hotels_from_json(filepath: str) -> List[Hotel]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Hotels JSON not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    hotels = []
    for h in data:
        # Chuyển đổi an toàn
        try:
            price = float(h.get("price", 0.0))
        except: price = 0.0
        
        try:
            rating = float(h.get("rating", 0.0))
        except: rating = 0.0

        # Tạo object Hotel với đầy đủ trường mới
        hotels.append(Hotel(
            id=int(h.get("id", 0)),
            name=str(h.get("name", "")),
            district=str(h.get("district", "")),
            price=price,
            rating=rating,
            capacity=int(h.get("capacity", 2)),
            amenities=h.get("amenities", []) or [],
            details=str(h.get("details") or ""),
            image=str(h.get("image", "")),
            
            # Các trường mới
            images=h.get("images", []) or [],
            address=str(h.get("address", "")),
            stars=int(h.get("stars", 0)),
            reviews_count=int(h.get("reviews_count", 0)),
            category_reviews=h.get("category_reviews", []) or [],
            
            available_from="2025-01-01",
            available_to="2025-12-31"
        ))
    return hotels   

# --------------------------- Main Recommend Function ---------------------------

def recommend_from_json(user_input: Dict[str, Any], hotels_json_path: str,
                        topN: int | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    
    BUDGET_SPREAD = 0.25 

    # Handle budget logic
    if 'budget' in user_input and user_input['budget'] is not None:
        try:
            budget_val = float(user_input['budget'])
            budget_min = max(0.0, budget_val * (1.0 - BUDGET_SPREAD))
            budget_max = max(0.0, budget_val * (1.0 + BUDGET_SPREAD))
        except:
            raise ValueError("Invalid budget")
    else:
        budget_min = float(user_input.get('budget_min', 500000))
        budget_max = float(user_input.get('budget_max', 2000000))

    ui = UserInput(
        district=user_input.get('district', 'Quận 1'),
        budget_min=budget_min,
        budget_max=budget_max,
        purpose=user_input.get('purpose', 'leisure'),
        check_in=user_input.get('check_in', ''),
        check_out=user_input.get('check_out', ''),
        topN=int(user_input.get('topN', 5))
    )

    if topN is None:
        topN = ui.topN

    hotels = load_hotels_from_json(hotels_json_path)
    results, meta = search_with_expansion(hotels, ui, topN=topN)
    meta['query'] = asdict(ui)
    
    return results, meta