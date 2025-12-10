"""
Recommender module for Hotel Recommendation POC

Updates v3:
- Enhanced rating_fit with hotel stars and purpose matching
- Strong penalty for hotels outside tau range
- NEW: Amenities matching system with purpose-based preferences
- Dynamic lambda selection
- District classification with dynamic tau
"""

from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Dict, Any, Set
from datetime import datetime, date
import json
import os
import math
import re

# --------------------------- Utilities ---------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def parse_date(d: str) -> date:
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except:
        return date.today()

# --------------------------- District Classification ---------------------------

DISTRICT_TIERS = {
    "center": [
        "Quận 1", "Quận 3", "Quận 4", "Quận 7",
        "Quận Phú Nhuận", "Quận Bình Thạnh"
    ],
    "mid": [
        "Quận 5", "Quận 6", "Quận 8", "Quận 10",
        "Quận 11", "Quận Tân Bình", "Quận Tân Phú", "Quận Gò Vấp"
    ],
    "outer": [
        "Quận 12", "Quận Bình Tân", "Thành phố Thủ Đức"
    ]
}

def get_district_tier(district: str) -> str:
    """Phân loại quận thành center, mid, hoặc outer."""
    for tier, districts in DISTRICT_TIERS.items():
        if district in districts:
            return tier
    return "mid"

# --------------------------- Amenities Configuration ---------------------------

# Chuẩn hóa danh sách amenities thành các categories
AMENITY_CATEGORIES = {
    # Connectivity & Technology
    "wifi": ["wi-fi", "wi fi", "wifi", "wifi miễn phí", "wifi miễn"],
    
    # Room Services
    "room_service": ["dịch vụ phòng", "room service", "dọn phòng"],
    "minibar": ["minibar", "tủ lạnh"],
    "safe": ["két an toàn"],
    "hairdryer": ["máy sấy tóc"],
    "tea_coffee": ["máy pha trà", "máy pha cà phê", "máy pha trà/cà phê"],
    "air_conditioning": ["điều hòa", "air conditioning"],
    
    # Facilities
    "restaurant": ["nhà hàng", "restaurant"],
    "bar": ["bar"],
    "pool": ["bể bơi", "pool"],
    "gym": ["phòng gym", "fitness", "gym"],
    "spa": ["spa", "massage"],
    
    # Services
    "reception_24h": ["quầy lễ tân 24 giờ", "reception"],
    "breakfast": ["bữa sáng", "buffet", "phục vụ bữa sáng"],
    "currency_exchange": ["đổi ngoại tệ", "dịch vụ thu đổi ngoại tệ"],
    "parking": ["bãi đỗ xe", "parking"],
    "airport_shuttle": ["đưa đón sân bay", "airport shuttle"],
    
    # Business
    "meeting_room": ["phòng họp", "meeting room", "conference"],
    "business_center": ["trung tâm kinh doanh", "business center"],
    
    # Family
    "kids_pool": ["bể bơi trẻ em", "kids pool"],
    "playground": ["khu vui chơi trẻ em", "playground"],
    "babysitting": ["trông trẻ", "babysitting"],
    
    # Common areas
    "lobby": ["phòng chờ", "lobby"],
}

def normalize_amenity(amenity: str) -> str:
    """
    Chuẩn hóa amenity về category chuẩn.
    Ví dụ: "wi-fi" -> "wifi", "dịch vụ phòng" -> "room_service"
    """
    amenity_lower = amenity.lower().strip()
    
    for category, keywords in AMENITY_CATEGORIES.items():
        for keyword in keywords:
            if keyword in amenity_lower or amenity_lower in keyword:
                return category
    
    # Nếu không match category nào, trả về chính nó (đã lowercase)
    return re.sub(r'[^a-z0-9_]', '_', amenity_lower)

def get_hotel_amenities_set(hotel_amenities: List[str]) -> Set[str]:
    """
    Chuyển danh sách amenities của hotel thành set các categories chuẩn hóa.
    """
    normalized = set()
    for amenity in hotel_amenities:
        normalized.add(normalize_amenity(amenity))
    return normalized

# --------------------------- Purpose-Based Amenities Preferences ---------------------------

