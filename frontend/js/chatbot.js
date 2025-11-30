import anime from 'https://cdn.jsdelivr.net/npm/animejs@3.2.1/lib/anime.es.js';

const askInput = document.getElementById("askInput");
const aiMessage = document.getElementById("aiMessage");

askInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && askInput.value.trim() !== "") {
        
        const userText = askInput.value.trim();
        console.log("User asked:", userText);

        // Tạm thời cho AI trả lời cứng
        aiMessage.textContent = `Mình đã nhận câu hỏi: "${userText}". Bạn muốn mình hỗ trợ điều gì thêm?`;

        askInput.value = "";
    }
});