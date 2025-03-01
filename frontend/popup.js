const SERVER_URL = "http://localhost:5000";

// Function to extract text when button is clicked
function extractText() {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            function: getTextFromPage
        }, (results) => {
            if (results && results[0] && results[0].result) {
                let extractedText = results[0].result;
                sendTextToBackend(extractedText);
            } else {
                console.error("Failed to extract text.");
            }
        });
    });
}

// Function to get the page's text manually
function getTextFromPage() {
    return document.body.innerText.trim();
}

// Function to send the extracted text to the Python backend
function sendTextToBackend(text) {
    fetch(`${SERVER_URL}/store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Text stored:", data);
        document.getElementById("response").innerHTML = "✅ Text extracted and stored!";
    })
    .catch(error => {
        console.error("Error sending data:", error);
        document.getElementById("response").innerHTML = "⚠️ Failed to store text.";
    });
}

// Function to get the latest stored text
function getStoredText() {
    let responseBox = document.getElementById("response");
    responseBox.innerHTML = "Fetching extracted content... ⏳";

    fetch(`${SERVER_URL}/get_text`)
    .then(response => response.json())
    .then(data => {
        responseBox.innerHTML = `<strong>Extracted Content:</strong><br>${data.latest_text}`;
    })
    .catch(error => {
        console.error("Error fetching stored content:", error);
        responseBox.innerHTML = "⚠️ Error retrieving content.";
    });
}

// Add event listeners to buttons
document.getElementById("extract").addEventListener("click", extractText);
document.getElementById("ask").addEventListener("click", getStoredText);
