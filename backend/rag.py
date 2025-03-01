from google import genai
import os
import json
from google.genai import types
from dotenv import load_dotenv
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

CHAT_HISTORY_FILE = "chat_history.json"
INPUT_JSON_FILE = "data.json"
load_dotenv()

client = genai.Client(api_key=os.environ["GENAI_API_KEY"])

def init_ret():
    """Initialize the retriever with the latest extracted text."""
    text = ""

    if os.path.exists(INPUT_JSON_FILE):
        with open(INPUT_JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data["webpages"]:
                text += data["webpages"][-1]["text"]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
    splitted_text = text_splitter.split_text(text)

    docs = text_splitter.create_documents(splitted_text)

    embedding_model = "sentence-transformers/all-mpnet-base-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    return retriever

template = """
You are an intelligent AI assistant who answers questions related to text extracted from a webpage.

Answer the question based on the document provided and the chat history. If you can't answer the question from the context document or the chat history, politely say that you don't have enough information from the webpage to answer that specific question.

Be concise and direct in your responses while being helpful and friendly. Format your response in a conversational manner.

The input will be provided as a JSON schema containing the chat history and the current question and the document.

The chat history will be in a field called "history" which will be a list of dictionaries. Each dictionary will have the following fields:
- question: the question asked by the user
- document: the document text provided
- response: the response provided by the assistant (you)

Each dictionary represents a turn in the conversation between you and the user. First dictionary being the start of the conversation.
The current question will be the question in the last history item and the current document will be the document in the last history item.
"""

def load_chat_history():
    """Load existing chat history from a json file or create a new one"""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {"history": []}
    return {"history": []}

def save_chat_history(history):
    """Save chat history to a json file"""
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

def chat_loop(question, retriever):
    """Process user question and maintain chat history."""
    try:
        # Get relevant document chunks using the retriever
        document_context = "\n\n".join([doc.page_content for doc in retriever.invoke(question)])
        
        # Load existing chat history
        history_json = load_chat_history()
        
        # Add new question and context to history
        new_entry = {
            "question": question,
            "document": document_context
        }
        
        # Append new entry to history
        history_json["history"].append(new_entry)
        
        # Keep only the last 10 conversations
        history_json["history"] = history_json["history"][-10:]
        
        # Convert history_json to string
        history_str = json.dumps(history_json, indent=4)
        
        # Get response from Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(system_instruction=template),
            contents=history_str
        )
        
        ai_response = response.text
        
        # Store the response in the history
        history_json["history"][-1]["response"] = ai_response
        
        # Save the updated history
        save_chat_history(history_json)
        
        return ai_response
    
    except Exception as e:
        print(f"Error in chat_loop: {str(e)}")
        return f"I encountered an error while processing your question. Please try again or check the system logs."