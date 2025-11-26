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
  const renderArea = document.getElementById("calendar-render-area");

  // Biến Location Dropdown
  const locationTrigger = document.getElementById("location-trigger");
  const locationDropdown = document.getElementById("location-dropdown");
  const locationDisplay = document.getElementById("location-display");
  const locationSearch = document.getElementById("location-search");
  const locationList = document.getElementById("location-list");
  const dropdownItems = locationList
    ? locationList.querySelectorAll(".dropdown-item")
    : [];

  // Chỉ số khách
  let currentGuests = 1;
  const MIN_GUESTS = 1;
  const MAX_GUESTS = 7;

  // Chỉ số ngày tháng
  let startDate = null;
  let endDate = null;
  const today = new Date();

  // Location đã chọn
  let selectedLocation = "Quận 1";

  // Biến kiểm tra khóa cuộn
  let isLocked = false;

  // 🔥 Biến lưu trữ dữ liệu khách sạn đã tìm kiếm
  let hotelDataCache = [];

  /* =========================================
       2. LOGIC SCROLL
       ========================================= */

  window.addEventListener("scroll", () => {
    if (isLocked) return;
    if (window.scrollY > 50) {
      heroSection.classList.add("shrink");
    } else {
      heroSection.classList.remove("shrink");
    }
  });

  /* =========================================
       3. LOGIC NÚT SEARCH
       ========================================= */

  if (searchBtn) {
    searchBtn.addEventListener("click", async (e) => {
      e.preventDefault && e.preventDefault();

      const resultsContainer = createResultsContainer();
      resultsContainer.innerHTML =
        '<div class="loading">Đang tìm kiếm...</div>';

      document.body.style.overflowY = "auto";
      if (whiteSection)
        whiteSection.scrollIntoView({ behavior: "smooth", block: "start" });

      if (guestPopup) guestPopup.classList.remove("active");
      if (calendarPopup) calendarPopup.classList.remove("active");
      if (locationDropdown) locationDropdown.classList.remove("active");

      const params = getSearchParams();
      if (!params.check_in || !params.check_out) {
        resultsContainer.innerHTML =
          '<p class="error">Vui lòng chọn ngày đến và đi.</p>';
        return;
      }

      try {
        const data = await callRecommendAPI(params);
        displayResults(data.results || []);
      } catch (err) {
        resultsContainer.innerHTML = `<p class="error">Có lỗi khi tìm kiếm: ${escapeHtml(
          err.message || "Unknown"
        )}</p>`;
      }
    });
  }

  /* =========================================
       4. LOGIC LOCATION DROPDOWN
       ========================================= */

  if (locationTrigger) {
    locationTrigger.addEventListener("click", (e) => {
      if (e.target.closest(".dropdown-item")) return;
      locationDropdown.classList.toggle("active");

      if (guestPopup) guestPopup.classList.remove("active");
      if (calendarPopup) calendarPopup.classList.remove("active");

      if (locationDropdown.classList.contains("active")) {
        setTimeout(() => locationSearch.focus(), 100);
      }

      e.stopPropagation();
    });
  }

  dropdownItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.stopPropagation();

      selectedLocation = item.dataset.value;
      locationDisplay.textContent = selectedLocation;
      locationDisplay.style.color = "#000";
      locationDisplay.style.fontWeight = "600";

      dropdownItems.forEach((i) => i.classList.remove("selected"));
      item.classList.add("selected");

      setTimeout(() => {
        locationDropdown.classList.remove("active");
        locationSearch.value = "";
        filterLocationItems("");
      }, 200);
    });
  });

  if (locationSearch) {
    locationSearch.addEventListener("input", (e) => {
      const searchTerm = e.target.value.toLowerCase();
      filterLocationItems(searchTerm);
    });
  }

  function filterLocationItems(searchTerm) {
    dropdownItems.forEach((item) => {
      const text = item.textContent.toLowerCase();
      if (text.includes(searchTerm)) {
        item.style.display = "block";
      } else {
        item.style.display = "none";
      }
    });
  }

  /* =========================================
       5. LOGIC GUEST COUNTER
       ========================================= */

  if (guestTrigger) {
    guestTrigger.addEventListener("click", (e) => {
      if (e.target.closest(".counter-btn")) return;
      guestPopup.classList.toggle("active");
      if (calendarPopup) calendarPopup.classList.remove("active");
      if (locationDropdown) locationDropdown.classList.remove("active");
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
       6. LOGIC CALENDAR
       ========================================= */

  function initCalendar() {
    startDate = new Date(today);
    startDate.setDate(today.getDate() + 1);
    startDate.setHours(0, 0, 0, 0);

    endDate = new Date(today);
    endDate.setDate(today.getDate() + 2);
    endDate.setHours(0, 0, 0, 0);

    updateDateText();
    if (renderArea) {
      renderCalendar(today.getMonth(), today.getFullYear());
    }
  }

  function renderCalendar(currentMonth, currentYear) {
    renderArea.innerHTML = "";

    for (let i = 0; i < 2; i++) {
      let month = currentMonth + i;
      let year = currentYear;
      if (month > 11) {
        month -= 12;
        year++;
      }

      const monthDiv = document.createElement("div");
      monthDiv.className = "month-container";
      monthDiv.style.flex = "1";

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

      const grid = document.createElement("div");
      grid.className = "month-grid";

      const daysShort = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
      daysShort.forEach((d) => {
        const dEl = document.createElement("div");
        dEl.className = "day-name";
        dEl.textContent = d;
        grid.appendChild(dEl);
      });

      const firstDay = new Date(year, month, 1).getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();

      for (let j = 0; j < firstDay; j++) {
        grid.appendChild(document.createElement("div"));
      }

      for (let day = 1; day <= daysInMonth; day++) {
        const dayEl = document.createElement("div");
        dayEl.className = "day-num";
        dayEl.textContent = day;

        const thisDate = new Date(year, month, day);
        thisDate.setHours(0, 0, 0, 0);

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

        dayEl.addEventListener("click", (e) => handleDayClick(thisDate, e));

        grid.appendChild(dayEl);
      }
      monthDiv.appendChild(grid);
      renderArea.appendChild(monthDiv);
    }
  }

  function handleDayClick(clickedDate, e) {
    e.stopPropagation();

    if (!startDate || (startDate && endDate)) {
      startDate = clickedDate;
      endDate = null;
    } else if (startDate && !endDate) {
      if (clickedDate < startDate) {
        startDate = clickedDate;
      } else {
        endDate = clickedDate;
        setTimeout(() => {
          calendarPopup.classList.remove("active");
        }, 300);
      }
    }
    updateDateText();
    renderCalendar(today.getMonth(), today.getFullYear());
  }

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

  if (dateTrigger) {
    dateTrigger.addEventListener("click", (e) => {
      calendarPopup.classList.toggle("active");
      if (guestPopup) guestPopup.classList.remove("active");
      if (locationDropdown) locationDropdown.classList.remove("active");
      e.stopPropagation();
    });
  }

  initCalendar();

  /* =========================================
       7. API & DISPLAY FUNCTIONS
       ========================================= */

  function createResultsContainer() {
    let container = document.querySelector(".results-container");
    if (container) return container;
    container = document.createElement("div");
    container.className = "results-container";
    container.style.maxWidth = "1200px";
    container.style.margin = "40px auto";
    container.style.padding = "20px";
    const white = document.querySelector(".white-section");
    const cards = white ? white.querySelector(".cards-grid") : null;
    if (white) {
      if (cards) white.insertBefore(container, cards);
      else white.appendChild(container);
    } else {
      document.body.appendChild(container);
    }
    return container;
  }

  function formatPrice(price) {
    if (price == null || Number.isNaN(Number(price))) return "-";
    return new Intl.NumberFormat("vi-VN").format(Number(price));
  }

  function escapeHtml(str = "") {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function buildHotelCard(h) {
    const image =
      (h.image || h.photo || "").trim() ||
      "https://via.placeholder.com/400x300?text=No+Image";
    const amenitiesHtml = (h.amenities || [])
      .slice(0, 6)
      .map((a) => `<span class="amenity-tag">${escapeHtml(a)}</span>`)
      .join("");
    const scoreHtml =
      h.score !== undefined && h.score !== null
        ? `<p class="score">Điểm phù hợp: ${(Number(h.score) * 100).toFixed(
            1
          )}%</p>`
        : "";
    return `
            <div class="hotel-card" data-id="${escapeHtml(String(h.id || ""))}">
                <div class="hotel-image"><img src="${escapeHtml(
                  image
                )}" alt="${escapeHtml(h.name || "")}" onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300?text=No+Image'"/></div>
                <div class="hotel-info">
                    <h3>${escapeHtml(h.name || "Unknown")}</h3>
                    <p class="district">📍 ${escapeHtml(h.district || "-")}</p>
                    <p class="price">💰 ${formatPrice(h.price)} VND/đêm</p>
                    <p class="rating">⭐ ${h.rating ?? "-"}/10</p>
                    <div class="amenities">${amenitiesHtml}</div>
                    ${scoreHtml}
                </div>
            </div>
        `;
  }

  function displayResults(hotels) {
    const container = createResultsContainer();
    if (!hotels || hotels.length === 0) {
      container.innerHTML =
        '<p class="no-results">Không tìm thấy khách sạn phù hợp. Vui lòng thử lại.</p>';
      const cardsGrid = document.querySelector(".cards-grid");
      if (cardsGrid) cardsGrid.style.display = "";
      return;
    }
    hotelDataCache = hotels;
    const html = hotels.map((h) => buildHotelCard(h)).join("");
    container.innerHTML = html;
    const cardsGrid = document.querySelector(".cards-grid");
    if (cardsGrid) cardsGrid.style.display = "none";
    const white = document.querySelector(".white-section");
    if (white) white.scrollIntoView({ behavior: "smooth", block: "start" });

    attachHotelCardListeners();
  }

  function attachHotelCardListeners() {
    const hotelCards = document.querySelectorAll(".hotel-card");
    hotelCards.forEach((card) => {
      card.addEventListener("click", (e) => {
        const hotelId = card.dataset.id;

        // Tìm dữ liệu khách sạn trong cache
        const clickedHotel = hotelDataCache.find(
          (h) => String(h.id || "") === hotelId
        );

        if (clickedHotel) {
          // 🔥 Điền thông tin vào Detail Section
          populateDetailSection(clickedHotel);
        }

        // Hiển thị Detail Section và cuộn tới đó
        if (detailSection) {
          detailSection.style.display = "flex";
          detailSection.scrollIntoView({ behavior: "smooth" });
        }

        // Đóng các popup khác
        if (guestPopup) guestPopup.classList.remove("active");
        if (calendarPopup) calendarPopup.classList.remove("active");
        if (locationDropdown) locationDropdown.classList.remove("active");
      });
    });
  }

  async function callRecommendAPI(searchParams) {
    try {
      const res = await fetch("http://localhost:8000/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(searchParams),
      });

      if (res.status === 204)
        return { results: [], meta: { message: "No hotels found" } };

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const msg = err?.detail || err?.message || `status ${res.status}`;
        throw new Error(msg);
      }
      return await res.json();
    } catch (e) {
      console.error("API error", e);
      throw e;
    }
  }

  function getSearchParams() {
    const location = selectedLocation || "Quận 1";
    const budgetMin = document.querySelector("#budget-min")?.value;
    const budgetMax = document.querySelector("#budget-max")?.value;

    let payload = {
      district: location,
      check_in: startDate ? startDate.toISOString().slice(0, 10) : null,
      check_out: endDate ? endDate.toISOString().slice(0, 10) : null,
      topN: 5,
    };

    if (budgetMin && budgetMax) {
      payload.budget_min = Number(budgetMin);
      payload.budget_max = Number(budgetMax);
    } else {
      payload.budget_min = 500000;
      payload.budget_max = 2000000;
    }

    const purposeSelect = document.querySelector("#purpose-select");
    payload.purpose = purposeSelect?.value || "leisure";
    payload.guests = currentGuests;

    return payload;
  }

  function populateDetailSection(hotel) {
    if (!detailSection) return;

    // 1. Tên khách sạn
    const nameEl = detailSection.querySelector(".name .heading200");
    if (nameEl) nameEl.textContent = hotel.name || "Tên chỗ ở không rõ";

    // 2. Hình ảnh
    const imageEl = detailSection.querySelector(".image-frame img");
    const imageSrc =
      (hotel.image || hotel.photo || "").trim() ||
      "../../assets/picture/group.jpg";
    if (imageEl) imageEl.src = imageSrc;

    // 3. Thông tin/Mô tả (Giả sử bạn có trường description/info trong dữ liệu)
    const infoEl = detailSection.querySelector(
      ".details-container .paragraph100regular"
    );
    // Vì dữ liệu mẫu không có mô tả chi tiết, ta dùng thông tin district và rating để làm ví dụ
    if (infoEl) {
      infoEl.innerHTML = `
            Địa điểm: ${hotel.district || "Không rõ"}<br>
            Giá: ${formatPrice(hotel.price)} VND/đêm<br>
            Mục đích: ${
              document.querySelector("#purpose-select")?.value || "Leisure"
            }<br>
            <br>
            Các tiện ích nổi bật: ${
              hotel.amenities?.slice(0, 5).join(", ") || "Không có thông tin"
            }
        `;
    }

    // 4. Rating (Giả định rating là điểm số từ 1-10)
    const ratingStarContainer = detailSection.querySelector(
      ".rating .rating-star"
    );
    if (ratingStarContainer) {
      const rating = Math.min(5, Math.ceil((hotel.rating || 0) / 2)); // Chuyển rating 1-10 thành 1-5 sao
      ratingStarContainer.innerHTML = Array(5)
        .fill(0)
        .map(
          (_, i) =>
            `<img src="../../assets/section/star-${
              i < rating ? "fill" : "line"
            }.svg" alt="Star"/>`
        )
        .join("");
    }

    // 5. Google Map (Bạn sẽ cần phải tích hợp Google Maps API để hiển thị map thật)
    const mapEl = detailSection.querySelector(".google-map");
    if (mapEl) {
      // Tạm thời hiển thị một iframe Google Map đơn giản với tên khách sạn/quận
      const mapHtml = `<iframe loading="lazy" allowfullscreen src="https://maps.google.com/maps?q=${encodeURIComponent(
        (hotel.name || "") + ", " + (hotel.district || "Thành phố Hồ Chí Minh")
      )}&t=&z=14&ie=UTF8&iwloc=&output=embed"></iframe>`;
      mapEl.innerHTML = mapHtml;
    }
  }

  /* =========================================
       8. CLICK OUTSIDE
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
    card.addEventListener("click", (e) => {
      // Lắng nghe click cho các thẻ gợi ý (Maybe you should try these)
      if (detailSection) {
        detailSection.style.display = "flex";
        detailSection.scrollIntoView({ behavior: "smooth" });
      }
      if (locationTrigger && !locationTrigger.contains(e.target)) {
        if (locationDropdown) locationDropdown.classList.remove("active");
      }
    });
  });
});
