const SERVER_URL = "http://localhost:5000";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "storeText") {
        fetch(`${SERVER_URL}/store`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: message.text })
        })
        .then(response => response.json())
        .then(data => console.log("Backend response:", data))
        .catch(error => console.error("Error sending data:", error));
    }
});