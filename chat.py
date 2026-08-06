from rag.memory_store import MemoryStore
from rag.chat_session import ChatSession
from rag.client import chroma_client

lore_store = MemoryStore(chroma_client, name="lore")
history_store = MemoryStore(chroma_client, name="chat_history")

session = ChatSession(memory_store=lore_store, history_store=history_store)

print("Chat started")
while True:
    user_inp = input("\nUser : ")
    if user_inp.lower() in ("q", "e","quit","exit"):
        print("\nChat ended\n")
        break
    
    reply = session.send(user_inp)
    print("Model: ", reply)