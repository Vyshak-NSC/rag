from rag.client import gemini_client
from rag.retrieval_agent import run_retrieval_agent


class ChatSession:
    def __init__(self, memory_store, history_store, turn_limit=40, model="gemini-3.1-flash-lite"):
        self.memory_store  = memory_store
        self.history_store = history_store
        self.turn_limit    = turn_limit
        self.model         = model
        self.transcript    = []
        self._exchange_counter = 0
        
        self.last_memory_context = None
        self.last_historyy_context = None
    
    def _drain_if_needed(self):
        if not len(self.transcript) > self.turn_limit:
            return

        drain_count = int(self.turn_limit * 0.75)
        drain_count -= drain_count % 2
        
        old_transcript  = self.transcript[:drain_count] 
        del self.transcript[:drain_count]
        
        ids = []
        texts = []
        
        for i in range(0, len(old_transcript), 2):
            user_turn = old_transcript[i]
            model_turn = old_transcript[i + 1]
            
            user_text = user_turn["parts"][0]["text"]
            model_text = model_turn["parts"][0]["text"]
            
            exchange_text = f"User: {user_text}\nModel: {model_text}"
            exchange_id = f"exchange-{self._exchange_counter}"
            
            texts.append(exchange_text)
            ids.append(exchange_id)
            
            self._exchange_counter += 1
        
        self.history_store.upsert(ids=ids, texts=texts, metadatas=None)
    
    def send(self, user_inp):
        memory_context  = run_retrieval_agent(user_inp, self.memory_store)
        history_context = self.history_store.retrieve_content(user_inp)
        
        self.last_memory_context = memory_context
        self.last_history_context = history_context
        
        self.transcript.append({"role":"user","parts":[{"text":user_inp}]})
        
        response = gemini_client.models.generate_content(
            model=self.model,
            contents=self.transcript,
            config={
                "system_instruction":(
                    "Keep responses concise and direct. Use a conversational, natural, and human-like tone, but avoid unnecessary fluff or robotic filler.\n\n"
                    "Search relevant data in the rag sustem, only if not availabel wil you search in the web."
                    f"Relevant knowledge for this chunk:\n{memory_context}\n\n"
                    f"Relevant past conversation history for this chunk:\n{history_context}\n\n"
                )
            }
        )
        
        self.transcript.append({"role":"model","parts":[{"text": response.text}]})
        self._drain_if_needed()

        return response.text
