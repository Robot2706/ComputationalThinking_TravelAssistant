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
        window.location.href = "./chatBot-review.html";
    });
});

const askInput = document.getElementById("askInput");
const aiMessage = document.getElementById("aiMessage");

askInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && askInput.value.trim() !== "") {
        
        const userText = askInput.value.trim();
        console.log("User asked:", userText);

        // Tạm thời cho AI trả lời cứng
        aiMessage.textContent = `Mình đã nhận câu trả lời: "${userText}". Bạn muốn mình hỗ trợ điều gì thêm?`;

        askInput.value = "";
    }
});