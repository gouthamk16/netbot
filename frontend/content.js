function extractText() {
    let text = document.body.innerText; 
    return text.replace(/\s+/g, ' ').trim();
}

chrome.runtime.sendMessage({ action: "storeText", text: extractText() });
