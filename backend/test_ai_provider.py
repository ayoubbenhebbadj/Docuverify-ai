"""Smoke test for the configured Hugging Face/OpenRouter chat API."""
from app.ai_extractor import client, model, AI_PROVIDER

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "Reply with exactly: DocuVerify API connection successful."}
    ],
    max_tokens=40,
)

print(f"Provider: {AI_PROVIDER}")
print(f"Model: {model}")
print(response.choices[0].message.content)
