from rag.client import chroma_client
from rag.memory_store import MemoryStore
from rag.ingestion import load_md_files, stringify_list

lore_store = MemoryStore(chroma_client, name="lore")

data = load_md_files("./docs")
texts = [item["text"] for item in data]
ids = [item["filename"] for item in data]
metadatas = [{"links": stringify_list(item["links"])} for item in data]

lore_store.upsert(ids=ids, texts=texts, metadatas=metadatas)
print(f"Ingested {len(ids)} files.")