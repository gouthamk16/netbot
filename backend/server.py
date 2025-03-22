from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from rag import chat_loop, init_ret

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

JSON_FILE = "data.json"
CHAT_HISTORY_FILE = "chat_history.json"
MAX_ENTRIES = 10  # Limit stored texts to 10

def save_text_to_json(text):
    """Save extracted text to a JSON file, keeping only the last 10 entries."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = {"webpages": []}

    data["webpages"].append({"text": text})

    # Keep only the last 10 entries
    if len(data["webpages"]) > MAX_ENTRIES:
        data["webpages"].pop(0)  # Remove the oldest entry

    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    
    # Clear chat history when new content is extracted
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)

@app.route("/store", methods=["POST"])
def store_text():
    """Receive webpage text and save it to JSON."""
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    save_text_to_json(text)
    return jsonify({"message": "Text stored successfully"}), 200

@app.route("/chat", methods=["POST"])
def handle_chat():
    """Process chat messages using RAG."""
    data = request.json
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        retriever = init_ret()
        response = chat_loop(question, retriever)
        return jsonify({"response": response}), 200
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({"error": "Failed to process question", "details": str(e)}), 500

@app.route("/check_content", methods=["GET"])
def check_content():
    """Check if any content has been extracted."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data["webpages"]:
                return jsonify({"content_available": True}), 200
    return jsonify({"content_available": False}), 200

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    """Clear the chat history."""
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    return jsonify({"message": "Chat history cleared successfully"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)