# 2rism - Hotel Recommender System

Dự án gợi ý khách sạn bao gồm Backend (FastAPI) và Frontend (HTML/CSS/JS).

## 📂 Cấu trúc hiện tại (Current Structure)

```text
Project_Root/
├── backend/                  # Chứa API và thuật toán
│   ├── data/processed/       # Chứa file hotels_parsed.json
│   ├── src/main.py           # File chạy chính của Backend
│   └── requirements.txt      # Thư viện cần cài
│
└── frontend/                 # Giao diện người dùng
    └── mainpage/
        └── mainmenu/
            └── mainmenu-page.html  <-- Trang chủ chính (Chạy file này)

🛠️ Hướng dẫn Chạy Backend (API)

Backend chịu trách nhiệm xử lý dữ liệu và thuật toán gợi ý. Cần chạy nó trước.

Bước 1: Mở Terminal và đi vào thư mục backend

Từ thư mục gốc của dự án, chạy lệnh:
Bash

cd backend

Bước 2: Thiết lập môi trường Python (Chỉ làm lần đầu)

1. Tạo môi trường ảo (venv):

    Windows: py -m venv venv

    Mac/Linux: python3 -m venv venv

2. Kích hoạt môi trường:

    Windows: .\venv\Scripts\activate

    Mac/Linux: source venv/bin/activate (Thấy chữ (venv) hiện ra đầu dòng là thành công)

3. Cài đặt thư viện:
Bash

pip install -r requirements.txt

Bước 3: Khởi động Server

Đảm bảo đang đứng trong thư mục backend, chạy lệnh:
Bash

uvicorn src.main:app --reload

    Nếu thành công, terminal sẽ báo: Uvicorn running on http://127.0.0.1:8000

    API Docs: Truy cập http://127.0.0.1:8000/docs để kiểm tra.

🖥️ Hướng dẫn Chạy Frontend (Giao diện)

Vì đây là web tĩnh (Static Web), không cần cài đặt phức tạp.

Cách tốt nhất: Dùng VS Code Live Server

Để tránh lỗi đường dẫn ảnh hoặc lỗi CORS khi gọi API, hãy dùng Extension Live Server.

    Mở VS Code tại thư mục gốc của dự án.

    Tìm đến file giao diện chính: 👉 Đường dẫn: frontend/mainpage/mainmenu/mainmenu-page.html

    Chuột phải vào file này -> Chọn "Open with Live Server".

Lưu ý quan trọng

    Backend phải đang chạy (Bước 3 ở trên) thì chức năng "Tìm kiếm/Gợi ý" mới hoạt động.

    Nếu bị lỗi, hãy kiểm tra lại xem Live Server có đang mở đúng thư mục gốc (Root) không.