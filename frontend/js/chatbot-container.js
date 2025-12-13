/**
 * ChatbotContainer - Enhanced Version
 * Features:
 * - Auto-scroll to bottom on new messages
 * - Chat history persistence with localStorage
 * - Session management
 */
class ChatbotContainer {
    constructor() {
        // State management
        this.state = {
            isVisible: false,
            isOpen: false,
            isFullscreen: false,
            currentView: 'result',
            topHotels: [],
            selectedHotel: null,
            conversationHistory: [],
        };
        
        // API endpoint
        this.API_URL = "http://127.0.0.1:8000/api/chat";
        
        // localStorage keys
        this.STORAGE_KEYS = {
            HISTORY: 'chatbotHistory_2rism',
            SESSION: 'chatbotSession_2rism',
            TOP_HOTELS: 'chatbotTopHotels_2rism',
            TIMESTAMP: 'chatbotTimestamp_2rism'
        };
        
        // Session timeout (24 hours)
        this.SESSION_TIMEOUT = 24 * 60 * 60 * 1000;
        
        // DOM references
        this.container = null;
        this.icon = null;
        this.resultView = null;
        this.reviewView = null;
        
        this.init();
    }
    
    /**
     * Initialize chatbot
     */
    init() {
        this.loadMarkedLibrary();
        this.createContainer();
        this.attachEventListeners();
        this.loadHistoryFromStorage();
        console.log('✅ ChatbotContainer initialized with session:', this.state.sessionId);
    }
    /**
     * ✅ THÊM: Load Marked.js library
     */
    loadMarkedLibrary() {
        if (typeof marked === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            script.async = false;
            document.head.appendChild(script);
            
            script.onload = () => {
                console.log('✅ Marked.js loaded');
                // ✅ Configure marked options
                if (typeof marked !== 'undefined' && marked.setOptions) {
                    marked.setOptions({
                        breaks: true,        // Convert \n to <br>
                        gfm: true,          // GitHub Flavored Markdown
                        headerIds: false,   // Don't add IDs to headers
                        mangle: false       // Don't escape autolinked email
                    });
                }
            };
        }
    }
    
    /**
     * ✅ THÊM: Parse Markdown to HTML
     */
    parseMarkdown(text) {
        if (typeof marked !== 'undefined' && marked.parse) {
            try {
                return marked.parse(text);
            } catch (e) {
                console.error('Markdown parse error:', e);
                return this.escapeHtml(text).replace(/\n/g, '<br>');
            }
        }
        // Fallback nếu marked chưa load
        return this.escapeHtml(text).replace(/\n/g, '<br>');
    }
    /**
     * ========================================
     * TASK 2: CHAT HISTORY PERSISTENCE
     * ========================================
     */
    
    /**
     * Load chat history from localStorage
     */
    loadHistoryFromStorage() {
        try {
            const timestamp = localStorage.getItem(this.STORAGE_KEYS.TIMESTAMP);
            
            // Check if session is expired
            if (timestamp) {
                const elapsed = Date.now() - parseInt(timestamp);
                if (elapsed > this.SESSION_TIMEOUT) {
                    console.log('⏰ Session expired, clearing history');
                    this.clearHistory();
                    return;
                }
            }
            
            // Load conversation history
            const historyData = localStorage.getItem(this.STORAGE_KEYS.HISTORY);
            if (historyData) {
                this.state.conversationHistory = JSON.parse(historyData);
                console.log('✅ Loaded', this.state.conversationHistory.length, 'messages from history');
            }
            
            // Load top hotels
            const hotelsData = localStorage.getItem(this.STORAGE_KEYS.TOP_HOTELS);
            if (hotelsData) {
                this.state.topHotels = JSON.parse(hotelsData);
                console.log('✅ Loaded', this.state.topHotels.length, 'hotels from storage');
            }
            
            // Load session ID
            const sessionId = localStorage.getItem(this.STORAGE_KEYS.SESSION);
            if (sessionId) {
                this.state.sessionId = sessionId;
            }
            
        } catch (error) {
            console.error('❌ Error loading history:', error);
            this.clearHistory();
        }
    }
    
