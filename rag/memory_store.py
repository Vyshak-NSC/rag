from rag.client import gemini_client
from rag.ingestion import stringify_list

class MemoryStore:
    def __init__(self, chroma_cleint, name, distance_threshold=0.75):
        self.collection = chroma_cleint.get_or_create_collection(name=name)
        self.distance_threshold = distance_threshold
    
    def upsert(self, ids, texts, metadatas=None, model_name="gemini-embedding-001"):
        embedded_response = gemini_client.models.embed_content(
            model=model_name,
            contents=texts
        )
        
        embeddings = [item.values for item in embedded_response.embeddings]
        self.collection.upsert(
            ids = ids,
            documents  = texts,
            embeddings = embeddings,
            metadatas  = metadatas
        )
    
    def retrieve_content(self, query, n_results=2, model="gemini-embedding-001"):
        query_resp = gemini_client.models.embed_content(
            model=model,
            contents=[query]
        )
        
        query_embedding = query_resp.embeddings[0].values
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas","distances"]
        )
        
        relevant = []
        
        for id, doc, dist, meta in zip(results["ids"][0], results["documents"][0], results["distances"][0], results["metadatas"][0]):
            if dist <= self.distance_threshold:
                relevant.append({
                    "id"  : id,
                    "doc" : doc,
                    "meta": meta
                })
        
        link_set = set()
        for item in relevant:
            if item and item.get('meta') and item.get("meta").get("links"):
                link_lst = item['meta']['links'].split(",")
                for link in link_lst:
                    link_set.add(link)
        
        if link_set:
            link_results = self.collection.get(ids=list(link_set))
        else:
            link_results = {"ids":[], "documents":[]}
        
        
        context = ""
        seen_ids = set()
        
        for item in relevant:
            if item.get('id') not in seen_ids:
                context += f"[{item.get('id')}]\n{item.get('doc')}\n\n"
                seen_ids.add(item.get('id'))
                
        for id, doc in zip(link_results['ids'], link_results['documents']):
            if id not in seen_ids:
                context += f"[{id}]\n{doc}\n\n"
                seen_ids.add(id)
        
        return context