# Cấu trúc: {purpose: {amenity_category: weight}}
# Weight càng cao = càng quan trọng cho purpose đó
PURPOSE_AMENITY_PREFERENCES = {
    "business": {
        # Must-have (weight cao)
        "wifi": 1.0,              # Cực kỳ quan trọng
        "business_center": 0.9,   # Rất quan trọng
        "meeting_room": 0.9,
        "reception_24h": 0.8,
        
        # Important
        "room_service": 0.7,
        "breakfast": 0.7,
        "air_conditioning": 0.6,
        "parking": 0.6,
        "airport_shuttle": 0.5,
        
        # Nice to have
        "restaurant": 0.5,
        "gym": 0.4,
        "safe": 0.4,
    },
    
    "leisure": {
        # Must-have
        "wifi": 0.8,
        "pool": 0.9,              # Rất quan trọng cho du lịch
        "restaurant": 0.8,
        "breakfast": 0.8,
        
        # Important
        "bar": 0.7,
        "spa": 0.7,
        "gym": 0.6,
        "air_conditioning": 0.7,
        "room_service": 0.6,
        
        # Nice to have
        "airport_shuttle": 0.5,
        "reception_24h": 0.5,
    },
    
    "family": {
        # Must-have
        "wifi": 0.7,
        "pool": 0.9,
        "kids_pool": 1.0,         # Cực kỳ quan trọng
        "playground": 0.9,
        "breakfast": 0.9,
        "restaurant": 0.8,
        
        # Important
        "babysitting": 0.8,
        "room_service": 0.7,
        "air_conditioning": 0.8,
        "safe": 0.6,
        
        # Nice to have
        "parking": 0.6,
        "reception_24h": 0.5,
    },
    
    "budget": {
        # Must-have (ít hơn, tập trung vào basics)
        "wifi": 0.9,              # Wifi là quan trọng nhất
        "air_conditioning": 0.8,
        "reception_24h": 0.6,
        
        # Important
        "breakfast": 0.5,         # Có thì tốt
        "room_service": 0.4,
        
        # Nice to have
        "parking": 0.3,
        "restaurant": 0.3,
    },
    
    "premium": {
        # Must-have (yêu cầu cao)
        "wifi": 1.0,
        "spa": 1.0,
        "pool": 0.9,
        "gym": 0.9,
        "restaurant": 0.9,
        "bar": 0.8,
        "room_service": 1.0,
        
        # Important
        "breakfast": 0.8,
        "safe": 0.8,
        "minibar": 0.8,
        "tea_coffee": 0.7,
        "business_center": 0.7,
        "parking": 0.7,
        "airport_shuttle": 0.7,
        
        # Nice to have
        "reception_24h": 0.6,
        "currency_exchange": 0.5,
    },
    
    "long_term": {
        # Must-have (sống lâu dài)
        "wifi": 1.0,              # Cực kỳ quan trọng
        "air_conditioning": 0.9,
        "room_service": 0.8,
        "minibar": 0.7,
        "tea_coffee": 0.8,        # Quan trọng cho dài ngày
        
        # Important
        "breakfast": 0.6,
        "restaurant": 0.7,
        "parking": 0.8,           # Quan trọng cho ở lâu
        "gym": 0.6,
        "pool": 0.5,
        
        # Nice to have
        "reception_24h": 0.5,
        "safe": 0.6,
    },
}

def compute_amenities_fit(hotel_amenities: List[str], purpose: str) -> float:
    """
    Tính amenities fit score dựa trên:
    1. Danh sách amenities của hotel
    2. Danh sách amenities ưu tiên cho purpose
    
    Algorithm:
    - Weighted Match Score: Tổng weight của các amenities match
    - Normalized by total possible weight
    
    Returns:
        float in [0, 1]: 1.0 = có tất cả amenities quan trọng
    """
    if not hotel_amenities:
        return 0.3  # Neutral score nếu không có thông tin
    
    # Lấy preferences cho purpose
    preferences = PURPOSE_AMENITY_PREFERENCES.get(purpose, PURPOSE_AMENITY_PREFERENCES["leisure"])
    
    if not preferences:
        return 0.5  # Neutral nếu purpose không có preferences
    
    # Chuẩn hóa amenities của hotel
    hotel_amenities_set = get_hotel_amenities_set(hotel_amenities)
    
    # Tính weighted match score
    matched_weight = 0.0
    total_weight = 0.0
    
    for amenity_category, weight in preferences.items():
        total_weight += weight
        if amenity_category in hotel_amenities_set:
            matched_weight += weight
    
    # Normalize
    if total_weight == 0:
        return 0.5
    
    base_score = matched_weight / total_weight
    
    # Bonus: Nếu có nhiều amenities hơn expected -> bonus nhỏ
    extra_amenities = len(hotel_amenities_set) - len(preferences)
    if extra_amenities > 0:
        bonus = min(0.1, extra_amenities * 0.02)  # Max 10% bonus
        base_score = min(1.0, base_score + bonus)
    
    return clamp(base_score, 0.0, 1.0)

