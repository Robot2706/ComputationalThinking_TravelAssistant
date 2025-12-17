// === FEATURING HOTELS LOGIC ===

document.addEventListener('DOMContentLoaded', () => {
    loadFeaturingHotels();
});

// Hàm lấy top 2 hotels được click nhiều nhất trong tuần từ backend
async function getTopHotelsThisWeek() {
    try {
        console.log('📡 Fetching top hotels from backend...');
        const response = await fetch('http://localhost:8000/api/hotels/top-clicked');
        
        if (!response.ok) {
            console.warn('⚠️ Error fetching top hotels:', response.status);
            return [];
        }
        
        const data = await response.json();
        console.log('📊 Top hotels from backend:', data.hotels);
        return data.hotels || [];
    } catch (e) {
        console.error('❌ Error getting top hotels:', e);
        return [];
    }
}

// Hàm lấy random 2 hotels từ API
async function getRandomHotelsFromAPI() {
    try {
        console.log('📡 Fetching hotels from API...');
        // Thử lấy từ lastSearchResults nếu có
        const savedResults = localStorage.getItem('lastSearchResults');
        if (savedResults) {
            try {
                const hotels = JSON.parse(savedResults);
                if (Array.isArray(hotels) && hotels.length > 0) {
                    console.log('✅ Found', hotels.length, 'hotels in lastSearchResults');
                    const shuffled = hotels.sort(() => Math.random() - 0.5);
                    return shuffled.slice(0, 2).map(h => {
                        let desc = h.details || h.description || 'Brief description';
                        if (desc.length > 200) {
                            desc = desc.substring(0, 200) + '...';
                        }
                        return {
                            hotelId: h.id,
                            name: h.name || 'Hotel',
                            description: desc,
                            image: h.image || h.photo || 'https://via.placeholder.com/316x380'
                        };
                    });
                }
            } catch (e) {
                console.log('⚠️ Error parsing lastSearchResults:', e);
            }
        }
        
        // Nếu không có lastSearchResults, gọi API
        console.log('📡 Calling API to get hotels...');
        const response = await fetch('http://localhost:8000/api/hotels');
        console.log('📊 API response status:', response.status);
        
        if (!response.ok) {
            console.warn('⚠️ API returned status:', response.status);
            return [];
        }
        
        const hotels = await response.json();
        console.log('📦 API returned:', hotels);
        
        if (!Array.isArray(hotels) || hotels.length === 0) {
            console.warn('⚠️ No hotels returned from API');
            return [];
        }
        
        // Shuffle và lấy 2 cái đầu
        const shuffled = hotels.sort(() => Math.random() - 0.5);
        return shuffled.slice(0, 2).map(h => {
            let desc = h.details || h.description || 'Brief description';
            if (desc.length > 200) {
                desc = desc.substring(0, 200) + '...';
            }
            return {
                hotelId: h.id,
                name: h.name || 'Hotel',
                description: desc,
                image: h.image || h.photo || 'https://via.placeholder.com/316x380'
            };
        });
    } catch (e) {
        console.error('❌ Error getting random hotels from API:', e);
        return [];
    }
}

// Hàm load dữ liệu hotels từ API
async function loadHotelData(hotelIds) {
    try {
        const hotels = [];
        for (const id of hotelIds) {
            const response = await fetch(`http://localhost:8000/api/hotels/${id}`);
            if (response.ok) {
                const data = await response.json();
                let desc = data.details || data.description || 'Brief description';
                if (desc.length > 200) {
                    desc = desc.substring(0, 200) + '...';
                }
                hotels.push({
                    hotelId: data.id,
                    name: data.name || 'Hotel',
                    description: desc,
                    image: data.image || data.photo || 'https://via.placeholder.com/316x380'
                });
            }
        }
        return hotels;
    } catch (e) {
        console.error('Error loading hotel data:', e);
        return [];
    }
}

// Hàm main load featuring hotels
async function loadFeaturingHotels() {
    try {
        // Lấy top hotels từ backend (đã kèm random fallback nếu cần)
        let topHotels = await getTopHotelsThisWeek();
        console.log('🏨 Top hotels to display:', topHotels);
        
        if (topHotels.length === 0) {
            console.warn('⚠️ No hotels returned from backend');
            displayFeaturingHotels([]);
        } else {
            // Load dữ liệu chi tiết cho những hotels này
            const hotelData = await loadHotelData(topHotels);
            displayFeaturingHotels(hotelData);
        }
    } catch (e) {
        console.error('❌ Error in loadFeaturingHotels:', e);
        displayFeaturingHotels([]);
    }
}

// Hàm hiển thị featuring hotels
function displayFeaturingHotels(hotels) {
    const featuringComplete = document.querySelector('.featuring-complete');
    if (!featuringComplete) {
        console.error('❌ .featuring-complete not found');
        return;
    }
    
    console.log('🎬 Displaying', hotels.length, 'featuring hotels');
    
    // Nếu không có hotels, hiển thị placeholder
    if (hotels.length === 0) {
        console.warn('⚠️ No hotels to display');
        featuringComplete.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #888;">No hotels available</p>';
        return;
    }
    
    // Xoá các featuring-group cũ
    featuringComplete.querySelectorAll('.featuring-group').forEach(el => el.remove());
    
    // Thêm hotels mới
    hotels.forEach((hotel, index) => {
        const featuringGroup = document.createElement('div');
        featuringGroup.className = 'featuring-group';
        featuringGroup.style.cursor = 'pointer';
        featuringGroup.innerHTML = `
            <div class="featuring-img" style="background-image: url('${hotel.image}'); background-size: cover; background-position: center; cursor: pointer;" onclick="window.location.href='hotel-detail.html?id=${hotel.hotelId}'"></div>
            <div class="featuring-content">
                <div class="heading300">${hotel.name}</div>
                <div class="paragraph100regular">${hotel.description}</div>
            </div>
        `;
        featuringComplete.appendChild(featuringGroup);
        console.log(`✅ Added hotel ${index + 1}: ${hotel.name}`);
    });
    
    console.log('✅ Featuring hotels displayed:', hotels.length);
}
