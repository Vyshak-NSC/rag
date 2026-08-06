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
# chroma_client.delete_collection(name="lore")
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

def retrieve_context(query, collection_name, n_results=2):
    # Embed query
    DISTANCE_THRESHOLD = 0.75
    query_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[query]
    )
    query_embedding = query_response.embeddings[0].values
    results=collection_name.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    # sample format of result
    # results = {
    #     "ids":       [["aelunis", "god-beast"]],
    #     "documents": [["[[Aelunis]] is the [[God Beast]] of Order...", "The first three beings created..."]],
    #     "metadatas": [[{"links": "aelunis,god-beast"}, {"links": "primordial-creator,veltharas,morvail,aelunis"}]],
    #     "distances": [[0.42, 0.69]]
    # }
    
    
    relevant = []
    
    for id, doc, dist, meta in zip(results["ids"][0], results["documents"][0], results["distances"][0], results["metadatas"][0]):
        if dist <= DISTANCE_THRESHOLD:
            relevant.append({
                "id":id, 
                "doc": doc,
                "meta": meta
            })
    # relevant data format sample
    # relevant = [
    #     {"id": "aelunis",   "doc": "[[Aelunis]] is the [[God Beast]] of Order...", "meta": {"links": "aelunis,god-beast"}},
    #     {"id": "god-beast", "doc": "The first three beings created...",             "meta": {"links": "primordial-creator,veltharas,morvail,aelunis"}}
    # ]
    
    # add to set to prevent link repeatition
    link_set = set()
    for links in relevant:
        if links and links.get("meta").get("links"):
            link_lst = links['meta']['links'].split(",")
            for link in link_lst:
                link_set.add(link)
    # linke set : {"aelunis", "god-beast", "primordial-creator", "veltharas", "morvail"}
    

    # retrieve document for extracted links
    if link_set:
        new_results = collection.get(ids=list(link_set))
    else:
        new_results = {"ids": [], "documents": []}
    
    # Create contect string
    context = ""
    seen_ids = set()
    

    for item in relevant:
        if item.get('id') not in seen_ids:
            context += f"[{item.get('id')}]\n{item.get('doc')}\n\n"
            seen_ids.add(item.get('id'))
            
    for id, doc in zip(new_results['ids'], new_results['documents']):
        if id not in seen_ids:
            context += f"[{id}]\n{doc}\n\n"
            seen_ids.add(id)
            
    return context

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


transcript = []
history = []
HISTORY_LIMIT = 48000
transcript_length = 0

print("Chat Started")
while True:
    user_inp = input("\nUser: ")
    if user_inp.lower() in ("exit","quit",'q'):
        print("Chat Ended")
        break
    
    context = retrieve_context(query=user_inp, collection_name=collection)
    print("\n============================== Context ==============================\n")
    print(context)
    print("\n============================== Context ==============================\n")
    
    user_turn = {
        "role": "user",
        "parts":[{"text":user_inp}]
    }
    transcript.append(user_turn)
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=transcript,
        config={
            "system_instruction": ("Keep responses concise and direct. Use a conversational, natural, and human-like tone, but avoid unnecessary fluff or robotic filler.\n\n"
                                   f"Relevant context for thsi turn:\n{context}"
            )
        }
    )
    
    model_turn = {
        "role":"model",
        "parts": [{"text": response.text}]
    }
    transcript.append(model_turn)
    
    print("Model: ", response.text)
    transcript_length += len(user_inp) + len(response.text)
    # print("\nTranscript length: ", transcript_length)
    # print("Transcript index length: ", len(transcript))
    
    if transcript_length >= HISTORY_LIMIT:
        index = int(len(transcript) * (3/4))
        history.append(transcript[:index])
        del transcript[:index]
    
