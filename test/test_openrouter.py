import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

or_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

response = or_client.chat.completions.create(
    model="openai/gpt-oss-20b:free",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}]
)
print(response.choices[0].message.content)