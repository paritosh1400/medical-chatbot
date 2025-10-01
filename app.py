# from flask import Flask, render_template, request
# from src.helper import download_hugging_face_embeddings
# from langchain_pinecone import PineconeVectorStore
# from langchain_openai import OpenAI
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate
# from dotenv import load_dotenv
# from src.prompt import *
# from langchain_ollama import OllamaLLM
# from langchain.memory import ConversationBufferMemory
# from langchain.memory import ConversationBufferWindowMemory
# from langchain.chains import ConversationalRetrievalChain
# import os

# app = Flask(__name__)

# load_dotenv()
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# if not PINECONE_API_KEY or not OPENAI_API_KEY:
#     raise ValueError("Missing API keys in .env file")

# os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# embeddings = download_hugging_face_embeddings()

# index_name = "medicalbot"
# docsearch = PineconeVectorStore.from_existing_index(
#     index_name=index_name,
#     embedding=embeddings,
# )

# retriever = docsearch.as_retriever(
#     search_type="similarity", 
#     search_kwargs={"k": 3}
# )


# llm = OpenAI(temperature=0.4, max_tokens=500)
# # llm = OllamaLLM(model="llama3", temperature=0.4)

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "Conversation so far:\n{chat_history}\n\nUser: {question}")
# ])

# # question_answer_chain = create_stuff_documents_chain(llm, prompt)
# # rag_chain = create_retrieval_chain(retriever, question_answer_chain)
# memory = ConversationBufferWindowMemory(
#     k=3,  
#     memory_key="chat_history",
#     input_key="question",
#     output_key="answer",
#     return_messages=True
# )

# rag_chain = ConversationalRetrievalChain.from_llm(
#     llm=llm,
#     retriever=retriever,
#     memory=memory,
#     return_source_documents=True,  
#     combine_docs_chain_kwargs={"prompt": prompt}
# )


# @app.route("/")
# def index():
#     return render_template("chat.html")


# @app.route("/get", methods=["POST"])
# # def chat():
# #     msg = request.form.get("msg", "").strip()

# #     if not msg:
# #         return "⚠️ No message provided", 400

# #     if msg.lower() in ["hi", "hello", "hey", "yo", "lol"]:
# #         return "👋 Hello! I’m your medical assistant. How can I help you today?"

# #     results = retriever.get_relevant_documents(msg)

# #     if not results or len(results) == 0:
# #         return "🤔 Sorry, I couldn’t find anything useful in my medical knowledge base. Could you rephrase?"

# #     response = rag_chain.invoke({"input": msg})
# #     return str(response["answer"])
# def chat():
#     msg = request.form.get("msg", "").strip()

#     if not msg:
#         return "No message provided", 400
    
#     if msg.lower() in ["hi", "hello", "hey", "yo", "sup"]:
#         return "Hello! I’m Medibot, your medical assistant. How can I help you today?"

#     response = rag_chain.invoke({"question": msg})
#     return str(response["answer"])


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080, debug=True)

from flask import Flask, render_template, request, jsonify
# from src.helper import download_hugging_face_embeddings
from src.helper import get_openai_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from pymongo import MongoClient
import os, uuid
from datetime import datetime
from zoneinfo import ZoneInfo


app = Flask(__name__)

# ------------------ ENV SETUP ------------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise ValueError("Missing API keys in .env file")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ------------------ MONGO SETUP ------------------
client = MongoClient(MONGO_URI)
db = client["medibot"]
chats_collection = db["chats"]

# ------------------ VECTOR DB ------------------
embeddings = get_openai_embeddings()
index_name = "medicalbot"
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
)
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# ------------------ LLM & PROMPT ------------------
llm = OpenAI(temperature=0.4, max_tokens=500)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "Conversation so far:\n{chat_history}\n\nUser: {question}")
])

# ------------------ HELPERS ------------------
def create_new_chat(title="New Chat"):
    chat_id = str(uuid.uuid4())

    now = datetime.now().astimezone()

    title = now.strftime("%I:%M %p - %B %d, %Y")

    chats_collection.insert_one({
        "_id": chat_id,
        "title": title,
        "created_at": now,
        "messages": []
    })
    return chat_id

def add_message(chat_id, role, content):
    chats_collection.update_one(
        {"_id": chat_id},   # match string ID
        {"$push": {"messages": {
            "role": role,
            "content": content,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }}}
    )

