"""
Recommender module for Hotel Recommendation POC

Updates:
- District classification: Center, Mid, Outer
- Dynamic tau_low and tau_high based on purpose and district tier
- Budget expansion logic with single 'budget' value support
- Dynamic lambda selection added (pick_lambda)

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
    """
    Phân loại quận thành center, mid, hoặc outer.
    Mặc định là mid nếu không tìm thấy.
    """
    for tier, districts in DISTRICT_TIERS.items():
        if district in districts:
            return tier
    return "mid"  # default fallback

# --------------------------- Tau Configuration by Purpose and Tier ---------------------------

# Cấu trúc: {purpose: {tier: (tau_low_percent, tau_high_percent)}}
# Các phần trăm này sẽ được nhân với budget để ra tau_low và tau_high
TAU_CONFIG = {
    "budget": {
        "center": (0.25, 0.10),
        "mid": (0.30, 0.10),
        "outer": (0.40, 0.15)
    },
    "business": {
        "center": (0.20, 0.30),
        "mid": (0.20, 0.25),
        "outer": (0.15, 0.20)
    },
    "leisure": {
        "center": (0.25, 0.30),
        "mid": (0.20, 0.25),
        "outer": (0.10, 0.35)
    },
    "family": {
        "center": (0.25, 0.35),
        "mid": (0.20, 0.30),
        "outer": (0.15, 0.25)
    },
    "premium": {
        "center": (0.10, 0.30),
        "mid": (0.15, 0.35),
        "outer": (0.10, 0.40)
    },
    "long_term": {
        "center": (0.40, 0.15),
        "mid": (0.35, 0.15),
        "outer": (0.30, 0.10)
    }
}

def compute_tau_values(budget_mid: float, purpose: str, district_tier: str) -> Tuple[float, float]:
    """
    Tính tau_low và tau_high dựa trên budget, purpose và district tier.

    Args:
        budget_mid: Giá trị budget trung bình (midpoint)
        purpose: Loại hình du lịch
        district_tier: center/mid/outer

    Returns:
        (tau_low, tau_high)
    """
    config = TAU_CONFIG.get(purpose, TAU_CONFIG["leisure"])
    tier_config = config.get(district_tier, config["mid"])

    tau_low_percent, tau_high_percent = tier_config
    tau_low = budget_mid * tau_low_percent
    tau_high = budget_mid * tau_high_percent

    return tau_low, tau_high

# --------------------------- Lambda selection (NEW) ---------------------------

def pick_lambda(budget_min: float, budget_max: float, purpose: str = "leisure") -> float:
    """
    Chọn giá trị lambda dựa trên midpoint của budget và purpose.

    """
    mid = (float(budget_min) + float(budget_max)) / 2.0
    if mid < 1_000_000:
        base = 0.7
    elif mid <= 2_000_000:
        base = 0.5
    else:
        base = 0.3

    # purpose adjustments
    purpose_adjust = {
        "business": -0.15,
        "premium": -0.10,
        "leisure": 0.0,
        "family": 0.05,
        "budget": 0.10,
        "long_term": 0.05,
    }
    adj = purpose_adjust.get(purpose, 0.0)
    lam = clamp(base + adj, 0.1, 0.9)
    return lam

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

DEFAULT_LAMBDA = 0.2


PURPOSE_WEIGHT = {
    "leisure": (0.4, 0.6),
    "family":  (0.5, 0.5),
    "premium": (0.5, 0.5),
    "business":(0.6, 0.4),
    "budget":  (0.9, 0.1),
    "long_term":(0.7, 0.3),
}

RATING_FLOOR = {
    "leisure": 6.5,
    "family": 7.0,
    "premium": 8.0,
    "business": 7.0,
    "budget": 5.5,
    "long_term": 6.0,
}

# --------------------------- Core algorithm functions ---------------------------
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
        # So sánh district không phân biệt hoa thường
        if h.district.lower() != inp.district.lower():
            continue
        if h.rating < floor:
            continue
        results.append(h)
    return results

def compute_price_fit(price: float, budget_min: float, budget_max: float,
                      lam: float, tau_low: float, tau_high: float) -> float:
    """
    Compute price_fit in [0,1] với tau_low và tau_high động.
    """
    mid = (budget_min + budget_max) / 2.0
    W = max(1.0, budget_max - budget_min)

    if budget_min <= price <= budget_max:
        # Inside bucket
        val = 1.0 - lam * (2.0 * abs(price - mid) / W)
    elif price < budget_min:
        # Below bucket - penalty dựa trên tau_low
        val = 1.0 - (budget_min - price) / max(1.0, tau_low)
    else:
        # Above bucket - penalty dựa trên tau_high
        val = 1.0 - (price - budget_max) / max(1.0, tau_high)

    return clamp(val, 0.0, 1.0)

def compute_rating_fit(rating: float) -> float:
    if rating is None: return 0.0
    return clamp(rating / 10.0, 0.0, 1.0)


def compute_score(h: Hotel, inp: UserInput, lam: float, 
                  tau_low: float, tau_high: float) -> float:
    """
    Tính điểm tổng hợp với tau động theo purpose và district tier.
    """
    w_price, w_rating = PURPOSE_WEIGHT.get(inp.purpose, (0.5, 0.5))
    pf = compute_price_fit(h.price, inp.budget_min, inp.budget_max, lam, tau_low, tau_high)
    rf = compute_rating_fit(h.rating)
    return w_price * pf + w_rating * rf

# --------------------------- Search with bucket expansion ---------------------------
def search_with_expansion(hotels: List[Hotel], inp: UserInput, topN: int = 5,
                          lam: float | None = None,
                          max_attempts: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run search với tau_low và tau_high động dựa trên purpose và district tier.
    Nếu lam là None thì tự pick bằng pick_lambda().
    """
    attempt = 0
    expanded = False
    W = max(1.0, inp.budget_max - inp.budget_min)
    current_min = inp.budget_min
    current_max = inp.budget_max

    # Xác định tier của quận
    district_tier = get_district_tier(inp.district)

    # Nếu lam không được truyền vào, tính tự động
    if lam is None:
        lam = pick_lambda(inp.budget_min, inp.budget_max, inp.purpose)

    # Tính tau ban đầu dựa trên budget_mid, purpose và district tier
    budget_mid = (current_min + current_max) / 2.0
    tau_low, tau_high = compute_tau_values(budget_mid, inp.purpose, district_tier)
    current_tau_low = tau_low
    current_tau_high = tau_high

    while True:
        candidates = hard_filter(hotels, inp)
        scored = []

        for h in candidates:
            # Tạo temp input với budget hiện tại
            temp_input = UserInput(
                inp.district, current_min, current_max,
                inp.purpose, inp.check_in, inp.check_out
            )
            sc = compute_score(h, temp_input, lam=lam,
                             tau_low=current_tau_low, tau_high=current_tau_high)
            if sc > 0:
                scored.append((h, sc))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:topN]

        if top:
            results = []
            for h, sc in top:
                # Trả về Dict đầy đủ các trường
                results.append(asdict(h) | {"score": round(sc, 4)})

            meta = {
                "attempts": attempt + 1,
                "expanded": expanded,
                "district_tier": district_tier,
                "current_min": current_min,
                "current_max": current_max,
                "tau_low": current_tau_low,
                "tau_high": current_tau_high,
                "lambda": lam
            }
            return results, meta

        # No results; expand if possible
        if attempt >= max_attempts:
            return [], {
                "attempts": attempt,
                "expanded": expanded,
                "district_tier": district_tier,
                "reason": "no_results",
                "lambda": lam
            }

        if attempt == 0:
            # Expand budget by ±50%
            delta = 0.5 * W
            current_min = max(0.0, inp.budget_min - delta)
            current_max = inp.budget_max + delta

            # Recalculate tau với budget mới
            budget_mid = (current_min + current_max) / 2.0
            current_tau_low, current_tau_high = compute_tau_values(
                budget_mid, inp.purpose, district_tier
            )
            expanded = True

        elif attempt == 1:
            # Relax tau_high further
            current_tau_high = current_tau_high * 1.5

        attempt += 1

