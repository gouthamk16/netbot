from google import genai
import os
import json
from google.genai import types
from dotenv import load_dotenv
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough

CHAT_HISTORY__FILE = "chat_history.json"
INPUT_JSON_FILE = "data.json"
load_dotenv()

client = genai.Client(api_key=os.environ["GENAI_API_KEY"])

def init_ret():
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
    retriever = vectorstore.as_retriever()

    return retriever

template = """
    You are an intelligent AI assistant who answers questions related to text extracted from a webpage (referred to as document).\n
    Answer the question given only based on the document provided and the chat history. If you can't answer the question from the context document or the chat history, reply "I can't answer the questtion from the webpage provided".
    Provide the answer alone without any additional text or formatting.\n
    The input will be a provided as a json schema containing the chat history and the current question and the document. \n
    The chat history will be in a field called "history" which will be a list of dictionaries. Each dictionary will have the following fields:\n
    - question: the question asked by the user\n
    - document: the document text provided\n
    - response: the response provided by the assistant (you)\n
    Each dictionary represents a turn in the conversation between you and the user. First dictionary being the start of the conversation\n
    The current question will be the question in the last history item and the current document will be the document in the last history item.\n
    As said before, the response for the question should also cater to the chat history provided along with the document.\n
"""

# Idea is to create a json file that stores the chat history and provide it to the model to generate the response
def load_chat_history():
    """Load existing chat hsitory from a json file or create a new one"""
    if os.path.exists(CHAT_HISTORY__FILE):
        with open(CHAT_HISTORY__FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {"history": []}
    return {"history": []}

def save_chat_history(history):
    """Save chat history to a json file"""
    with open(CHAT_HISTORY__FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

def chat(question, document):
    """Converse with gemini and handle history"""
    history_json = load_chat_history()
    new_entry = {
        "question": question,
        "document": document
    }

    # Append new entry to history
    history_json["history"].append(new_entry)

    # Keep only the last 10 conversations
    history_json["history"] = history_json["history"][-10:]

    # Convert history_json to string
    history_str = json.dumps(history_json, indent=4)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config = types.GenerateContentConfig(system_instruction = template),
        contents = history_str
    )

    ai_response = response.text

    # Store the response on the history
    history_json["history"][-1]["response"] = ai_response

    # Save the updated history
    save_chat_history(history_json)

    return ai_response

# Main chat loop
def chat_loop(question, retriever):

    document_context = retriever.invoke(question)[0].page_content
    
    # Get AI response
    response = chat(question, document_context)

    return response