import json
import logging
from openai import AsyncOpenAI
from config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    GEMINI_MODEL, MIN_ODDS, TOP_BETS_COUNT
)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://github.com/betting-bot",
        "X-Title": "Betting Tips Bot",
    },
)

SYSTEM_PROMPT = (
    "You are an elite football betting analyst with 20 years of experience. "
    "You think like a professional bettor: you look for VALUE, not just favorites. "
    "Always respond with valid JSON only — no markdown, no explanation outside the JSON."
)


def _build_prompt(match_info: dict, odds_data: dict | None) -> str:
    home   = match_info["home_team"]
    away   = match_info["away_team"]
    league = match_info.get("league", "Unknown")

    if odds_data and odds_data.get("markets"):
        odds_section = (
            "CURRENT BOOKMAKER ODDS (best available):\n"
            + json.dumps(odds_data["markets"], indent=2)
        )
        odds_note = (
            "Use these real odds. Calculate implied probability for each outcome "
            "and compare to your estimated TRUE probability."
        )
    else:
        odds_section = (
            "No bookmaker odds available. "
            "Estimate realistic decimal odds for each market based on team analysis."
        )
        odds_note = (
            "Provide estimated odds for each bet. "
            "Only include bets where your estimated odds would be >= 1.50."
        )

    return f"""
MATCH: {home} vs {away}
COMPETITION: {league}

{odds_section}

INSTRUCTIONS:
1. Analyze both teams: recent form (last 5 games), head-to-head record, home/away performance,
   key absences, tactical tendencies, goal-scoring and defensive stats.
2. {odds_note}
3. EXCLUDE any bet with odds below {MIN_ODDS}.
4. Find the top {TOP_BETS_COUNT} VALUE BETS — where true probability > implied probability.
5. Rank by confidence (highest first).

RESPOND WITH THIS EXACT JSON:
{{
  "match_context": "2-3 sentences about key factors affecting this match",
  "bets": [
    {{
      "rank": 1,
      "market": "market type (1X2 / Over-Under / BTTS / Double Chance / Asian Handicap / etc)",
      "pick": "exact selection (e.g. Home Win / Over 2.5 Goals / BTTS Yes)",
      "odds": 1.85,
      "confidence_pct": 74,
      "value_reason": "one sentence why this is a value bet"
    }}
  ]
}}
"""


async def generate_tips(match_info: dict, odds_data: dict | None) -> dict | None:
    try:
        response = await client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": _build_prompt(match_info, odds_data)},
            ],
            max_tokens=1200,
            temperature=0.2,
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)
        bets = data.get("bets", [])

        # Hard filter: remove anything below MIN_ODDS
        bets = [b for b in bets if float(b.get("odds", 0)) >= MIN_ODDS]

        # Sort by confidence descending
        bets.sort(key=lambda x: x.get("confidence_pct", 0), reverse=True)

        return {
            "context": data.get("match_context", ""),
            "bets":    bets[:TOP_BETS_COUNT],
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in analyzer: {e}")
        return None
    except Exception as e:
        logger.error(f"Analyzer error: {e}")
        return None