# --------------------------- Tau Configuration ---------------------------

TAU_CONFIG = {
    "budget": {
        "center": (0.25, 0.05),
        "mid": (0.23, 0.07),
        "outer": (0.20, 0.10)
    },
    "business": {
        "center": (0.20, 0.20),
        "mid": (0.15, 0.25),
        "outer": (0.10, 0.30)
    },
    "leisure": {
        "center": (0.15, 0.20),
        "mid": (0.13, 0.25),
        "outer": (0.10, 0.30)
    },
    "family": {
        "center": (0.25, 0.25),
        "mid": (0.20, 0.27),
        "outer": (0.15, 0.30)
    },
    "premium": {
        "center": (0.10, 0.30),
        "mid": (0.05, 0.35),
        "outer": (0.03, 0.40)
    },
    "long_term": {
        "center": (0.40, 0.05),
        "mid": (0.35, 0.10),
        "outer": (0.30, 0.15)
    }
}

def compute_tau_values(budget_mid: float, purpose: str, district_tier: str) -> Tuple[float, float]:
    config = TAU_CONFIG.get(purpose, TAU_CONFIG["leisure"])
    tier_config = config.get(district_tier, config["mid"])
    
    tau_low_percent, tau_high_percent = tier_config
    tau_low = budget_mid * tau_low_percent
    tau_high = budget_mid * tau_high_percent
    
    return tau_low, tau_high

# --------------------------- Lambda selection ---------------------------

def pick_lambda(budget_min: float, budget_max: float, purpose: str = "leisure") -> float:
    mid = (float(budget_min) + float(budget_max)) / 2.0
    if mid < 1_000_000:
        base = 0.7
    elif mid <= 2_000_000:
        base = 0.5
    else:
        base = 0.3

    purpose_adjust = {
        "business": -0.13,
        "premium": -0.15,
        "leisure": 0.01,
        "family": 0.03,
        "budget": 0.10,
        "long_term": 0.05,
    }
    adj = purpose_adjust.get(purpose, 0.0)
    lam = clamp(base + adj, 0.1, 0.9)
    return lam

# --------------------------- Star Rating Configuration ---------------------------

PURPOSE_STAR_PREFERENCE = {
    "budget": (1, 3),
    "leisure": (3, 4),
    "family": (3, 4),
    "business": (3, 5),
    "premium": (4, 5),
    "long_term": (2, 4),
}

def compute_star_fit(hotel_stars: int, purpose: str) -> float:
    if hotel_stars <= 0:
        return 0.5
    
    min_preferred, max_preferred = PURPOSE_STAR_PREFERENCE.get(purpose, (2, 4))
    
    if min_preferred <= hotel_stars <= max_preferred:
        return 1.0
    elif hotel_stars < min_preferred:
        gap = min_preferred - hotel_stars
        return clamp(1.0 - (gap * 0.15), 0.3, 1.0)
    else:
        gap = hotel_stars - max_preferred
        return clamp(1.0 - (gap * 0.10), 0.5, 1.0)

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
    images: List[str] = field(default_factory=list)
    address: str = ""
    stars: int = 0
    reviews_count: int = 0
    category_reviews: List[Dict] = field(default_factory=list)
    available_from: str = "2025-01-01"
    available_to: str = "2025-12-31"

# --------------------------- Purpose Weights ---------------------------

