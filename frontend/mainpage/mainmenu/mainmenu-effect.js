document.addEventListener('DOMContentLoaded', function() {
    
    /* =========================================
       1. KHAI BÁO BIẾN
       ========================================= */
    // Các phần tử chính
    const searchBtn = document.querySelector('.search-button-purple');
    const heroSection = document.querySelector('.hero-section');
    const whiteSection = document.querySelector('.white-section');
    
    // Biến cho Popup
    const guestTrigger = document.getElementById('guest-trigger');
    const guestPopup = document.getElementById('guest-popup');
    const btnMinus = document.getElementById('btn-minus');
    const btnPlus = document.getElementById('btn-plus');
    const guestCountNum = document.getElementById('guest-count-number');
    const guestDisplay = document.getElementById('guest-display');

    const dateTrigger = document.getElementById('date-trigger');
    const calendarPopup = document.getElementById('calendar-popup');
    const dateDisplay = document.getElementById('date-display');
    const days = document.querySelectorAll('.day-num');

    // Chỉ số khách
    let currentGuests = 1;
    const MIN_GUESTS = 1;
    const MAX_GUESTS = 7;

    /* =========================================
       2. LOGIC SCROLL & SEARCH BUTTON (MỚI)
       ========================================= */
    
    // Logic cuộn trang: Khi cuộn > 50px thì thu nhỏ Header
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            heroSection.classList.add('shrink');
        } else {
            heroSection.classList.remove('shrink');
        }
    });

    // Logic Nút Tìm Kiếm
    /* =========================================
       LOGIC SEARCH BUTTON: BIẾN HÌNH & KHÓA CUỘN
       ========================================= */
    
    // Biến kiểm tra xem đã khóa chưa
    let isLocked = false;

    // Logic cuộn trang cho hiệu ứng shrink (Chỉ chạy khi CHƯA khóa)
    window.addEventListener('scroll', () => {
        if (isLocked) return; // Nếu đã khóa thì không làm gì cả, để CSS tự lo

        if (window.scrollY > 50) {
            heroSection.classList.add('shrink');
        } else {
            heroSection.classList.remove('shrink');
        }
    });

    // Logic Nút Tìm Kiếm
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            
            // BƯỚC 1: Mở khóa cuộn và lướt xuống cho đẹp
            document.body.style.overflowY = 'auto';
            if (whiteSection) {
                whiteSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            // Đóng các popup
            if (guestPopup) guestPopup.classList.remove('active');
            if (calendarPopup) calendarPopup.classList.remove('active');

            // BƯỚC 2: SAU KHI LƯỚT XONG (Khoảng 800ms) -> KHÓA LẠI
            setTimeout(() => {
                // Bật cờ khóa
                isLocked = true; 

                // Thêm class đặc biệt vào body để kích hoạt CSS ở Bước 1
                document.body.classList.add('mode-locked');
                
                // Đảm bảo Hero có class shrink
                heroSection.classList.add('shrink');

                // QUAN TRỌNG: Reset thanh cuộn về 0
                // Vì lúc này margin-top của white-section đã bị xóa (nhờ CSS), 
                // nên vị trí 0 bây giờ chính là ngay đầu trang nội dung.
                window.scrollTo(0, 0); 

            }, 800); // Thời gian chờ khớp với thời gian lướt xuống
        });
    }


    /* =========================================
       3. LOGIC CHO GUEST COUNTER (CŨ)
       ========================================= */
    if (guestTrigger) {
        guestTrigger.addEventListener('click', (e) => {
            if (e.target.closest('.counter-btn')) return; 
            guestPopup.classList.toggle('active');
            if (calendarPopup) calendarPopup.classList.remove('active');
            e.stopPropagation();
        });
    }

    if (btnPlus) {
        btnPlus.addEventListener('click', (e) => {
            e.stopPropagation();
            if (currentGuests < MAX_GUESTS) {
                currentGuests++;
                updateGuestUI();
            }
        });
    }

    if (btnMinus) {
        btnMinus.addEventListener('click', (e) => {
            e.stopPropagation();
            if (currentGuests > MIN_GUESTS) {
                currentGuests--;
                updateGuestUI();
            }
        });
    }

    function updateGuestUI() {
        if (guestCountNum) guestCountNum.textContent = currentGuests;
        if (guestDisplay) {
            guestDisplay.textContent = `${currentGuests} guest${currentGuests > 1 ? 's' : ''}`;
            guestDisplay.style.color = "#000";
            guestDisplay.style.fontWeight = "600";
        }
    }

    /* =========================================
       4. LOGIC CHO CALENDAR (CŨ)
       ========================================= */
    if (dateTrigger) {
        dateTrigger.addEventListener('click', (e) => {
            calendarPopup.classList.toggle('active');
            if (guestPopup) guestPopup.classList.remove('active');
            e.stopPropagation();
        });
    }

    if (days) {
        days.forEach(day => {
            day.addEventListener('click', (e) => {
                e.stopPropagation();
                days.forEach(d => d.classList.remove('selected'));
                e.target.classList.add('selected');
                
                const dayVal = e.target.textContent;
                if (dateDisplay) {
                    dateDisplay.textContent = `Nov ${dayVal} - Dec 2`; 
                    dateDisplay.style.color = "#000";
                    dateDisplay.style.fontWeight = "600";
                }
                
                setTimeout(() => {
                    if (calendarPopup) calendarPopup.classList.remove('active');
                }, 200);
            });
        });
    }

    /* =========================================
       5. CLICK OUTSIDE
       ========================================= */
    window.addEventListener('click', (e) => {
        if (guestTrigger && !guestTrigger.contains(e.target)) {
            if (guestPopup) guestPopup.classList.remove('active');
        }
        if (dateTrigger && !dateTrigger.contains(e.target)) {
            if (calendarPopup) calendarPopup.classList.remove('active');
        }
    });

});