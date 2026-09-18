import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List
from config import settings

# Initialize the google-genai client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class TestCase(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False

class StarterCode(BaseModel):
    cpp: str
    python: str
    javascript: str

class CodingChallenge(BaseModel):
    title: str
    difficulty: str
    story_narrative: str
    constraints: List[str]
    starter_templates: StarterCode
    test_cases: List[TestCase]

async def generate_challenge(topic: str) -> dict:
    """Generates a competitive coding challenge using Gemini."""
    prompt = (
        f"Generate a competitive coding challenge based on the topic: {topic}. "
        "Provide a title, difficulty (easy/medium/hard), an engaging eSports-style story narrative, "
        "constraints, starter templates for C++, Python, and JS, and at least 4 test cases (2 public, 2 hidden)."
    )
    
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CodingChallenge,
        ),
    )
    return json.loads(response.text)
