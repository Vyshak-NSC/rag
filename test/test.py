import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# response = client.models.list()
# for i in response:
#     print(i.name)

model_list = [
# 'gemini-pro-latest',
# 'gemini-flash-lite-latest',
# 'gemini-flash-latest',
'gemini-3.6-flash'
'gemini-3.5-flash-lite',
'gemini-3.5-flash',
'gemini-3.1-flash-lite',
'gemini-2.5-flash-lite',
'gemini-2.5-pro',
'gemini-2.5-flash',
'gemini-2.0-flash-lite',
'gemini-2.0-flash',

]
# def get_response():
#     for model in model_list:
# try:
transcript = []

while True:
    user_inp = input("\nUser: ")
    if user_inp.lower() == "exit":
        print("Chat ended")
        break
    # return "chat ended"
    
    user_turn = {
        "role": "user",
        "parts": [{"text":user_inp}]    
    }
    transcript.append(user_turn)
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=transcript,
        config={
            "system_instruction": "Keep responses concise and direct. Use a conversational, natural, and human-like tone, but avoid unnecessary fluff or robotic filler."
        }
    )

    model_turn = {
        "role": "model",
        "parts":[{"text": response.text}]
    }
    transcript.append(model_turn)
    print("Model: ", response.text)
            # return {"model": model, "response":response.text}

# except:
#     print(f"Model: {model} failed.")
    # continue

# res = get_response()

# print(res.get("model", None))
# print(res.get("response", None))