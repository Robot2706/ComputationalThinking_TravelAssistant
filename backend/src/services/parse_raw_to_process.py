import json
import os
import re

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN (PATH CONFIGURATION)
# ==========================================

# Đường dẫn file đầu vào (Raw Data)
INPUT_PATH = r"C:\Users\Admin\source\repos\ComputationalThinking_TravelAssistant\backend\data\raw\hotels_raw.json"

# Đường dẫn thư mục đầu ra
OUTPUT_DIR = r"C:\Users\Admin\source\repos\ComputationalThinking_TravelAssistant\backend\data\processed"

# Tên file đầu ra
OUTPUT_FILE_PATH = os.path.join(OUTPUT_DIR, "hotels_parsed.json")

# ==========================================
# 2. TỪ KHÓA ĐỂ PARSE TIỆN NGHI (AMENITIES)
# ==========================================
# Cấu trúc: "Tên hiển thị": ["từ khóa 1", "từ khóa 2", ...]
AMENITY_KEYWORDS = {
    "Wi-Fi miễn phí": ["wifi", "wi-fi", "internet", "mạng không dây"],
    "Điều hòa không khí": ["điều hòa", "máy lạnh", "air conditioning", "a/c"],
    "Lễ tân 24h": ["lễ tân 24", "24/24", "24h"],
    "Dịch vụ phòng": ["dịch vụ phòng", "room service"],
    "Thang máy": ["thang máy", "elevator", "lift"],
    "Tủ lạnh": ["tủ lạnh", "fridge", "refrigerator"],
    "Két an toàn": ["két an toàn", "két sắt", "safe", "safety box"],
    "Hồ bơi": ["hồ bơi", "bể bơi", "pool"],
    "Nhà hàng": ["nhà hàng", "restaurant", "ẩm thực"],
    "Bữa sáng": ["bữa sáng", "ăn sáng", "breakfast"]
}

# ==========================================
# 3. CÁC HÀM XỬ LÝ (HELPER FUNCTIONS)
# ==========================================

def extract_district(address_str):
    """
    Trích xuất tên Quận từ chuỗi địa chỉ.
    """
    if not isinstance(address_str, str):
        return "Quận 1" # Mặc định nếu lỗi
    
    # Regex bắt: Quận X, District X, TP Thủ Đức, Huyện X
    match = re.search(r'(Quận\s+[\d\w]+|District\s+[\d\w]+|Thành phố\s+Thủ Đức|TP\.\s+Thủ Đức|Huyện\s+[\w\s]+)', address_str, re.IGNORECASE | re.UNICODE)
    
    if match:
        return match.group(0).strip().title()
    return "Quận 1"

def extract_amenities_from_text(text):
    """
    Quét văn bản để tìm tiện nghi dựa trên keywords.
    """
    if not text:
        return ["Wi-Fi miễn phí", "Điều hòa không khí"] # Mặc định tối thiểu
    
    text_lower = text.lower()
    found = []
    
    for amenity_name, keywords in AMENITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found.append(amenity_name)
                break # Tìm thấy 1 keyword là đủ cho nhóm này
    
    # Nếu không tìm thấy gì thì trả về list mặc định
    if not found:
        return ["Wi-Fi miễn phí", "Điều hòa không khí", "Lễ tân 24h"]
    
    return found

def process_hotel_data(raw_items):
    processed_list = []
    
    # Dùng enumerate(raw_items, 1) để tạo ID chạy từ 1, 2, 3...
    for index, item in enumerate(raw_items, 1):
        
        # 1. Xử lý Địa chỉ (Raw có thể là object hoặc string)
        addr_raw = item.get("address", {})
        if isinstance(addr_raw, dict):
            full_address = addr_raw.get("full", "")
        else:
            full_address = str(addr_raw)
            
        district = extract_district(full_address)

        # 2. Xử lý Ảnh (Lấy tối đa 10)
        raw_images = item.get("images", [])
        limited_images = raw_images[:10] # Cắt lấy 10 ảnh đầu
        
        # Ảnh đại diện: Ưu tiên trường 'image', nếu không có lấy cái đầu tiên trong list
        thumbnail = item.get("image")
        if not thumbnail and limited_images:
            thumbnail = limited_images[0]
        if not thumbnail:
            thumbnail = "https://via.placeholder.com/800x600?text=No+Image"

        # 3. Xử lý Mô tả & Tiện nghi
        details_text = item.get("description", "") or item.get("details", "")
        
        # Parse amenities từ mô tả
        amenities_list = extract_amenities_from_text(details_text)

        # 4. Map dữ liệu sang cấu trúc chuẩn
        hotel = {
            "id": index, # Tạo ID mới tuần tự 1, 2, 3...
            "name": item.get("name", "Unknown Hotel"),
            "district": district,
            "address": full_address,
            "price": float(item.get("price", 0) or 0),
            "rating": float(item.get("rating", 0) or 0),
            "stars": int(item.get("stars", 3) or 3),
            "capacity": 2, # Mặc định
            
            # Map các trường review
            "reviews_count": int(item.get("reviews", 0) or item.get("reviews_count", 0)),
            "category_reviews": item.get("categoryReviews", []) or [],
            
            "details": details_text,
            
            # Ảnh
            "image": thumbnail,
            "images": limited_images,

            # Tiện nghi đã parse
            "amenities": amenities_list
        }
        
        processed_list.append(hotel)
    
    return processed_list

# ==========================================
# 4. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    print("-" * 50)
    print(f"🔄 Đang đọc dữ liệu từ: {INPUT_PATH}")
    
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Lỗi: Không tìm thấy file tại {INPUT_PATH}")
        exit(1)

    try:
        # Đọc file raw
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        print(f"   => Tìm thấy {len(raw_data)} khách sạn raw.")

        # Xử lý
        clean_data = process_hotel_data(raw_data)

        # Đảm bảo thư mục ra tồn tại
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Ghi file kết quả
        with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)

        # Output kết quả như yêu cầu
        print(f"✅ XỬ LÝ THÀNH CÔNG!")
        print(f"📂 File kết quả: {OUTPUT_FILE_PATH}")
        print(f"📊 Tổng số khách sạn: {len(clean_data)}")
        if len(clean_data) > 0:
            print(f"🖼️  Số ảnh gallery của khách sạn đầu tiên: {len(clean_data[0]['images'])}")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")