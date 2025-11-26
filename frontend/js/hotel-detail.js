/* frontend/js/hotel-detail.js */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Lấy ID từ URL
    const urlParams = new URLSearchParams(window.location.search);
    const hotelId = urlParams.get('id');

    if (hotelId) {
        // Hiển thị trạng thái đang tải
        document.getElementById('hotel-name').innerText = "Đang tải thông tin...";
        
        // Gọi hàm lấy dữ liệu thật
        fetchHotelDetail(hotelId); 
    } else {
        showError("Không tìm thấy ID khách sạn!");
    }
});

function fetchHotelDetail(id) {
    // BƯỚC QUAN TRỌNG: Lấy dữ liệu từ localStorage (nơi trang Home đã lưu)
    const storedData = localStorage.getItem('lastSearchResults');
    
    if (storedData) {
        const hotels = JSON.parse(storedData);
        
        // Tìm khách sạn có ID khớp với ID trên URL
        // Lưu ý: So sánh dạng String để tránh lỗi '188' khác 188
        const foundHotel = hotels.find(h => String(h.id) === String(id));

        if (foundHotel) {
            renderHotelData(foundHotel);
        } else {
            // Nếu không tìm thấy trong list cũ (hoặc user vào thẳng link mà không qua search)
            // Lúc này mới cần gọi API riêng cho detail (nếu có backend)
            // Hoặc hiển thị lỗi
            showError("Không tìm thấy thông tin khách sạn này trong danh sách.");
        }
    } else {
        showError("Dữ liệu đã hết hạn. Vui lòng quay lại trang chủ tìm kiếm lại.");
    }
}

function renderHotelData(data) {
    // Hàm helper để gán text an toàn
    const setContent = (elementId, value) => {
        const el = document.getElementById(elementId);
        if (el) el.innerText = value || '';
    };

    setContent('hotel-name', data.name);
    setContent('hotel-district', data.district);
    setContent('hotel-rating', data.rating);
    
    // Details
    const detailsEl = document.getElementById('hotel-details-text');
    if (detailsEl) {
        detailsEl.innerText = data.details || "Chưa có mô tả chi tiết cho khách sạn này.";
    }

    // Price
    const priceEl = document.getElementById('hotel-price');
    if (priceEl) {
        priceEl.innerText = data.price 
            ? new Intl.NumberFormat('vi-VN').format(Number(data.price)) 
            : "Liên hệ";
    }

    // Image
    const imgEl = document.getElementById('hotel-img');
    if (imgEl) {
        const imgSrc = data.image || data.photo || data.img_url;
        if (imgSrc) imgEl.src = imgSrc;
        else imgEl.src = '../assets/images/background.jpg';
        
        imgEl.onerror = function() {
            this.src = '../assets/images/background.jpg';
        };
    }

    // Amenities
    const amenitiesContainer = document.getElementById('amenities-container');
    if (amenitiesContainer) {
        amenitiesContainer.innerHTML = '';
        const list = data.amenities || [];
        if (list.length > 0) {
            list.forEach(item => {
                const span = document.createElement('span');
                span.className = 'amenity-tag';
                span.innerText = item;
                amenitiesContainer.appendChild(span);
            });
        } else {
            amenitiesContainer.innerHTML = '<span style="color:#888">Đang cập nhật tiện nghi...</span>';
        }
    }

    // --- MỚI: Xử lý Google Map ---
    const mapContainer = document.getElementById('map-container');
    if (mapContainer) {
        // Tạo chuỗi tìm kiếm: Tên khách sạn + Quận + Thành phố
        const searchQuery = `${data.name}, ${data.district}, Thành phố Hồ Chí Minh`;
        
        // Mã hóa chuỗi để đưa vào URL
        const encodedQuery = encodeURIComponent(searchQuery);

        // Tạo iframe HTML
        // z=15: Độ zoom
        // output=embed: Chế độ nhúng
        const mapHtml = `
            <iframe 
                class="map-frame"
                loading="lazy" 
                allowfullscreen 
                referrerpolicy="no-referrer-when-downgrade"
                src="https://maps.google.com/maps?q=${encodedQuery}&t=&z=15&ie=UTF8&iwloc=&output=embed">
            </iframe>
        `;
        
        mapContainer.innerHTML = mapHtml;
    }
}

function showError(message) {
    const container = document.querySelector('.detail-page-container');
    if (container) {
        container.innerHTML = `
            <div style="text-align:center; margin-top:100px; color: #333;">
                <h2>⚠️ Rất tiếc!</h2>
                <p>${message}</p>
                <a href="../index.html" style="color:#7B61FF; font-weight:600; text-decoration:none; margin-top:20px; display:inline-block;">
                    ← Quay về trang chủ
                </a>
            </div>
        `;
    }
}