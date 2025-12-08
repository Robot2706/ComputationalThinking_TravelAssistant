document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const hotelId = urlParams.get('id');

    if (hotelId) {
        document.getElementById('hotel-name').innerText = "Đang tải thông tin...";
        // Gọi hàm fetch API
        fetchHotelDetail(hotelId); 
    } else {
        showError("Không tìm thấy ID khách sạn!");
    }
});

// --- IMPORT FIREBASE ---
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js';
import { getFirestore, doc, updateDoc, getDoc, arrayUnion, Timestamp } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';

const firebaseConfig = {
  apiKey: "AIzaSyDF9lK914D_YpHAUNwD2lf8X5q27pH05AY",
  authDomain: "rism-24a9a.firebaseapp.com",
  projectId: "rism-24a9a",
  storageBucket: "rism-24a9a.firebasestorage.app",
  messagingSenderId: "1014525451464",
  appId: "1:1014525451464:web:facd617d7d8c86212019fd",
  measurementId: "G-LR7VE1J9XH"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// --- HÀM MỚI: GỌI TRỰC TIẾP API BACKEND ---
async function fetchHotelDetail(id) {
    try {
        // Gọi endpoint get_hotel mà ta vừa sửa ở Backend
        const response = await fetch(`http://localhost:8000/api/hotels/${id}`);
        
        if (!response.ok) {
            throw new Error("Không tìm thấy khách sạn hoặc lỗi server.");
        }

        const data = await response.json();
        
        // Có dữ liệu từ API -> Render ra màn hình
        renderHotelData(data);
        
        // ✅ SAVE HOTEL HISTORY TO FIREBASE
        await saveHotelHistory(data);

    } catch (error) {
        console.error("Lỗi:", error);
        showError("Không thể tải thông tin khách sạn. Vui lòng thử lại.");
    }
}

// ✅ FUNCTION TO SAVE HOTEL HISTORY
async function saveHotelHistory(hotelData) {
    try {
        // Check if user is logged in
        onAuthStateChanged(auth, async (user) => {
            if (user) {
                const hotelHistory = {
                    id: hotelData.id,
                    name: hotelData.name,
                    district: hotelData.district || hotelData.address,
                    price: hotelData.price,
                    rating: hotelData.rating || 0,
                    image: hotelData.image || hotelData.images?.[0] || '',
                    timestamp: Timestamp.now(),
                    visitedAt: new Date().toISOString()
                };

                try {
                    // Get current hotel history
                    const userDocRef = doc(db, 'users', user.uid);
                    const userDocSnap = await getDoc(userDocRef);
                    
                    let updatedHistory = [];
                    if (userDocSnap.exists() && userDocSnap.data().hotelHistory) {
                        updatedHistory = [...userDocSnap.data().hotelHistory];
                    }
                    
                    // Add new hotel to the beginning
                    updatedHistory.unshift(hotelHistory);
                    
                    // Keep only last 6 hotels
                    if (updatedHistory.length > 6) {
                        updatedHistory = updatedHistory.slice(0, 6);
                    }
                    
                    // Update user's hotel history in Firestore
                    await updateDoc(userDocRef, {
                        hotelHistory: updatedHistory
                    });

                    console.log('✅ Hotel history saved (max 6):', updatedHistory);
                } catch (error) {
                    console.error('❌ Error updating hotel history:', error);
                }
            }
        });
    } catch (error) {
        console.error('❌ Error saving hotel history:', error);
        // Don't throw error - let page load normally even if history save fails
    }
}

function renderHotelData(data) {
    // ... (Giữ nguyên toàn bộ phần logic renderHotelData cũ không cần sửa gì cả) ...
    // ... (Phần render tên, giá, ảnh, sao, map... vẫn hoạt động tốt với data mới) ...
    
    // (Để tiết kiệm không gian chat, bạn giữ nguyên nội dung hàm này từ phiên bản trước nhé)
    // Tôi copy lại đoạn đầu để bạn dễ hình dung vị trí:
    
    const setContent = (id, val) => {
        const el = document.getElementById(id);
        if(el) el.textContent = val;
    };

    setContent('hotel-name', data.name);
    setContent('hotel-address', data.address || data.district);
    
    const priceEl = document.getElementById('hotel-price');
    if(priceEl) priceEl.textContent = new Intl.NumberFormat('vi-VN').format(Number(data.price));
    
    const detailsEl = document.getElementById('hotel-details-text');
    if(detailsEl) detailsEl.innerText = data.details || "Chưa có mô tả.";

    // Stars
    const starsContainer = document.getElementById('hotel-stars');
    if (starsContainer) {
        starsContainer.innerHTML = '';
        const starCount = Number(data.stars) || 0;
        for (let i = 0; i < starCount; i++) {
            starsContainer.innerHTML += '<i class="fa-solid fa-star"></i>';
        }
    }

    // Images
    const mainImg = document.getElementById('hotel-img');
    const thumbList = document.getElementById('gallery-list');
    
    if(mainImg) {
        mainImg.src = data.image || '../assets/images/background.jpg';
        mainImg.onerror = function() { this.src = '../assets/images/background.jpg'; };
    }

    if (thumbList) {
        thumbList.innerHTML = '';
        if (data.images && data.images.length > 0) {
            data.images.forEach((imgUrl, index) => {
                if (index > 4) return; 
                const img = document.createElement('img');
                img.src = imgUrl;
                img.className = 'thumb-img';
                img.onerror = function() { this.style.display = 'none'; }; 
                img.onclick = function() {
                    if(mainImg) mainImg.src = imgUrl;
                    document.querySelectorAll('.thumb-img').forEach(el => el.classList.remove('active'));
                    this.classList.add('active');
                };
                thumbList.appendChild(img);
            });
        }
    }

    // Reviews
    setContent('review-count', data.reviews_count || 0);
    setContent('hotel-rating', data.rating || 0);
    
    const reviewCats = document.getElementById('review-cats');
    if (reviewCats) {
        reviewCats.innerHTML = '';
        if (data.category_reviews && data.category_reviews.length > 0) {
            data.category_reviews.forEach(cat => {
                const score = Number(cat.score);
                const percent = (score / 10) * 100;
                const html = `
                    <div class="review-item">
                        <span>${cat.title}</span>
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div class="review-bar-bg">
                                <div class="review-bar-fill" style="width: ${percent}%"></div>
                            </div>
                            <span style="font-weight:600">${score}</span>
                        </div>
                    </div>
                `;
                reviewCats.innerHTML += html;
            });
        } else {
            reviewCats.innerHTML = '<span style="color:#888; font-size:13px">Chưa có đánh giá chi tiết.</span>';
        }
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

    // Map
// 6. Map (FIXED URL 100%)
    const mapContainer = document.getElementById('map-container');
    if (mapContainer) {
        // Tạo chuỗi tìm kiếm: Tên khách sạn + Quận + Thành phố
        // Thêm "Vietnam" để chính xác hơn
        const searchQuery = `${data.name}, ${data.district}, Thành phố Hồ Chí Minh, Vietnam`;
        
        // Mã hóa URL
        const encodedQuery = encodeURIComponent(searchQuery);
        
        // Sử dụng đường dẫn maps.google.com chuẩn
        const mapHtml = `
            <iframe 
                class="map-frame" 
                loading="lazy" 
                allowfullscreen 
                frameborder="0"
                src="https://maps.google.com/maps?q=${encodedQuery}&t=&z=15&ie=UTF8&iwloc=&output=embed">
            </iframe>`;
            
        mapContainer.innerHTML = mapHtml;
    }
}

function showError(message) {
    const container = document.querySelector('.detail-page-container');
    if (container) {
        container.innerHTML = `<div style="text-align:center; margin-top:100px;"><h2>⚠️ ${message}</h2><a href="../index.html">Quay về trang chủ</a></div>`;
    }
}