def get_chat_history(chat_id):
    chat = chats_collection.find_one({"_id": chat_id})
    return chat["messages"] if chat else []

def build_memory(chat_id):
    history = get_chat_history(chat_id)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="question",
        output_key="answer",
        return_messages=True
    )
    for msg in history:
        if msg["role"] == "user":
            memory.chat_memory.add_user_message(msg["content"])
        elif msg["role"] == "assistant":
            memory.chat_memory.add_ai_message(msg["content"])
    return memory

# def generate_chat_title(message: str) -> str:
#     base = (message or "").strip()
#     fallback = (base[:40] + "…") if len(base) > 40 else (base or "New Chat")

#     prompt_text = (
#         "Create a short, 2–4 word, Title Case medical topic from this user query.\n"
#         "No punctuation or quotes. Examples: High Fever, Ankle Sprain Care, Antibiotic Side Effects.\n"
#         f"Query: {base}\n"
#         "Title:"
#     )
#     try:
#         # use .invoke correctly
#         response = title_llm.invoke(prompt_text)

#         # response is usually a string if you're using langchain_openai.OpenAI
#         if isinstance(response, str):
#             title = response
#         else:
#             title = getattr(response, "content", str(response))

#         # clean & sanitize
#         title = title.strip().splitlines()[0]
#         title = re.sub(r'^[\'"“”]+|[\'"“”]+$', '', title)   # strip quotes
#         title = re.sub(r'[^A-Za-z0-9 \-]', '', title)       # safe chars
#         title = title.title().strip()[:40]

#         return title or fallback
#     except Exception as e:
#         app.logger.warning(f"Title generation failed, using fallback: {e}")
#         return fallback

# ------------------ ROUTES ------------------
@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/new_chat", methods=["POST"])
def new_chat():
    chat_id = create_new_chat()
    return jsonify({"chat_id": chat_id})

@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg", "").strip()
    chat_id = request.form.get("chat_id")

    if not msg:
        return "No message provided", 400
    if not chat_id:
        return "Chat ID missing", 400
    
    if msg.lower() in ["hi", "hello", "hey", "yo", "sup", "lol"]:
        return "Hello! I’m Medibot, your medical assistant. How can I help you today?"

    # ---- Handle "what did I ask before?" without LLM ----
    if "what did i ask" in msg.lower() or "last question" in msg.lower():
        chat = chats_collection.find_one({"_id": chat_id})
        if chat and chat.get("messages"):
            # find the last user message
            last_user_msg = next(
                (m["content"] for m in reversed(chat["messages"]) if m["role"] == "user"),
                None
            )
            if last_user_msg:
                return f"You asked: \"{last_user_msg}\""
            else:
                return "You haven’t asked me anything yet."
        else:
            return "You haven’t asked me anything yet."

    memory = build_memory(chat_id)

    rag_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt}
    )

    response = rag_chain.invoke({"question": msg})
    answer = response["answer"].strip()

    if answer.lower().startswith("assistant:"):
        answer = answer[len("assistant:"):].strip()
    elif answer.lower().startswith("medibot:"):
        answer = answer[len("medibot:"):].strip()

    # Save both user & assistant messages
    add_message(chat_id, "user", msg)
    add_message(chat_id, "assistant", answer)

    return answer

@app.route("/chats", methods=["GET"])
def list_chats():
    # chats = list(chats_collection.find({}, {"_id": 1, "title": 1, "created_at": 1}))
    # # convert datetime for JSON
    # for c in chats:
    #     c["created_at"] = c["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    # return jsonify(chats)
    chats = list(chats_collection.find({}, {"_id": 1, "title": 1, "created_at": 1, "messages": 1}).sort("created_at", -1))
    for chat in chats:
        if "messages" in chat and chat["messages"]:
            chat["last_message"] = chat["messages"][-1]["content"]  # last message
        else:
            chat["last_message"] = "No messages yet"
        chat["_id"] = str(chat["_id"])
        del chat["messages"]  # don’t send all messages
    return jsonify(chats)

@app.route("/chats/<chat_id>/messages", methods=["GET"])
def get_chat_messages(chat_id):
    chat = chats_collection.find_one({"_id": chat_id})
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify(chat.get("messages", []))

@app.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    result = chats_collection.delete_one({"_id": chat_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)