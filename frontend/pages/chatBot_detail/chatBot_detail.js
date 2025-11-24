const cards = document.querySelectorAll(".hotel-card");
const cardList = document.getElementById("cardList");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");

// Lấy dữ liệu từ localStorage
const hotelList = JSON.parse(localStorage.getItem("hotelList")) || [];
let currentIndex = parseInt(localStorage.getItem("selectedHotelIndex")) || 0;

// Gắn dữ liệu vào tất cả card
cards.forEach((card, index) => {
    const hotel = hotelList[index];
    if(hotel){
        card.querySelector(".card-title").textContent = hotel.name;
        card.querySelector(".card-rating").textContent = hotel.rating;
        card.querySelector(".card-description").textContent = hotel.description;
    }
});

// Hàm cập nhật hiển thị carousel
function updateCarousel(){
    const activeCard = cards[currentIndex];
    const container = cardList.parentElement;
    
    // Tính vị trí center của card so với container
    const cardCenter = activeCard.offsetLeft + activeCard.offsetWidth / 2;
    const containerCenter = container.offsetWidth / 2;

    const translateX = cardCenter - containerCenter;

    cardList.style.transform = `translateX(${-translateX}px)`;
}

// Nút prev/next
prevBtn?.addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + cards.length) % cards.length;
    updateCarousel();
});
nextBtn?.addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % cards.length;
    updateCarousel();
});

// Load trang
document.addEventListener("DOMContentLoaded", () => {
    updateCarousel();

    // Home button
    const homeBtn = document.getElementById("goHome");
    homeBtn?.addEventListener("click", () => {
        window.location.href = "../chatBot_result/chatBot_result.html";
    });
});