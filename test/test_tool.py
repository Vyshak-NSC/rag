import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.memory_store import MemoryStore
from rag.client import chroma_client
from rag.retrieval_agent import search_tool, run_retrieval_agent

lore_store = MemoryStore(chroma_client=chroma_client, name='lore')
# results = search_tool('aelunis', lore_store)

# print(results)

result = run_retrieval_agent("What happens to a Cretodastrian if their universe's creator tries to intervene directly?", lore_store)
print("\n=== FINAL GATHERED CONTEXT ===\n", result)