# ===== UPDATED: Bổ sung weight cho amenities =====
PURPOSE_WEIGHT = {
    # (price_weight, rating_weight, amenities_weight)
    "leisure": (0.35, 0.45, 0.20),   # 35% price, 45% rating, 20% amenities
    "family":  (0.35, 0.40, 0.25),   # Amenities quan trọng hơn cho gia đình
    "premium": (0.20, 0.50, 0.30),   # Premium quan tâm rating và amenities
    "business":(0.30, 0.45, 0.25),   # Business cần amenities phù hợp
    "budget":  (0.70, 0.20, 0.10),   # Budget ưu tiên giá
    "long_term":(0.55, 0.25, 0.20),  # Long term cần amenities nhưng giá quan trọng
}

RATING_FLOOR = {
    "leisure": 7.0,
    "family": 6.5,
    "premium": 8.0,
    "business": 6.8,
    "budget": 5.5,
    "long_term": 6.0,
}

# --------------------------- Core Algorithm Functions ---------------------------

def is_available(h: Hotel, check_in: str, check_out: str) -> bool:
    try:
        a_from = parse_date(h.available_from)
        a_to = parse_date(h.available_to)
        ci = parse_date(check_in)
        co = parse_date(check_out)
    except Exception:
        return True
    return (a_from <= ci) and (a_to >= co)

def hard_filter(hotels: List[Hotel], inp: UserInput) -> List[Hotel]:
    results = []
    floor = RATING_FLOOR.get(inp.purpose, 6.0)
    for h in hotels:
        if h.district.lower() != inp.district.lower():
            continue
        if h.rating < floor:
            continue
        results.append(h)
    return results

def compute_price_fit(price: float, budget_min: float, budget_max: float,
                      lam: float, tau_low: float, tau_high: float) -> float:
    """Price fit với exponential penalty ngoài tau range."""
    mid = (budget_min + budget_max) / 2.0
    W = max(1.0, budget_max - budget_min)
    
    if budget_min <= price <= budget_max:
        val = 1.0 - lam * (2.0 * abs(price - mid) / W)
        return clamp(val, 0.0, 1.0)
    
    elif price < budget_min:
        deviation = budget_min - price
        if deviation <= tau_low:
            val = 1.0 - (deviation / tau_low) * 0.3
        else:
            excess = deviation - tau_low
            decay_rate = 0.0005
            val = 0.7 * math.exp(-decay_rate * excess)
        return clamp(val, 0.0, 1.0)
    
    else:
        deviation = price - budget_max
        if deviation <= tau_high:
            val = 1.0 - (deviation / tau_high) * 0.3
        else:
            excess = deviation - tau_high
            decay_rate = 0.0003
            val = 0.7 * math.exp(-decay_rate * excess)
        return clamp(val, 0.0, 1.0)

def compute_rating_fit(rating: float, hotel_stars: int, purpose: str, 
                       reviews_count: int = 0) -> float:
    """Enhanced rating fit với stars và reviews count."""
    if rating is None or rating <= 0:
        base_rating_fit = 0.0
    else:
        base_rating_fit = clamp(rating / 10.0, 0.0, 1.0)
    
    star_fit = compute_star_fit(hotel_stars, purpose)
    
    if reviews_count > 0:
        confidence = min(1.0, math.log10(reviews_count + 1) / 3.0)
    else:
        confidence = 0.5
    
    purpose_rating_importance = {
        "premium": 1.2,
        "business": 1.1,
        "leisure": 1.0,
        "family": 1.0,
        "budget": 0.8,
        "long_term": 0.9,
    }
    importance = purpose_rating_importance.get(purpose, 1.0)
    
    rating_component = base_rating_fit * 0.50
    star_component = star_fit * 0.30
    confidence_component = confidence * 0.20
    
    combined = (rating_component + star_component + confidence_component) * importance
    
    return clamp(combined, 0.0, 1.0)