    /**
     * Save chat history to localStorage
     */
    saveHistoryToStorage() {
        try {
            // Save conversation history
            localStorage.setItem(
                this.STORAGE_KEYS.HISTORY, 
                JSON.stringify(this.state.conversationHistory)
            );
            
            // Save top hotels
            localStorage.setItem(
                this.STORAGE_KEYS.TOP_HOTELS,
                JSON.stringify(this.state.topHotels)
            );
            
            // Save session ID
            localStorage.setItem(
                this.STORAGE_KEYS.SESSION,
                this.state.sessionId
            );
            
            // Save timestamp
            localStorage.setItem(
                this.STORAGE_KEYS.TIMESTAMP,
                Date.now().toString()
            );
            
            console.log('💾 History saved to localStorage');
            
        } catch (error) {
            console.error('❌ Error saving history:', error);
        }
    }
    
    /**
     * Add message to history and save
     */
    addToHistory(userMessage, botResponse) {
        this.state.conversationHistory.push({
            user: userMessage,
            bot: botResponse,
            timestamp: Date.now()
        });
        
        // Save to localStorage
        this.saveHistoryToStorage();
    }
    
    /**
     * Clear chat history
     */
    clearHistory() {
        this.state.conversationHistory = [];
        this.state.topHotels = [];
        this.state.sessionId = this.generateSessionId();
        
        // Clear localStorage
        Object.values(this.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        
        console.log('🗑️ Chat history cleared');
    }
    
    /**
     * Restore chat messages to UI
     */
    restoreMessagesToUI() {
        if (this.state.conversationHistory.length === 0) return;
        
        const currentView = this.state.currentView === 'result' ? this.resultView : this.reviewView;
        
        // Clear current messages (except welcome/hotel cards)
        const existingMessages = currentView.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        // Render history messages
        this.state.conversationHistory.forEach(msg => {
            this.addUserMessageToDOM(msg.user, false); // false = don't save again
            this.addBotMessageToDOM(msg.bot, false);
        });
        
        console.log('✅ Restored', this.state.conversationHistory.length, 'messages to UI');
    }
    
    /**
     * ========================================
     * DOM CREATION
     * ========================================
     */
    
    createContainer() {
        const containerHTML = `
            <!-- Chatbot Container -->
            <div class="chatbot-container" id="chatbotContainer" style="display: none;">
                
                <!-- Floating Icon -->
                <div class="chatbot-icon" id="chatbotIcon">
                    <button class="chatbot-icon-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="white">
                            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                        </svg>
                        <span class="chatbot-badge" id="chatbotBadge">3</span>
                    </button>
                </div>
                
                <!-- Chat Window -->
                <div class="chatbot-window" id="chatbotWindow" style="display: none;">
                    
                    <!-- Header -->
                    <div class="chatbot-window-header">
                        <div class="header-left">
                            <button class="btn-back" id="btnBack" style="display: none;">
                                <i class="fas fa-arrow-left"></i>
                            </button>
                            <img src="assets/icons/logo.svg" alt="2rism" class="chatbot-logo">
                            <span class="chatbot-title">Touriri</span>
                        </div>
                        <div class="header-right">
                            <button class="btn-fullscreen" id="btnFullscreen" title="Toàn màn hình">
                                <i class="fas fa-expand"></i>
                            </button>
                            <button class="btn-clear-history" id="btnClearHistory" title="Xóa lịch sử chat">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                    </div>
                    
                    <!-- Views Container (with auto-scroll) -->
                    <div class="chatbot-views" id="chatbotViews">
                        
                        <!-- RESULT VIEW -->
                        <div class="chatbot-view chatbot-result-view" id="resultView">
                            <div class="ai-message-box">
                                <p id="aiWelcomeMessage">👋 Xin chào! Tôi đã tìm thấy <strong>Top 3 khách sạn</strong> phù hợp nhất cho bạn:</p>
                            </div>
                            
                            <div class="hotels-list" id="hotelsList">
                                <!-- Hotels will be rendered here -->
                            </div>
                            
                            <div class="ai-question-box">
                                <p>Bạn có muốn xem chi tiết review của khách sạn nào không? Hoặc hỏi tôi bất kỳ điều gì!</p>
                            </div>
                            
                            <!-- Messages container for result view -->
                            <div class="messages-container" id="resultMessages"></div>
                        </div>
                        
                        <!-- REVIEW VIEW -->
                        <div class="chatbot-view chatbot-review-view" id="reviewView" style="display: none;">
                            <div class="review-header">
                                <h2 id="reviewHotelName">Hotel Name</h2>
                                <div class="review-rating" id="reviewRating">⭐ 4.5/5</div>
                            </div>
                            
                            <div class="review-content" id="reviewContent">
                                <!-- AI review summary -->
                            </div>
                            
                            <div class="ai-question-box">
                                <p>Bạn muốn hỏi gì thêm về khách sạn này?</p>
                            </div>
                            
                            <!-- Messages container for review view -->
                            <div class="messages-container" id="reviewMessages"></div>
                        </div>
                        
                    </div>
                    
                    <!-- Input Area -->
                    <div class="chatbot-input-area">
                        <input 
                            type="text" 
                            id="chatbotInput" 
                            class="chatbot-input" 
                            placeholder="Hỏi tôi về khách sạn..."
                            autocomplete="off"
                        >
                        <button class="btn-send" id="btnSend">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                    
                </div>
                
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', containerHTML);
        
        // Get DOM references
        this.container = document.getElementById('chatbotContainer');
        this.icon = document.getElementById('chatbotIcon');
        this.window = document.getElementById('chatbotWindow');
        this.resultView = document.getElementById('resultView');
        this.reviewView = document.getElementById('reviewView');
        this.chatbotViews = document.getElementById('chatbotViews');
        this.badge = document.getElementById('chatbotBadge');
        this.input = document.getElementById('chatbotInput');
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Icon click
        this.icon.addEventListener('click', () => this.toggleChatWindow());
        
        // Back button
        document.getElementById('btnBack').addEventListener('click', () => this.showResultView());
        
        // Clear history button
        document.getElementById('btnClearHistory').addEventListener('click', () => this.handleClearHistory());
        
        // Fullscreen button
        document.getElementById('btnFullscreen').addEventListener('click', () => this.toggleFullscreen());

        // Send message
        document.getElementById('btnSend').addEventListener('click', () => this.sendMessage());
        
        // Enter key
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    }
    
    /**
     * Handle clear history button click
     */
    handleClearHistory() {
    if (confirm('Bạn có chắc muốn xóa toàn bộ lịch sử chat?')) {
        this.clearHistory();
        
        // ✅ Clear ALL message containers
        const chatMessages = document.getElementById('chatMessages');
        const resultMessages = document.getElementById('resultMessages');
        const reviewMessages = document.getElementById('reviewMessages');
        
        if (chatMessages) chatMessages.innerHTML = '';
        if (resultMessages) resultMessages.innerHTML = '';
        if (reviewMessages) reviewMessages.innerHTML = '';
        
        alert('✅ Đã xóa lịch sử chat!');
    }
    }
    
    /**
    * Update hotels (called when user searches again)
    */
    updateHotels(hotels) {
        if (!hotels || hotels.length === 0) return;
        
        this.state.topHotels = hotels.slice(0, 3);
        this.saveHistoryToStorage();
        
        // Re-render hotels list
        this.renderHotelsList();
        
        // Update modal if exists
        if (document.getElementById('touririModal')) {
            this.loadHotelsToModal();
        }
        
        // Update badge
        this.badge.textContent = this.state.topHotels.length;
        
        console.log('✅ Updated to', this.state.topHotels.length, 'new hotels');
    }

    /**
     * Show chatbot after search
     */
    showChatbot(hotels) {
        if (!hotels || hotels.length === 0) return;
        
        // Update state
        this.state.isVisible = true;
        this.state.topHotels = hotels.slice(0, 3);
        
        // Save top hotels to storage
        this.saveHistoryToStorage();

        if (this.state.isOpen) {
            this.renderHotelsList();
            // Cập nhật modal nếu đã tạo
            if (document.getElementById('touririModal')) {
                this.loadHotelsToModal();
            }
        }
        
        // Show container
        this.container.style.display = 'block';
        this.badge.textContent = this.state.topHotels.length;
        
        setTimeout(() => {
            this.icon.style.animation = 'slideInUp 0.5s ease';
        }, 100);
        
        console.log('✅ Chatbot shown with', this.state.topHotels.length, 'hotels');
    }
    
    /**
     * Open chat window
     */
    openChatWindow() {
        this.state.isOpen = true;
        this.window.style.display = 'flex';
        
        // Show result view
        this.showResultView();
        
        // Hide badge
        this.badge.style.display = 'none';
        
        // Render hotels if needed
        if (document.getElementById('hotelsList').children.length === 0) {
            this.renderHotelsList();
        }
        
        // Restore chat history
        this.restoreMessagesToUI();
        
        // Auto-scroll to bottom
        this.scrollToBottom();
        
        // Focus input
        setTimeout(() => this.input.focus(), 300);
    }

    toggleChatWindow() {
        if (this.state.isOpen) {
            this.closeChatWindow();
        } else {
            this.openChatWindow();
        }
    }

    toggleFullscreen() {
        this.state.isFullscreen = !this.state.isFullscreen;
        const btnIcon = document.querySelector('#btnFullscreen i');
        
        if (this.state.isFullscreen) {
            this.window.classList.add('fullscreen');
            btnIcon.className = 'fas fa-compress';  // Change to compress icon
        } else {
            this.window.classList.remove('fullscreen');
            btnIcon.className = 'fas fa-expand';    // Back to expand icon
        }
    }

    /**
     * Close chat window
     */
    closeChatWindow() {
        this.state.isOpen = false;
        this.window.style.display = 'none';
        this.badge.style.display = 'flex';
    }
    
    /**
     * Render hotels list
     */
    renderHotelsList() {
        const hotelsList = document.getElementById('hotelsList');
        hotelsList.innerHTML = '';
        
        this.state.topHotels.forEach((hotel, index) => {
            const hotelCard = this.createHotelCard(hotel, index);
            hotelsList.appendChild(hotelCard);
        });
    }
    
    /**
     * Create hotel card
     */
    createHotelCard(hotel, index) {
        const card = document.createElement('div');
        card.className = 'hotel-card-compact';
        card.dataset.index = index;
        
        const stars = '⭐'.repeat(Math.floor((hotel.rating || 4) / 2));
        const price = hotel.price ? new Intl.NumberFormat('vi-VN').format(hotel.price) : 'Liên hệ';
        
        card.innerHTML = `
            <div class="hotel-card-header">
                <h3 class="hotel-name">${hotel.name || hotel.hotel_name}</h3>
                <div class="hotel-rating">
                    <span class="stars">${stars}</span>
                    <span class="rating-value">${(hotel.rating || 4).toFixed(1)}/10</span>
                </div>
            </div>
            
            <div class="hotel-info">
                <p class="hotel-price">💰 ${price} VND/đêm</p>
                <p class="hotel-location">📍 ${hotel.district || hotel.location || 'TP.HCM'}</p>
            </div>
            
            <div class="hotel-actions">
                <button class="btn-review" data-index="${index}">
                    📝 Xem Reviews
                </button>
            </div>
        `;
        
        card.querySelector('.btn-review').addEventListener('click', () => {
            this.showReviewView(hotel);
        });
        
        return card;
    }
    
    /**
     * Show review view
     */
    async showReviewView(hotel) {
        this.state.currentView = 'review';
        this.state.selectedHotel = hotel;
        
        this.resultView.style.display = 'none';
        this.reviewView.style.display = 'block';
        
        document.getElementById('btnBack').style.display = 'block';
        
        document.getElementById('reviewHotelName').textContent = hotel.name || hotel.hotel_name;
        const stars = '⭐'.repeat(Math.floor((hotel.rating || 4) / 2));
        document.getElementById('reviewRating').textContent = `${stars} ${(hotel.rating || 4).toFixed(1)}/10`;
        
        await this.loadReviewSummary(hotel);
        
        // Auto-scroll after view change
        this.scrollToBottom();
    }
    
    /**
     * Show result view
     */
    showResultView() {
        this.state.currentView = 'result';
        this.state.selectedHotel = null;
        
        this.resultView.style.display = 'block';
        this.reviewView.style.display = 'none';
        
        document.getElementById('btnBack').style.display = 'none';
        
        // Auto-scroll
        this.scrollToBottom();
    }
    
    /**
     * Load review summary
     */
    async loadReviewSummary(hotel) {
        const reviewContent = document.getElementById('reviewContent');
        
        reviewContent.innerHTML = `
            <div class="loading-review">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <p>Đang phân tích reviews...</p>
            </div>
        `;
        
        try {
            const question = `Hãy tóm tắt những review và đánh giá về khách sạn "${hotel.name || hotel.hotel_name}". Phân tích điểm mạnh, điểm yếu và đưa ra nhận xét tổng quan.`;
            
            const response = await fetch(this.API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: question,
                    hotel_context: {
                        id: hotel.id || hotel.hotel_id,
                        name: hotel.name || hotel.hotel_name,
                        rating: hotel.rating,
                        price: hotel.price
                    }
                })
            });
            
            if (!response.ok) throw new Error('API Error');
            
            const data = await response.json();

            // Parse Markdown to HTML
            const htmlContent = this.parseMarkdown(data.answer || data.response);
            
            reviewContent.innerHTML = `
                <div class="review-summary markdown-content">
                    ${htmlContent}
                </div>
            `;
            
            // Auto-scroll after content loaded
            this.scrollToBottom();
            
        } catch (error) {
            console.error('Review Error:', error);
            reviewContent.innerHTML = `
                <div class="error-message">
                    <p>❌ Xin lỗi, không thể tải review lúc này.</p>
                </div>
            `;
        }
    }
    
    /**
     * Format review text
     */
    formatReviewText(text) {
        return text.replace(/\n/g, '<br>');
    }
    
    /**
     * ========================================
     * TASK 1: AUTO-SCROLLING
     * ========================================
     */
    
    /**
     * Auto-scroll to bottom of chat views
     */
    scrollToBottom() {
        setTimeout(() => {
            if (this.chatbotViews) {
                // Scroll the main views container
                this.chatbotViews.scrollTop = this.chatbotViews.scrollHeight;
                
                // Also scroll current view container
                const currentView = this.state.currentView === 'result' ? this.resultView : this.reviewView;
                if (currentView) {
                    currentView.scrollTop = currentView.scrollHeight;
                }
            }
        }, 100);
    }
    
    /**
     * ========================================
     * MESSAGE HANDLING
     * ========================================
     */
    
    /**
     * Send message to AI
     */
        async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;
        
        this.addUserMessageToDOM(message, true);
        this.input.value = '';
        this.input.disabled = true;
        
        this.addLoadingMessage();
        
        try {
            const context = {
                currentView: this.state.currentView,
                hotels: this.state.topHotels,
                selectedHotel: this.state.selectedHotel,
                conversationHistory: this.state.conversationHistory
            };
            
            const response = await fetch(this.API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: message,
                    context: context
                })
            });
            
            if (!response.ok) throw new Error('API Error');
            
            const data = await response.json();
            
            this.removeLoadingMessage();
            
            const botAnswer = data.answer || data.response || 'Xin lỗi, tôi không hiểu câu hỏi.';
            this.addBotMessageToDOM(botAnswer, true);
            
            this.addToHistory(message, botAnswer);
            
        } catch (error) {
            console.error('Chat Error:', error);
            this.removeLoadingMessage();
            this.addBotMessageToDOM('❌ Xin lỗi, tôi không thể trả lời lúc này.', false);
        } finally {
            this.input.disabled = false;
            this.input.focus();
        }
    }
    
    /**
     * Add user message to DOM
     * @param {string} text - Message text
     * @param {boolean} shouldSave - Save to history or not
     */
    addUserMessageToDOM(text, shouldSave = true) {
        const container = this.getMessagesContainer();
        const messageBox = document.createElement('div');
        messageBox.className = 'message user-message';
        messageBox.innerHTML = `<div class="message-content">${this.escapeHtml(text)}</div>`;
        
        container.appendChild(messageBox);
        this.scrollToBottom();
    }
    
    /**
     * Add bot message to DOM
     * @param {string} html - Message HTML
     * @param {boolean} shouldSave - Save to history or not
     */
    addBotMessageToDOM(text, shouldSave = true) {
        const container = this.getMessagesContainer();
        const messageBox = document.createElement('div');
        messageBox.className = 'message bot-message';
        
        // ✅ QUAN TRỌNG: Parse Markdown to HTML
        const htmlContent = this.parseMarkdown(text);
        
        messageBox.innerHTML = `<div class="message-content markdown-content">${htmlContent}</div>`;
        
        container.appendChild(messageBox);
        this.scrollToBottom();
    }
    
    /**
     * Add loading message
     */
    addLoadingMessage() {
        const container = this.getMessagesContainer();
        const loadingBox = document.createElement('div');
        loadingBox.className = 'message bot-message loading-message';
        loadingBox.innerHTML = `
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        container.appendChild(loadingBox);
        this.scrollToBottom();
    }
    
    removeLoadingMessage() {
        const loadingMsg = document.querySelector('.loading-message');
        if (loadingMsg) loadingMsg.remove();
    }
    
    getMessagesContainer() {
        return this.state.currentView === 'result' 
            ? document.getElementById('resultMessages')
            : document.getElementById('reviewMessages');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize
window.chatbotContainer = new ChatbotContainer();