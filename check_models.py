import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"}
)

data = json.loads(urllib.request.urlopen(req).read())
gemini_models = [m["id"] for m in data["data"] if "gemini" in m["id"].lower()]

print("=== Gemini models available ===")
for m in sorted(gemini_models):
    print(m)