import os
import re
from dotenv import load_dotenv
from google import genai
import numpy as np
import chromadb

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# set up chroma db
chroma_client = chromadb.PersistentClient(path="./chroma_data")
chroma_client.delete_collection(name="lore")
collection = chroma_client.get_or_create_collection(name="lore")

def stringify_list(lst):
    return ",".join(lst).replace(" ", "-").lower()

def load_files(path):
    data = []
    files = [file for file in os.listdir(path) if file.endswith('.md')]
    
    for file in files:
        full_path = os.path.join(path,file)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            links = re.findall(r'\[\[(.*?)\]\]', content)
            
            res = { "filename" : file.removesuffix('.md'), "text" : content, "links":links}
            data.append(res)
    return data

data = load_files("./docs")

texts = [item["text"] for item in data]
ids   = [item["filename"] for item in data]

response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=texts
)

embeddings = [item.values for item in response.embeddings]
metadatas = [{"links":stringify_list(item["links"])} for item in data]

collection.upsert(
    ids=ids,
    documents=texts,
    embeddings=embeddings,
    metadatas=metadatas
)


def retrieve_context(query, n_results=2):
    # Embed query
    query_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[query]
    )
    query_embedding = query_response.embeddings[0].values
    results=collection.query(query_embeddings=[query_embedding],n_results=n_results)

    # print("Results: \n", results['ids'])
    # print()
    # print("Results: \n", results['documents'])
    # print()
    # Extract links from result to corresponding documents
    # metadata :
    # [[{'links': 'filename1,filename2'},{'links':'filename1,filename2'}]]
    # metadat[0] for response for single query
    
    # add to set to prevent link repeatition
    link_set = set()
    for links in results["metadatas"][0]:
        if links and links.get("links"):
            link_lst = links['links'].split(",")
            for link in link_lst:
                link_set.add(link)
    
    # retrieve document for extracted links
    new_results = collection.get(ids=list(link_set))
    
    # Create contect string
    context = ""
    seen_ids = set()
    
    for id, doc in zip(results['ids'][0], results['documents'][0]):
        if id not in seen_ids:
            context += f"[{id}]\n{doc}\n\n"
            seen_ids.add(id)
            
    for id, doc in zip(new_results['ids'], new_results['documents']):
        if id not in seen_ids:
            context += f"[{id}]\n{doc}\n\n"
            seen_ids.add(id)
            
    # print("Results: \n", results)
    # print()
    # print("links :\n", link_set)
    # print()
    # print("link Results: \n", new_results)
    return context

print(retrieve_context("tell me about aelunis"))