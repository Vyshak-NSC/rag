from google import genai
from google.genai import types
from rag.client import gemini_client
from rag.memory_store import MemoryStore

search_tool_description = types.FunctionDeclaration(
    name='search_tool',
    description="Search the world's lore knowledge base for information relevant to a specific concept or question. Call this once per distinct thing you need to know.",
    parameters_json_schema={
        "type":"object",
        "properties":{
            "query": {"type":"string", "description":"A focused search query for one specific piece of information needed."}
        },
        "required":["query"]
    }
)

tool = types.Tool(function_declarations=[search_tool_description])
MAX_ITERATION = 5

def run_retrieval_agent(user_request, memory_store, model="gemini-3.1-flash-lite"):
    contents=[{"role":"user", "parts":[{"text": user_request}]}]
    gathered_context = ""
    
    for i in range(MAX_ITERATION):
        response = gemini_client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[tool],
                system_instruction=(
                    "You are gathering information needed to fulfill the user's request. "
                    "Call search_tool for each distinct fact or concept you need. "
                    "Do not call it for things you already have or that aren't relevant. "
                    "Once you have enough to proceed, respond with plain text saying you're ready — "
                    "do not call the tool again."
                )
            )
        )
        
        if not response.function_calls:
            print(f"Agent stopped after {i} search(es)")
            break
            
        for call in response.function_calls:
            query = call.args["query"]
            print(f"  -> searching: {query}")
            result = search_tool(query, memory_store)
            gathered_context += result

            contents.append({"role": "user", "parts": [{"function_response": {"name": "search_tool", "response": {"result": result}}}]})

    return gathered_context

def search_tool(query, memory_store):
    results = memory_store.search(query)
    
    if not results:
        return "No relevant data found for this query"
    
    formatted =""
    for item in results:
        formatted += f"[{item['id']}]\n[{item['doc']}]\n"
        links = item['meta'].get("links")
        
        if links:
            formatted += f"(references: {links})\n"
        formatted += "\n"
    return formatted