# --------------------------- JSON Export / Load Functions ---------------------------

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
    """
    Main entrypoint với hỗ trợ:
    - Single 'budget' value (expand ±25%)
    - Legacy 'budget_min' và 'budget_max'
    - Tự động phân loại district tier
    - Tính tau_low/tau_high động
    """
    BUDGET_SPREAD = 0.25  # ±25%

    required_minimal = ['district', 'check_in', 'check_out']
    for k in required_minimal:
        if k not in user_input:
            raise ValueError(f"Missing user input field: {k}")

    purpose = user_input.get('purpose') or "leisure"

    # Handle budget input
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
                raise ValueError("Invalid numeric values for 'budget_min'/'budget_max'")
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
    # CALL search_with_expansion without passing lam -> pick_lambda will run
    results, meta = search_with_expansion(hotels, ui, topN=topN)
    meta['query'] = asdict(ui)

    return results, meta

# --------------------------- Main Script ---------------------------
if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(BASE_DIR, "..", "..", "data", "processed", "hotels_parsed.json")

    if not os.path.exists(default_path):
        print(f"Default hotels_parsed.json not found at {default_path}")
    else:
        # Test với các quận khác nhau
        test_cases = [
            {
                'district': 'Quận 1',  # Center
                'budget_min': 500000,
                'budget_max': 2000000,
                'purpose': 'business',
                'check_in': '2025-12-24',
                'check_out': '2025-12-25',
                'topN': 5
            },
            {
                'district': 'Quận 10',  # Mid
                'budget_min': 300000,
                'budget_max': 800000,
                'purpose': 'leisure',
                'check_in': '2025-12-24',
                'check_out': '2025-12-25',
                'topN': 5
            },
            {
                'district': 'Quận 12',  # Outer
                'budget_min': 200000,
                'budget_max': 500000,
                'purpose': 'budget',
                'check_in': '2025-12-24',
                'check_out': '2025-12-25',
                'topN': 5
            }
        ]

        export_dir = os.path.join(BASE_DIR, "..", "results")
        os.makedirs(export_dir, exist_ok=True)

        for i, sample in enumerate(test_cases):
            results, meta = recommend_from_json(sample, default_path)
            export_file = os.path.join(export_dir, f"recommend_results_{i+1}.json")
            export_results_to_json(results, meta, export_file)
            print(f"✓ Test case {i+1} ({meta['district_tier']}) exported to {export_file}")
