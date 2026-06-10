import json
import re
import logging
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

VISION_MODELS = [
    "google/gemini-2.5-flash-image",   # مخصص للصور
    "google/gemini-2.5-flash",         # fallback عام
    "google/gemini-2.5-flash-lite",    # fallback خفيف
]

client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://github.com/betting-bot",
        "X-Title": "Betting Tips Bot",
    },
)

VISION_PROMPT = """Look at this sports betting screenshot.

Extract ONLY these fields and return ONLY a JSON object, nothing else:
{
  "home_team": "team name in English",
  "away_team": "team name in English",
  "league": "competition name",
  "match_date": "date if visible or null"
}

Important: return ONLY the JSON, no explanation, no markdown."""


async def extract_match_info(image_base64: str) -> dict | None:
    for model in VISION_MODELS:
        try:
            logger.info(f"Trying vision model: {model}")
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                            {"type": "text", "text": VISION_PROMPT},
                        ],
                    }
                ],
                max_tokens=300,
            )

            raw = response.choices[0].message.content.strip()
            logger.info(f"Vision raw response: {raw}")

            raw = re.sub(r"```json|```", "", raw).strip()
            data = json.loads(raw)

            if data.get("home_team") and data.get("away_team"):
                logger.info(f"Match found: {data['home_team']} vs {data['away_team']}")
                return data

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed for {model}: {e} | raw: {raw}")
            continue
        except Exception as e:
            logger.warning(f"Model {model} failed: {e}")
            continue

    logger.error("All vision models failed")
    return None
