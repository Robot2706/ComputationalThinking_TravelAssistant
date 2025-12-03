# 🏨 2rism - Hệ thống Gợi ý Khách sạn Thông minh

2rism là một ứng dụng web giúp người dùng tìm kiếm và nhận gợi ý khách sạn dựa trên vị trí, ngân sách, thời gian và mục đích chuyến đi. Dự án sử dụng FastAPI cho Backend và HTML/CSS/JS thuần cho Frontend.

---

## 🛠️ Yêu cầu Cài đặt (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:
1.  Python 3.8 trở lên.
2.  Node.js & npm (https://nodejs.org/).
3.  Visual Studio Code (VS Code).

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

Frontend sử dụng Vite làm build tool và Firebase cho authentication.

**Lưu ý**: Mở Terminal mới riêng cho Frontend, không cần kích hoạt venv.

Bước 1: Mở Terminal tại thư mục frontend
   cd frontend

Bước 2: Cài đặt các dependencies (lần đầu tiên)
   npm install

   (Lần sau chỉ cần chạy bước 3, không cần chạy bước 2 lại)
   * Nếu nó hiện thông báo như thế này: 
   npm : File C:\Program Files\nodejs\npm.ps1 cannot be loaded because running scripts is disabled on this system....

   - thì cần vào powershell (chạy quyền admin) kiểm tra: Get-ExecutionPolicy. Nếu nó ghi Restricted thì ghi thêm lệnh:
      Set-ExecutionPolicy RemoteSigned -Scope CurrentUser, rùi ấn Y -> enter.
Bước 3: Chạy Development Server
   npm run dev

   ✅ Thành công: Terminal báo "VITE vX.X.X ready in XXX ms" và "Local: http://localhost:5173/".
   👉 Mở trình duyệt và truy cập http://localhost:5173/

Bước 4: Dừng Server
   Nhấn Ctrl + C trong Terminal

---

**🎯 Chạy cùng lúc Backend + Frontend:**

* Terminal 1 (Backend - dùng venv):
  ```bash
  cd backend
  source venv/bin/activate
  uvicorn src.main:app --reload
  ```

* Terminal 2 (Frontend - không cần venv):
  ```bash
  cd frontend
  npm run dev
  ```

---

## 🧪 Cách sử dụng

### Đăng ký / Đăng nhập
1.  Trên trang chủ, bấm nút "Sign up/Sign in" ở góc trên phải.
2.  Chọn đăng ký (Sign up) hoặc đăng nhập (Login):
    * **Đăng ký**: Nhập tên, email, mật khẩu (tối thiểu 8 ký tự).
    * **Đăng nhập**: Nhập email và mật khẩu.
    * **Google**: Bấm nút "Continue with Google" để đăng nhập nhanh.
3.  Sau khi đăng nhập thành công, tên bạn sẽ hiện trên navbar.

### Tìm kiếm khách sạn
1.  Trên trang chủ, nhập thông tin vào thanh tìm kiếm:
    * Location: Nhập tên quận (ví dụ: "District 1").
    * Budget: Nhập khoảng giá (Min - Max).
    * Dates: Chọn ngày nhận/trả phòng.
    * Guests: Chọn số lượng người.
2.  Bấm nút Tìm kiếm (Kính lúp).
3.  Danh sách khách sạn phù hợp sẽ hiển thị dưới hero section.

### Các tính năng khác
* **Chat with AI**: Tư vấn lựa chọn khách sạn bằng AI.
* **About Us**: Thông tin về dự án.
* **Hotel Details**: Xem chi tiết từng khách sạn.
