# from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
# # from pinecone.grpc import PineconeGRPC as Pinecone
# from pinecone import ServerlessSpec, Pinecone
# from langchain_pinecone import PineconeVectorStore
# from dotenv import load_dotenv
# import os

# load_dotenv()
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# if not PINECONE_API_KEY:
#     raise ValueError("Missing PINECONE_API_KEY in .env")

# pc = Pinecone(api_key=PINECONE_API_KEY)
# index_name = "medicalbot"

# print("Getting Data")
# extracted_data = load_pdf_file(data="Data/")
# text_chunks = text_split(extracted_data)
# print(f"✅ Loaded {len(text_chunks)} text chunks")

# print("Using OpenAI embeddings")
# embeddings = download_hugging_face_embeddings()

# if index_name not in [i.name for i in pc.list_indexes()]:
#     print("Creating Pinecone index")
#     pc.create_index(
#         name=index_name,
#         dimension=1536,   
#         metric="cosine",
#         spec=ServerlessSpec(cloud="aws", region="us-east-1")
#     )

# docsearch = PineconeVectorStore.from_documents(
#     documents=text_chunks,
#     index_name=index_name,
#     embedding=embeddings
# )

# print(f"Stored {len(text_chunks)} chunks into Pinecone index '{index_name}'.")

from src.helper import load_pdf_file, text_split, get_openai_embeddings
from pinecone import ServerlessSpec, Pinecone
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY in .env")

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "medicalbot"

print("Getting Data")
extracted_data = load_pdf_file(data="Data/")
text_chunks = text_split(extracted_data)
print(f"Loaded {len(text_chunks)} text chunks")

embeddings = get_openai_embeddings()  

if index_name in [i.name for i in pc.list_indexes()]:
    print(f"⚠️ Index '{index_name}' already exists, deleting it...")
    pc.delete_index(index_name)

print("Creating Pinecone index with dim=1536")
pc.create_index(
    name=index_name,
    dimension=1536, 
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# embeddings in Pinecone
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings
)

print(f"Stored {len(text_chunks)} chunks into Pinecone index '{index_name}'.")