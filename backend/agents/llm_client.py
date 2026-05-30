import httpx
import logging
import json
from typing import Dict, Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

async def call_ollama(prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
    """
    Direct asynchronous HTTP call to the local Ollama service.
    If json_mode is True, tells Ollama to respond in JSON format.
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    # Construct full prompt with system prompt if provided
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1  # lower temperature for analytical tasks
        }
    }
    
    if json_mode:
        payload["format"] = "json"
        
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Ollama returned error {response.status_code}: {response.text}")
                return "{}" if json_mode else "Error calling LLM."
                
            res_json = response.json()
            return res_json.get("response", "").strip()
            
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        # Return empty JSON or plain text depending on JSON mode
        return "{}" if json_mode else f"Error: LLM service is unreachable ({e})."
