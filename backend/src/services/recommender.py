"""
Recommender module for Hotel Recommendation POC

Changes in this variant:
- Accepts frontend that provides a single "budget" value instead of separate budget_min/budget_max.
  If `budget` is present in user_input, we expand it to a (budget_min, budget_max) interval by +/-25%.
  If frontend still provides budget_min/budget_max, those are used unchanged (backward compatible).
- If `purpose` is missing from user_input, default to "leisure".
- recommend_from_json validates and normalizes inputs accordingly, then calls existing search logic.
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
    return datetime.strptime(d, "%Y-%m-%d").date()

# --------------------------- Data classes ---------------------------
@dataclass
class UserInput:
    district: str
    budget_min: float
    budget_max: float
    purpose: str  # leisure, business, family, budget, premium, long_term
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
    available_from: str = "2025-01-01"
    available_to: str = "2025-12-31"

# --------------------------- Default parameters ---------------------------
DEFAULT_LAMBDA = 0.25
DEFAULT_TAU_LOW = 200000.0   # scale for below-min penalty
DEFAULT_TAU_HIGH = 200000.0  # scale for above-max penalty

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
    try:
        a_from = parse_date(h.available_from)
        a_to = parse_date(h.available_to)
        ci = parse_date(check_in)
        co = parse_date(check_out)
    except Exception:
        # if dates invalid or missing, treat as available (validation should be done upstream)
        return True
    return (a_from <= ci) and (a_to >= co)


def hard_filter(hotels: List[Hotel], inp: UserInput) -> List[Hotel]:
    """
    Apply basic hard filters:
    - district must match
    - availability must cover check_in..check_out
    - rating must be >= rating floor for purpose
    """
    results = []
    floor = RATING_FLOOR.get(inp.purpose, 6.0)
    for h in hotels:
        if h.district != inp.district:
            continue
        if not is_available(h, inp.check_in, inp.check_out):
            continue
        if h.rating < floor:
            continue
        results.append(h)
    return results


def compute_price_fit(price: float, budget_min: float, budget_max: float,
                      lam: float = DEFAULT_LAMBDA,
                      tau_low: float = DEFAULT_TAU_LOW,
                      tau_high: float = DEFAULT_TAU_HIGH) -> float:
    """
    Compute price_fit in [0,1].
    - inside bucket: 1 - lam * (2 * |price - mid| / W)
      (mid = center, W = width; so value at edges = 1 - lam)
    - below bucket: linear penalty scaled by tau_low
    - above bucket: linear penalty scaled by tau_high
    """
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
    """Normalize rating (0..10) to [0,1]."""
    if rating is None:
        return 0.0
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
    """
    Run search; if no results, attempt up to max_attempts expansions:
      attempt 0 -> widen budget by ±50%·W
      attempt 1 -> relax tau_high (make over-budget penalty milder)
    Returns (results, meta)
    meta contains attempts, expanded flag, and final params
    """
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
            # use current_min/current_max when computing score
            temp_input = UserInput(inp.district, current_min, current_max, inp.purpose, inp.check_in, inp.check_out)
            sc = compute_score(h, temp_input, lam=lam, tau_low=tau_low, tau_high=current_tau_high)
            if sc > 0:
                scored.append((h, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:topN]

        if top:
            results = []
            for h, sc in top:
                results.append({
                    "id": h.id,
                    "name": h.name,
                    "district": h.district,
                    "price": h.price,
                    "rating": h.rating,
                    "capacity": h.capacity,
                    "amenities": h.amenities,
                    "details": h.details,
                    "score": round(sc, 4)
                })

            meta = {"attempts": attempt+1, "expanded": expanded, "current_min": current_min, "current_max": current_max, "tau_high": current_tau_high}
            return results, meta

        # no results; decide if we can expand
        if attempt >= max_attempts:
            return [], {"attempts": attempt, "expanded": expanded, "reason": "no_results"}

        if attempt == 0:
            # widen budget by ±50% of original W
            delta = 0.5 * W
            current_min = max(0.0, inp.budget_min - delta)
            current_max = inp.budget_max + delta
            expanded = True
        elif attempt == 1:
            # relax tau_high to be more permissive for over-budget results
            current_tau_high = current_tau_high * 1.5
        attempt += 1

# --------------------------- JSON Export / Load Functions ---------------------------

def export_results_to_json(results: List[Dict[str, Any]], meta: Dict[str, Any], 
                           filepath: str, indent: int = 2) -> None:
    """
    Export search results and metadata to a JSON file.
    
    Args:
        results: List of hotel dictionaries from search_with_expansion
        meta: Metadata dictionary from search_with_expansion
        filepath: Path to output JSON file
        indent: JSON indentation (default: 2)
    """
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
        # Defensive conversions: ensure numeric fields are correct types
        try:
            price = float(h.get("price", 0.0))
        except Exception:
            price = 0.0
        try:
            rating = float(h.get("rating", 0.0))
        except Exception:
            rating = 0.0
        hotels.append(Hotel(
            id=int(h.get("id", 0)),
            name=h.get("name", ""),
            district=h.get("district", ""),
            price=price,
            rating=rating,
            capacity=int(h.get("capacity", 1)) if h.get("capacity") is not None else 1,
            amenities=h.get("amenities", []) or [],
            details=h.get("details", "") or "",
            available_from=h.get("available_from", "2025-01-01"),
            available_to=h.get("available_to", "2025-12-31")
        ))
    return hotels   

# --------------------------- Frontend / API helper ---------------------------

def recommend_from_json(user_input: Dict[str, Any], hotels_json_path: str,
                        topN: int | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main entrypoint for frontend/backend route.

    Changes to support frontend that passes only `budget`:
    - user_input may contain:
        - 'budget' (single numeric value)  OR
        - 'budget_min' and 'budget_max' (legacy)
    - If 'budget' is present, we build a symmetric interval around it:
        budget_min = budget * (1 - BUDGET_SPREAD)
        budget_max = budget * (1 + BUDGET_SPREAD)
      where BUDGET_SPREAD = 0.25 (25%) by default (configurable below).
    - If 'purpose' is missing, default to 'leisure'.
    - Required fields: district, check_in, check_out (budget is provided as described).
    """
    # config for single-budget expansion
    BUDGET_SPREAD = 0.25  # +/- 25%

    # minimal required keys
    required_minimal = ['district', 'check_in', 'check_out']
    for k in required_minimal:
        if k not in user_input:
            raise ValueError(f"Missing user input field: {k}")

    # normalize purpose
    purpose = user_input.get('purpose') or "leisure"

    # handle budget input
    if 'budget' in user_input and user_input['budget'] is not None:
        try:
            budget_val = float(user_input['budget'])
        except Exception:
            raise ValueError("Invalid numeric value for 'budget'")
        budget_min = max(0.0, budget_val * (1.0 - BUDGET_SPREAD))
        budget_max = max(0.0, budget_val * (1.0 + BUDGET_SPREAD))
    else:
        # fallback to legacy fields if provided
        if 'budget_min' in user_input and 'budget_max' in user_input:
            try:
                budget_min = float(user_input['budget_min'])
                budget_max = float(user_input['budget_max'])
            except Exception:
                raise ValueError("Invalid numeric values for 'budget_min'/'budget_max'")
        else:
            # last resort: use defaults similar to previous behavior
            budget_min = float(user_input.get('budget_min', 500000))
            budget_max = float(user_input.get('budget_max', 2000000))

    # build UserInput object
    ui = UserInput(
        district=user_input['district'],
        budget_min=budget_min,
        budget_max=budget_max,
        purpose=purpose,
        check_in=user_input['check_in'],
        check_out=user_input['check_out'],
        topN=int(user_input.get('topN', 5))
    )

    if topN is None:
        topN = ui.topN

    hotels = load_hotels_from_json(hotels_json_path)

    results, meta = search_with_expansion(hotels, ui, topN=topN)
    meta['query'] = asdict(ui)
    return results, meta

# --------------------------- if run as script ---------------------------
if __name__ == '__main__':
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Đường dẫn tương đối tới file hotels_parsed.json
    default_path = os.path.join(
        BASE_DIR, ".." ,"..", "data", "processed", "hotels_parsed.json"
    )

    if not os.path.exists(default_path):
        print(f"Default hotels_parsed.json not found at {default_path}. Please provide path.")
    else:
        # Sample user input (note: this script uses budget_min/budget_max)
        sample = {
            'district': 'Quận 1',
            'budget_min': 500000,
            'budget_max': 2000000,
            'purpose': 'business',
            'check_in': '2025-11-14',
            'check_out': '2025-11-15',
            'topN': 5
        }

        # Run recommendation
        results, meta = recommend_from_json(sample, default_path)

        # Folder kết quả
        export_dir = os.path.join(BASE_DIR, "..", "results")
        os.makedirs(export_dir, exist_ok=True)

        # Export JSON ra results/recommend_results.json
        export_file = os.path.join(export_dir, "recommend_results.json")
        export_results_to_json(results, meta, export_file)

        print(f"✓ Recommendation exported to {export_file}")
