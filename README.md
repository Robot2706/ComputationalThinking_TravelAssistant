# 🏨 2rism - Hệ thống Gợi ý Khách sạn Thông minh

2rism là một ứng dụng web giúp người dùng tìm kiếm và nhận gợi ý khách sạn dựa trên vị trí, ngân sách, thời gian và mục đích chuyến đi. Dự án sử dụng FastAPI cho Backend và HTML/CSS/JS thuần cho Frontend.

---

## 🛠️ Yêu cầu Cài đặt (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:
1.  Python 3.8 trở lên.
2.  Visual Studio Code (VS Code).
3.  Extension "Live Server" trên VS Code (để chạy Frontend).

---

## 🚀 Hướng dẫn Cài đặt & Chạy (Step-by-Step)

### Phần 1: Khởi chạy Backend (API)

Backend cần được chạy trước để cung cấp dữ liệu cho Frontend.

Bước 1: Mở Terminal tại thư mục backend
   cd backend

Bước 2: Tạo và kích hoạt môi trường ảo (Virtual Environment)

   * Trên Windows:
     
     py -m venv venv
     
     .\venv\Scripts\activate

   * Trên macOS / Linux:
     
     python3 -m venv venv
     
     source venv/bin/activate

   (Sau khi kích hoạt, bạn sẽ thấy chữ (venv) màu xanh ở đầu dòng lệnh).

Bước 3: Cài đặt thư viện
   pip install -r requirements.txt

Bước 4: Chạy Server
   uvicorn src.main:app --reload

   ✅ Thành công: Terminal báo "Uvicorn running on http://127.0.0.1:8000".
   👉 Kiểm tra API: Truy cập http://127.0.0.1:8000/docs.

---

### Phần 2: Khởi chạy Frontend (Giao diện)

Lưu ý: Không mở trực tiếp file HTML bằng cách click đúp (Double click) vì sẽ bị lỗi chặn API (CORS). Hãy dùng Live Server.

1.  Mở VS Code tại thư mục gốc của dự án.
2.  Tìm đến file trang chủ:
    frontend/mainpage/mainmenu/mainmenu-page.html
3.  Chuột phải vào file này và chọn "Open with Live Server".
4.  Trình duyệt sẽ tự mở trang web.

---

## 🧪 Cách sử dụng

1.  Tại trang chủ, nhập thông tin vào thanh tìm kiếm:
    * Location: Nhập tên quận (ví dụ: "District 1").
    * Budget: Nhập khoảng giá (Min - Max).
    * Date: Chọn ngày nhận/trả phòng trên lịch.
    * Guests: Chọn số lượng người.
2.  Bấm nút Tìm kiếm (Kính lúp màu tím).
3.  Trang web sẽ tự động trượt xuống và hiển thị danh sách khách sạn phù hợp nhất từ Backend.
