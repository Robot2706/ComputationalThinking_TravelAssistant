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
# 2. CÁC HÀM XỬ LÝ (HELPER FUNCTIONS)
# ==========================================

def extract_district(address_str):
    """
    Trích xuất tên Quận từ chuỗi địa chỉ đầy đủ.
    Ví dụ: "202/1 Đường Lê Thánh Tôn, Quận 1, TP HCM" -> "Quận 1"
    """
    if not isinstance(address_str, str):
        return "Thành phố Hồ Chí Minh"
    
    # Regex bắt các trường hợp: Quận X, District X, TP Thủ Đức
    match = re.search(r'(Quận\s+[\d\w]+|District\s+[\d\w]+|Thành phố\s+Thủ Đức|TP\.\s+Thủ Đức)', address_str, re.IGNORECASE | re.UNICODE)
    
    if match:
        return match.group(0).title() # Viết hoa chữ cái đầu
    return "Thành phố Hồ Chí Minh"

def process_hotel_data(raw_items):
    processed_list = []
    
    # Danh sách tiện nghi mặc định (Do data raw không có list cụ thể)
    default_amenities = [
        "Wi-Fi miễn phí", "Điều hòa không khí", "Lễ tân 24h", 
        "Dịch vụ phòng", "Thang máy", "Tủ lạnh", "Két an toàn"
    ]

    # Dùng enumerate để tạo ID giả nếu trong raw không có ID
    for index, item in enumerate(raw_items):
        
        # 1. Xử lý ID: Nếu không có thì tự tạo dựa trên index + 1
        hotel_id = item.get("id")
        if hotel_id is None:
            hotel_id = index + 1

        # 2. Xử lý Địa chỉ
        # Data raw address là object { full: "...", ... }
        addr_obj = item.get("address", {})
        if isinstance(addr_obj, dict):
            full_address = addr_obj.get("full", "")
        else:
            full_address = str(addr_obj)
            
        district = extract_district(full_address)

        # 3. Xử lý Ảnh
        raw_images = item.get("images", [])
        
        # - Lấy ảnh đầu tiên làm thumbnail (trường 'image')
        thumbnail = raw_images[0] if raw_images else "https://via.placeholder.com/800x600?text=No+Image"
        
        # - Cắt lấy tối đa 10 ảnh cho gallery (trường 'images')
        limited_images = raw_images[:10]

        # 4. Map dữ liệu sang cấu trúc chuẩn
        hotel = {
            "id": hotel_id,
            "name": item.get("name", "Unknown Hotel"),
            "district": district,
            "address": full_address,
            "price": item.get("price", 0),
            "rating": item.get("rating", 0.0),
            "stars": item.get("stars", 3),
            "capacity": 2, # Giá trị mặc định
            
            # Map các trường đổi tên
            "reviews_count": item.get("reviews", 0),
            "category_reviews": item.get("categoryReviews", []),
            "details": item.get("description", ""),
            
            # Ảnh
            "image": thumbnail,
            "images": limited_images,

            # Tiện nghi
            "amenities": default_amenities
        }
        
        processed_list.append(hotel)
    
    return processed_list

# ==========================================
# 3. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    print(f"🔄 Đang đọc dữ liệu từ: {INPUT_PATH}")
    
    # 1. Kiểm tra file đầu vào
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Lỗi: Không tìm thấy file tại {INPUT_PATH}")
        print("👉 Vui lòng tạo file hotels_raw.json và dán dữ liệu vào đó trước.")
        exit(1)

    try:
        # 2. Đọc file JSON raw
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        print(f"   => Tìm thấy {len(raw_data)} khách sạn raw.")

        # 3. Xử lý dữ liệu
        clean_data = process_hotel_data(raw_data)

        # 4. Đảm bảo thư mục đầu ra tồn tại
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 5. Ghi file JSON processed
        with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)

        print("-" * 50)
        print(f"✅ XỬ LÝ THÀNH CÔNG!")
        print(f"📂 File kết quả: {OUTPUT_FILE_PATH}")
        print(f"📊 Tổng số khách sạn: {len(clean_data)}")
        if len(clean_data) > 0:
            print(f"🖼️  Số ảnh gallery của khách sạn đầu tiên: {len(clean_data[0]['images'])}")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")