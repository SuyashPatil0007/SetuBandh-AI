import httpx
from typing import Optional

# Using Sarvam AI / Bhashini REST endpoint
SARVAM_API_KEY = "YOUR_SARVAM_API_KEY"

# ISO Language code mapping for North East India
SUPPORTED_LANGUAGES = {
    "en": "en-IN",       # English
    "as": "as-IN",       # Assamese (অসমীয়া)
    "bn": "bn-IN",       # Bengali (বাংলা)
    "hi": "hi-IN",       # Hindi (हिन्दी)
    "mni": "mni-IN",     # Manipuri / Meitei (মৈতৈলোন্)
    "ne": "ne-IN",       # Nepali (नेपाली)
    "brx": "brx-IN"      # Bodo (बड़ो)
}

async def translate_text(text: str, target_lang: str = "hi") -> str:
    """
    Translates advisory descriptions into the target regional Indian language.
    """
    if target_lang == "en" or not text:
        return text

    target_code = SUPPORTED_LANGUAGES.get(target_lang, "hi-IN")
    
    url = "https://api.sarvam.ai/translate"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "input": text,
        "source_language_code": "en-IN",
        "target_language_code": target_code,
        "mode": "formal"
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("translated_text", text)
    except Exception:
        pass
    return text  # Fallback to English if network/API drops