def compute_score(h: Hotel, inp: UserInput, lam: float, 
                  tau_low: float, tau_high: float) -> float:
    """
    ===== UPDATED: Tích hợp amenities fit vào tổng điểm =====
    Score = w_price * price_fit + w_rating * rating_fit + w_amenities * amenities_fit
    """
    # Lấy weights cho purpose (bây giờ có 3 components)
    weights = PURPOSE_WEIGHT.get(inp.purpose, (0.4, 0.4, 0.2))
    w_price, w_rating, w_amenities = weights
    
    # Tính 3 components
    pf = compute_price_fit(h.price, inp.budget_min, inp.budget_max, 
                          lam, tau_low, tau_high)
    
    rf = compute_rating_fit(h.rating, h.stars, inp.purpose, h.reviews_count)
    
    af = compute_amenities_fit(h.amenities, inp.purpose)
    
    # Tổng hợp
    total_score = w_price * pf + w_rating * rf + w_amenities * af
    
    return total_score

# --------------------------- Search with expansion ---------------------------

def search_with_expansion(hotels: List[Hotel], inp: UserInput, topN: int = 5,
                          lam: float | None = None,
                          max_attempts: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Search với amenities matching tích hợp."""
    attempt = 0
    expanded = False
    W = max(1.0, inp.budget_max - inp.budget_min)
    current_min = inp.budget_min
    current_max = inp.budget_max

    district_tier = get_district_tier(inp.district)

    if lam is None:
        lam = pick_lambda(inp.budget_min, inp.budget_max, inp.purpose)

    budget_mid = (current_min + current_max) / 2.0
    tau_low, tau_high = compute_tau_values(budget_mid, inp.purpose, district_tier)
    current_tau_low = tau_low
    current_tau_high = tau_high

    while True:
        candidates = hard_filter(hotels, inp)
        scored = []

        for h in candidates:
            temp_input = UserInput(
                inp.district, current_min, current_max,
                inp.purpose, inp.check_in, inp.check_out
            )
            sc = compute_score(h, temp_input, lam=lam,
                             tau_low=current_tau_low, tau_high=current_tau_high)
            
            if sc > 0.1:
                scored.append((h, sc))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:topN]

        if top:
            results = []
            for h, sc in top:
                hotel_dict = asdict(h)
                hotel_dict["score"] = round(sc, 4)
                
                # Bổ sung: Tính riêng từng component để debug
                pf = compute_price_fit(h.price, current_min, current_max, lam, current_tau_low, current_tau_high)
                rf = compute_rating_fit(h.rating, h.stars, inp.purpose, h.reviews_count)
                af = compute_amenities_fit(h.amenities, inp.purpose)
                
                hotel_dict["score_breakdown"] = {
                    "price_fit": round(pf, 3),
                    "rating_fit": round(rf, 3),
                    "amenities_fit": round(af, 3)
                }
                
                results.append(hotel_dict)

            meta = {
                "attempts": attempt + 1,
                "expanded": expanded,
                "district_tier": district_tier,
                "current_min": current_min,
                "current_max": current_max,
                "tau_low": current_tau_low,
                "tau_high": current_tau_high,
                "lambda": lam,
                "total_candidates": len(candidates),
                "scored_candidates": len(scored),
                "weights": {
                    "price": PURPOSE_WEIGHT.get(inp.purpose, (0.4, 0.4, 0.2))[0],
                    "rating": PURPOSE_WEIGHT.get(inp.purpose, (0.4, 0.4, 0.2))[1],
                    "amenities": PURPOSE_WEIGHT.get(inp.purpose, (0.4, 0.4, 0.2))[2]
                }
            }
            return results, meta

        if attempt >= max_attempts:
            return [], {
                "attempts": attempt,
                "expanded": expanded,
                "district_tier": district_tier,
                "reason": "no_results",
                "lambda": lam,
                "total_candidates": len(candidates)
            }

        if attempt == 0:
            delta = 0.5 * W
            current_min = max(0.0, inp.budget_min - delta)
            current_max = inp.budget_max + delta
            budget_mid = (current_min + current_max) / 2.0
            current_tau_low, current_tau_high = compute_tau_values(
                budget_mid, inp.purpose, district_tier
            )
            expanded = True

        elif attempt == 1:
            current_tau_high = current_tau_high * 1.5

        attempt += 1

# --------------------------- JSON Functions ---------------------------

def export_results_to_json(results: List[Dict[str, Any]], meta: Dict[str, Any],
                           filepath: str, indent: int = 2) -> None:
    output = {
        "results": results,
        "meta": meta,
        "timestamp": datetime.now().isoformat()
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=indent)

def load_hotels_from_json(filepath: str) -> List[Hotel]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Hotels JSON not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    hotels = []
    for h in data:
        try:
            price = float(h.get("price", 0.0))
        except: 
            price = 0.0
        
        try:
            rating = float(h.get("rating", 0.0))
        except: 
            rating = 0.0

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
    """Main entrypoint với amenities matching."""
    BUDGET_SPREAD = 0.25

    required_minimal = ['district', 'check_in', 'check_out']
    for k in required_minimal:
        if k not in user_input:
            raise ValueError(f"Missing user input field: {k}")

    purpose = user_input.get('purpose') or "leisure"

    if 'budget' in user_input and user_input['budget'] is not None:
        try:
            budget_val = float(user_input['budget'])
            budget_min = max(0.0, budget_val * (1.0 - BUDGET_SPREAD))
            budget_max = max(0.0, budget_val * (1.0 + BUDGET_SPREAD))
        except:
            raise ValueError("Invalid budget")
    else:
        if 'budget_min' in user_input and 'budget_max' in user_input:
            try:
                budget_min = float(user_input['budget_min'])
                budget_max = float(user_input['budget_max'])
            except Exception:
                raise ValueError("Invalid budget_min/budget_max")
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

# --------------------------- Main Script ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.join(BASE_DIR, "..", "..", "data", "processed", "hotels_parsed.json")

if __name__ == '__main__':
    if not os.path.exists(default_path):
        print(f"Hotels JSON not found at {default_path}")
    else:
        test_cases = [
            {
                'district': 'Quận 1',
                'budget_min': 500000,
                'budget_max': 2000000,
                'purpose': 'business',
                'check_in': '2025-12-24',
                'check_out': '2025-12-25',
                'topN': 5
            },
            {
                'district': 'Quận 10',
                'budget_min': 300000,
                'budget_max': 800000,
                'purpose': 'leisure',
                'check_in': '2025-12-24',
                'check_out': '2025-12-25',
                'topN': 5
            },
            {
                'district': 'Quận 1',
                'budget_min': 1000000,
                'budget_max': 3000000,
                'purpose': 'premium',
                'check_in': '2025-12-24',
                'check_out': '2025-12-25',
                'topN': 5
            }
        ]

        export_dir = os.path.join(BASE_DIR, "..", "results")
        os.makedirs(export_dir, exist_ok=True)

        for i, sample in enumerate(test_cases):
            print(f"\n{'='*60}")
            print(f"Test case {i+1}: {sample['purpose'].upper()} @ {sample['district']}")
            print(f"{'='*60}")
            
            results, meta = recommend_from_json(sample, default_path)
            export_file = os.path.join(export_dir, f"recommend_results_{i+1}.json")
            export_results_to_json(results, meta, export_file)
            
            print(f"✓ Found {len(results)} results")
            print(f"  - Candidates: {meta.get('total_candidates', 0)}")
            print(f"  - Scored: {meta.get('scored_candidates', 0)}")
            print(f"  - Lambda: {meta.get('lambda', 0):.3f}")
            print(f"  - Weights: Price={meta['weights']['price']:.2f}, "
                f"Rating={meta['weights']['rating']:.2f}, "
                f"Amenities={meta['weights']['amenities']:.2f}")
            
            if results:
                print(f"\n  Top 3 hotels:")
                for idx, hotel in enumerate(results[:3], 1):
                    breakdown = hotel.get('score_breakdown', {})
                    print(f"    {idx}. {hotel['name']} (Score: {hotel['score']:.3f})")
                    print(f"       Price: {hotel['price']:,.0f} VND | Rating: {hotel['rating']:.1f} | Stars: {hotel['stars']}")
                    print(f"       Score breakdown: Price={breakdown.get('price_fit', 0):.3f}, "
                        f"Rating={breakdown.get('rating_fit', 0):.3f}, "
                        f"Amenities={breakdown.get('amenities_fit', 0):.3f}")
                    print(f"       Amenities ({len(hotel['amenities'])}): {', '.join(hotel['amenities'][:5])}")
            
            print(f"\n  Exported to {export_file}")