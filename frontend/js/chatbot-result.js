/* luồng 1: 
- chatbot hiển thị kết quả sau lọc, so sánh top3, nên là ở phần giao diện này chỉ cần hiển thị 3 card hotel output
- 3 card tĩnh
- hiển thị thông tin ngắn của top3:
    - tên khách sạn
    - rating
    - giới thiệu ngắn
    - giá cả
    - địa chỉ
    - liên hệ
*/

// Giả sử top3 hotel data (thực tế lấy từ API hoặc filter)
const hotels = [
    { name: "Hotel A", rating: "4.5", description: "Giới thiệu ngắn Hotel A..." },
    { name: "Hotel B", rating: "4.0", description: "Giới thiệu ngắn Hotel B..." },
    { name: "Hotel C", rating: "4.8", description: "Giới thiệu ngắn Hotel C..." },
];

// Gắn dữ liệu vào card
document.querySelectorAll(".hotel-card").forEach((card, index) => {
    const hotel = hotels[index];
    card.querySelector(".card-title").textContent = hotel.name;
    card.querySelector(".card-rating").textContent = hotel.rating;
    card.querySelector(".card-description").textContent = hotel.description;

    // Lưu card khi click → chuyển sang detail
    card.addEventListener("click", () => {
        // Lưu index của card được chọn
        localStorage.setItem("selectedHotelIndex", index); 
        // Lưu toàn bộ danh sách hotel để detail có thể đọc
        localStorage.setItem("hotelList", JSON.stringify(hotels)); 

        // Redirect sang chatBot_detail.html
        // Vì folder cùng cấp: ../chatBot_detail/chatBot_detail.html
        window.location.href = "../chatBot_detail/chatBot_detail.html";
    });
});