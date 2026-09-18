from google import genai
from google.genai import types
from config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def generate_shoutcast(event_log: str) -> str:
    """Generates a witty eSports commentator line based on a match event."""
    prompt = (
        "You are a hype eSports shoutcaster for a live coding tournament. "
        f"React to this event in exactly one witty, energetic sentence: '{event_log}'"
    )
    
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.8,
        )
    )
    return response.text.strip()
