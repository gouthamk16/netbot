from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from rag import chat_loop, init_ret

app = Flask(__name__)
CORS(app)

JSON_FILE = "data.json"
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

@app.route("/store", methods=["POST"])
def store_text():
    """Receive webpage text and save it to JSON."""
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    save_text_to_json(text)
    return jsonify({"message": "Text stored successfully"}), 200

@app.route("/get_text", methods=["GET"])
def get_stored_text():
    """Retrieve only the latest stored webpage text."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data["webpages"]:
                retriever = init_ret()
                result = chat_loop("How many BRO workers are trapped?", retriever)
                return jsonify({"latest_text": result})
                # return jsonify({"latest_text": data["webpages"][-1]["text"]})  # Return only the latest
    return jsonify({"latest_text": "No stored content found."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
