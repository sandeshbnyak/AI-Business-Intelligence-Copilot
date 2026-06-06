import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Singleton Groq client
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"Warning: Could not initialize Groq client. Check API Key. {e}")
    groq_client = None

def get_llm_response(prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 1024, temperature: float = 0.0) -> str:
    """Wrapper function to easily call Groq inference."""
    if not groq_client:
        return "Error: Groq client not initialized. Check GROQ_API_KEY in .env."
        
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error communicating with LLM: {str(e)}"
