from functools import lru_cache
from app.config import settings

@lru_cache(maxsize=1)
def get_llm():
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0,
        )
    except Exception:
        return None
