document.addEventListener("DOMContentLoaded", function () {
  /* =========================================
       1. KHAI BÁO BIẾN
       ========================================= */
  const searchBtn = document.querySelector(".search-button-purple");
  const heroSection = document.querySelector(".hero-section");
  const whiteSection = document.querySelector(".white-section");
  const detailSection = document.querySelector(".detail-section");

  // Biến Guest
  const guestTrigger = document.getElementById("guest-trigger");
  const guestPopup = document.getElementById("guest-popup");
  const btnMinus = document.getElementById("btn-minus");
  const btnPlus = document.getElementById("btn-plus");
  const guestCountNum = document.getElementById("guest-count-number");
  const guestDisplay = document.getElementById("guest-display");

  // Biến Calendar
  const dateTrigger = document.getElementById("date-trigger");
  const calendarPopup = document.getElementById("calendar-popup");
  const dateDisplay = document.getElementById("date-display");
  const renderArea = document.getElementById("calendar-render-area"); // Khu vực vẽ lịch

  // Chỉ số khách
  let currentGuests = 1;
  const MIN_GUESTS = 1;
  const MAX_GUESTS = 7;

  // Chỉ số ngày tháng
  let startDate = null;
  let endDate = null;
  const today = new Date();

  // Biến kiểm tra khóa cuộn
  let isLocked = false;

  /* =========================================
       2. LOGIC SCROLL & SEARCH BUTTON (KHÓA CUỘN)
       ========================================= */

  // Logic cuộn trang: Khi cuộn > 50px thì thu nhỏ Header
  window.addEventListener("scroll", () => {
    if (isLocked) return; // Nếu đã khóa thì để CSS lo
    if (window.scrollY > 50) {
      heroSection.classList.add("shrink");
    } else {
      heroSection.classList.remove("shrink");
    }
  });

  // Logic Nút Tìm Kiếm
  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      // Mở khóa cuộn và lướt xuống
      document.body.style.overflowY = "auto";
      if (whiteSection) {
        whiteSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      // Đóng các popup
      if (guestPopup) guestPopup.classList.remove("active");
      if (calendarPopup) calendarPopup.classList.remove("active");

      // SAU KHI LƯỚT XONG -> KHÓA LẠI
      setTimeout(() => {
        isLocked = true;
        document.body.classList.add("mode-locked");
        heroSection.classList.add("shrink");
        window.scrollTo(0, 0);
      }, 800);
    });
  }

  /* =========================================
       3. LOGIC GUEST COUNTER
       ========================================= */
  if (guestTrigger) {
    guestTrigger.addEventListener("click", (e) => {
      if (e.target.closest(".counter-btn")) return;
      guestPopup.classList.toggle("active");
      if (calendarPopup) calendarPopup.classList.remove("active");
      e.stopPropagation();
    });
  }

  if (btnPlus) {
    btnPlus.addEventListener("click", (e) => {
      e.stopPropagation();
      if (currentGuests < MAX_GUESTS) {
        currentGuests++;
        updateGuestUI();
      }
    });
  }

  if (btnMinus) {
    btnMinus.addEventListener("click", (e) => {
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
      guestDisplay.textContent = `${currentGuests} guest${
        currentGuests > 1 ? "s" : ""
      }`;
      guestDisplay.style.color = "#000";
      guestDisplay.style.fontWeight = "600";
    }
  }

  /* =========================================
       4. LOGIC CALENDAR (KIỂU BOOKING.COM)
       ========================================= */

  // Hàm khởi tạo: Chọn sẵn ngày mai và ngày kia
  function initCalendar() {
    startDate = new Date(today);
    startDate.setDate(today.getDate() + 1);
    startDate.setHours(0, 0, 0, 0);

    endDate = new Date(today);
    endDate.setDate(today.getDate() + 2);
    endDate.setHours(0, 0, 0, 0);

    updateDateText();
    // Kiểm tra xem renderArea có tồn tại không trước khi vẽ
    if (renderArea) {
      renderCalendar(today.getMonth(), today.getFullYear());
    }
  }

  // Hàm vẽ lịch
  function renderCalendar(currentMonth, currentYear) {
    renderArea.innerHTML = ""; // Xóa lịch cũ

    // Vẽ 2 tháng
    for (let i = 0; i < 2; i++) {
      let month = currentMonth + i;
      let year = currentYear;
      if (month > 11) {
        month -= 12;
        year++;
      }

      // Tạo khung tháng
      const monthDiv = document.createElement("div");
      monthDiv.className = "month-container";
      monthDiv.style.flex = "1";

      // Tiêu đề
      const monthName = new Date(year, month).toLocaleString("en-US", {
        month: "long",
        year: "numeric",
      });
      const title = document.createElement("div");
      title.className = "month-title";
      title.style.width = "100%";
      title.style.marginBottom = "15px";
      title.style.textAlign = "center";
      title.style.fontWeight = "600";
      title.textContent = monthName;
      monthDiv.appendChild(title);

      // Grid ngày
      const grid = document.createElement("div");
      grid.className = "month-grid";

      // Header Thứ
      const daysShort = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
      daysShort.forEach((d) => {
        const dEl = document.createElement("div");
        dEl.className = "day-name";
        dEl.textContent = d;
        grid.appendChild(dEl);
      });

      // Tính toán ngày
      const firstDay = new Date(year, month, 1).getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();

      // Ô trống đầu tháng
      for (let j = 0; j < firstDay; j++) {
        grid.appendChild(document.createElement("div"));
      }

      // Các ngày
      for (let day = 1; day <= daysInMonth; day++) {
        const dayEl = document.createElement("div");
        dayEl.className = "day-num";
        dayEl.textContent = day;

        const thisDate = new Date(year, month, day);
        thisDate.setHours(0, 0, 0, 0);

        // Tô màu logic
        if (startDate && thisDate.getTime() === startDate.getTime()) {
          dayEl.classList.add("start-date");
        } else if (endDate && thisDate.getTime() === endDate.getTime()) {
          dayEl.classList.add("end-date");
        } else if (
          startDate &&
          endDate &&
          thisDate > startDate &&
          thisDate < endDate
        ) {
          dayEl.classList.add("in-range");
        }

        // Click chọn ngày
        dayEl.addEventListener("click", (e) => handleDayClick(thisDate, e));

        grid.appendChild(dayEl);
      }
      monthDiv.appendChild(grid);
      renderArea.appendChild(monthDiv);
    }
  }

  // Xử lý khi click vào ngày
  function handleDayClick(clickedDate, e) {
    e.stopPropagation();

    if (!startDate || (startDate && endDate)) {
      // Trường hợp 1: Chưa chọn gì HOẶC Đã chọn đủ cặp -> Reset chọn lại Start
      startDate = clickedDate;
      endDate = null;
    } else if (startDate && !endDate) {
      // Trường hợp 2: Đã có Start, đang chọn End
      if (clickedDate < startDate) {
        // Nếu chọn ngày nhỏ hơn Start -> Start mới
        startDate = clickedDate;
      } else {
        // Nếu chọn ngày lớn hơn Start -> Đó là End
        endDate = clickedDate;
        setTimeout(() => {
          calendarPopup.classList.remove("active");
        }, 300);
      }
    }
    updateDateText();
    renderCalendar(today.getMonth(), today.getFullYear());
  }

  // Cập nhật text hiển thị
  function updateDateText() {
    if (!dateDisplay) return;
    if (startDate && endDate) {
      const options = { month: "short", day: "numeric" };
      dateDisplay.textContent = `${startDate.toLocaleDateString(
        "en-US",
        options
      )} - ${endDate.toLocaleDateString("en-US", options)}`;
      dateDisplay.style.color = "#000";
      dateDisplay.style.fontWeight = "600";
    } else if (startDate) {
      const options = { month: "short", day: "numeric" };
      dateDisplay.textContent = `${startDate.toLocaleDateString(
        "en-US",
        options
      )} - Checkout?`;
    } else {
      dateDisplay.textContent = "Choose a Date";
    }
  }

  // Bật tắt Calendar Popup
  if (dateTrigger) {
    dateTrigger.addEventListener("click", (e) => {
      calendarPopup.classList.toggle("active");
      if (guestPopup) guestPopup.classList.remove("active");
      e.stopPropagation();
    });
  }

  // Chạy khởi tạo
  initCalendar();

  /* =========================================
       5. CLICK OUTSIDE (ĐÓNG POPUP)
       ========================================= */
  window.addEventListener("click", (e) => {
    if (guestTrigger && !guestTrigger.contains(e.target)) {
      if (guestPopup) guestPopup.classList.remove("active");
    }
    if (dateTrigger && !dateTrigger.contains(e.target)) {
      if (calendarPopup) calendarPopup.classList.remove("active");
    }
  });
  /* ================================
       6. CLICK CARD HIỂN THỊ DETAIL
       ================================ */
  const cards = document.querySelectorAll(".card-item");
  cards.forEach((card) => {
    card.addEventListener("click", () => {
      detailSection.style.display = "flex"; // bật hiển thị
      detailSection.scrollIntoView({ behavior: "smooth" });
    });
  });
});
