const SERVER_URL = "http://localhost:5000";

// DOM elements
const chatContainer = document.getElementById("chatContainer");
const userInput = document.getElementById("userInput");
const sendMessageBtn = document.getElementById("sendMessage");
const extractBtn = document.getElementById("extract");
const clearChatBtn = document.getElementById("clearChat");

// Initialize chat interface
document.addEventListener("DOMContentLoaded", () => {
    // Add event listeners for input and buttons
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && userInput.value.trim() !== "") {
            sendMessage();
        }
    });
    
    sendMessageBtn.addEventListener("click", () => {
        if (userInput.value.trim() !== "") {
            sendMessage();
        }
    });
    
    extractBtn.addEventListener("click", extractText);
    clearChatBtn.addEventListener("click", clearChat);
    
    // Check if content is already extracted
    checkContentAvailability();
});

// Check if content is already extracted
function checkContentAvailability() {
    fetch(`${SERVER_URL}/check_content`)
    .then(response => response.json())
    .then(data => {
        if (!data.content_available) {
            addSystemMessage("Please extract the webpage content first to start chatting.");
        }
    })
    .catch(error => {
        console.error("Error checking content availability:", error);
        addSystemMessage("Connection to server failed. Please try again.");
    });
}

// Extract text from page
function extractText() {
    addSystemMessage("Extracting content from this webpage...");
    
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            function: getTextFromPage
        }, (results) => {
            if (results && results[0] && results[0].result) {
                let extractedText = results[0].result;
                sendTextToBackend(extractedText);
            } else {
                addSystemMessage("⚠️ Failed to extract text from this page.");
            }
        });
    });
}

// Get page text
function getTextFromPage() {
    return document.body.innerText.trim();
}

// Send extracted text to backend
function sendTextToBackend(text) {
    fetch(`${SERVER_URL}/store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Text stored:", data);
        addSystemMessage("✅ Content extracted successfully! You can now ask questions about this webpage.");
    })
    .catch(error => {
        console.error("Error sending data:", error);
        addSystemMessage("⚠️ Failed to store text. Please try again.");
    });
}

// Send user message to chat
function sendMessage() {
    const message = userInput.value.trim();
    
    // Add user message to chat
    addUserMessage(message);
    
    // Clear input field
    userInput.value = "";
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send message to backend
    fetch(`${SERVER_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add response to chat
        addSystemMessage(data.response);
    })
    .catch(error => {
        console.error("Error sending message:", error);
        removeTypingIndicator();
        addSystemMessage("⚠️ Error getting response. Please try again.");
    });
}

// Add user message to chat
function addUserMessage(message) {
    const messageElement = document.createElement("div");
    messageElement.className = "user-message";
    messageElement.innerHTML = `<p>${escapeHtml(message)}</p>`;
    chatContainer.appendChild(messageElement);
    scrollToBottom();
}

// Add system message to chat
function addSystemMessage(message) {
    const messageElement = document.createElement("div");
    messageElement.className = "system-message";
    messageElement.innerHTML = `<p>${message}</p>`;
    chatContainer.appendChild(messageElement);
    scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "typing-indicator";
    typingIndicator.id = "typingIndicator";
    typingIndicator.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    chatContainer.appendChild(typingIndicator);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById("typingIndicator");
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Clear chat history
function clearChat() {
    // Clear local chat UI
    chatContainer.innerHTML = '';
    
    // Add welcome message
    addSystemMessage("Chat history cleared. What would you like to know about this webpage?");
    
    // Clear server-side chat history
    fetch(`${SERVER_URL}/clear_chat`, {
        method: "POST"
    })
    .then(response => response.json())
    .then(data => {
        console.log("Chat history cleared:", data);
    })
    .catch(error => {
        console.error("Error clearing chat history:", error);
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Scroll chat to bottom
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}