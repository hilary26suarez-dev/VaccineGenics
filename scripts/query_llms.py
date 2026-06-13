"""
LLM Council — queries multiple LLMs via GitHub Models (Azure AI Inference).
Uses GITHUB_TOKEN (already in .env) to access GPT-4o and Llama-3.3-70B.
Falls back to OPENAI_API_KEY / GEMINI_API_KEY if available.
Usage: python scripts/query_llms.py "your prompt here"
"""
import sys
import json
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_ENDPOINT = "https://models.inference.ai.azure.com"

def query_model(model: str, prompt: str, label: str) -> dict:
    try:
        from openai import OpenAI
        # Prefer direct OpenAI key, fall back to GitHub Models
        openai_key = os.getenv("OPENAI_API_KEY", "")
        github_token = os.getenv("GITHUB_TOKEN", "")

        if openai_key and "gpt" in model:
            client = OpenAI(api_key=openai_key)
        elif github_token:
            client = OpenAI(base_url=GITHUB_ENDPOINT, api_key=github_token)
        else:
            return {"label": label, "model": model, "response": "ERROR: No API key available"}

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.7,
        )
        return {
            "label": label,
            "model": model,
            "response": resp.choices[0].message.content.strip()
        }
    except Exception as e:
        return {"label": label, "model": model, "response": f"ERROR: {e}"}


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello"

    # Query two different models for diverse perspectives
    model1 = os.getenv("OPENAI_MODEL", "gpt-4o-mini")       # ChatGPT perspective
    model2 = os.getenv("SECOND_MODEL", "Llama-3.3-70B-Instruct")  # Llama perspective

    result1 = query_model(model1, prompt, "ChatGPT (GPT-4o-mini)")
    result2 = query_model(model2, prompt, "Meta Llama 3.3 70B")

    output = {
        "prompt": prompt,
        "responses": [result1, result2]
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
