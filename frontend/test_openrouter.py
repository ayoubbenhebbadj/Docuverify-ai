
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")

if not api_key or not model:
    raise RuntimeError(
        "Set OPENROUTER_API_KEY and OPENROUTER_MODEL in .env"
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": (
                "Reply with exactly: "
                "DocuVerify AI connection successful."
            ),
        }
    ],
    max_tokens=100,
)

print("Model:", response.model)
print("Response:", response.choices[0].message.content)
