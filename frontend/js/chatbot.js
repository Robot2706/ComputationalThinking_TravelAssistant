const chatInput = document.getElementById("chat-input");
const chatContainer = document.getElementById("chat-container");

// AUTO SCROLL
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ADD USER BUBBLE
function addUserMessage(text) {
    const bubble = document.createElement("div");
    bubble.className = "user-bubble";
    bubble.textContent = text;

    chatContainer.appendChild(bubble);
    scrollToBottom();
}

// ADD BOT MESSAGE (Markdown supported)
function addBotMessage(mdText) {
    const wall = document.createElement("div");
    wall.className = "bot-message bot-wall";

    // Convert markdown → HTML
    wall.innerHTML = marked.parse(mdText);

    chatContainer.appendChild(wall);
    scrollToBottom();
}

// BOT FAKE REPLY (demo)
async function fakeBotReply(text) {
    await new Promise(r => setTimeout(r, 500));

    addBotMessage(`
**You asked:**  
_${text}_  

Here is a markdown example:  
- Bullet point  
- **Bold text**  
- *Italic text*  
- \`Inline code\`
`);
}

// SEND MESSAGE
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    addUserMessage(text);
    chatInput.value = "";

    fakeBotReply(text); // replace with API call later
}

// ENTER TO SEND
chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") {
        sendMessage();
    }
});
