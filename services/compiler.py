import base64
import httpx
from config import settings

# Approximate Language IDs for Judge0 CE
LANGUAGE_MAP = {
    "python": 71,
    "cpp": 54,
    "javascript": 93
}

async def submit_code(source_code: str, language: str, test_inputs: list[str], expected_outputs: list[str]) -> list[dict]:
    """
    Submits user code to Judge0 for execution against provided test cases.
    Returns a list of result dictionaries per test case.
    """
    url = f"https://{settings.JUDGE0_HOST}/submissions"
    headers = {
        "x-rapidapi-key": settings.JUDGE0_API_KEY,
        "x-rapidapi-host": settings.JUDGE0_HOST,
        "content-type": "application/json"
    }
    
    lang_id = LANGUAGE_MAP.get(language.lower(), 71)
    
    async with httpx.AsyncClient() as client:
        results = []
        for inp, exp in zip(test_inputs, expected_outputs):
            payload = {
                "source_code": base64.b64encode(source_code.encode()).decode(),
                "language_id": lang_id,
                "stdin": base64.b64encode(inp.encode()).decode() if inp else None,
                "expected_output": base64.b64encode(exp.encode()).decode() if exp else None,
                "base64_encoded": True
            }
            # We use wait=true for synchronous response from the async API
            resp = await client.post(url, json=payload, headers=headers, params={"wait": "true"})
            if resp.status_code == 200:
                data = resp.json()
                results.append({
                    "status": data.get("status", {}).get("description"),
                    "time": data.get("time"),
                    "memory": data.get("memory"),
                    "stdout": base64.b64decode(data.get("stdout")).decode() if data.get("stdout") else None,
                    "compile_output": base64.b64decode(data.get("compile_output")).decode() if data.get("compile_output") else None
                })
            else:
                results.append({
                    "status": "API Error", 
                    "compile_output": f"HTTP {resp.status_code}: {resp.text}"
                })
        return results
