from dotenv import load_dotenv
import httpx
import os

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"


def get_openrouter_api_key() -> str:
    """Return the configured OpenRouter API key from the environment.

    Returns:
        The non-empty OpenRouter API key.

    Raises:
        RuntimeError: If the API key is missing.
    """
    api_key = os.getenv("OPEN_ROUTER_API_KEY", "").strip()
    print(api_key)
    if not api_key:
        raise RuntimeError("OPEN_ROUTER_API_KEY is not set")
    return api_key


def complete_prompt(prompt: str) -> str:
    """Send one prompt to OpenRouter and return the first response message.

    Args:
        prompt: User prompt text to send to the model.

    Returns:
        The first assistant message content.

    Raises:
        RuntimeError: If configuration is missing or the API response is invalid.
        httpx.HTTPError: If the request fails.
    """
    response = httpx.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {get_openrouter_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30.0,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if not content.strip():
        raise RuntimeError("OpenRouter returned an empty response")
    return content
