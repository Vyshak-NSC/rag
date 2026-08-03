import os
from dotenv import load_dotenv
from google import genai
import numpy as np
import chromadb

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="lore")

def cosine_similarity(vec_a,vec_b):
    a = np.array(vec_a)
    b = np.array(vec_b)
    
    dot_product = np.dot(a,b)
    mag_a = np.linalg.norm(a)
    mag_b = np.linalg.norm(b)
    return dot_product/(mag_a * mag_b)

embedding_data = ["altaria is as big as sun",
    "alteria is fantasy world with mana as the source of all thing, instead of atoms.",
    "some creatures of alteria can be giant as mountains when at high tiers",
    "terraclaw brute is a tier 1 bear type beast",
    "terraclaw can become colossal or titan class at higher tiers",
    "aerfang stalker is a tier 1 wolf type beast",
    "a rabbit type is weaker and smaller than bear and wolf type"]

response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=embedding_data
)

embeddings = [item.values for item in response.embeddings]
# for item in response.embeddings:
#     embeddings.append(item.values)

collection.upsert(
    ids=[str(x) for x in range(len(embedding_data))],
    documents=embedding_data,
    embeddings=embeddings
)

query = "what do u know of weakest beasts"

query_response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=[query]
)

query_embedding = query_response.embeddings[0].values

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

print(results['documents'])