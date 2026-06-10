import aiohttp
import logging
from config import ODDS_API_KEY

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"

# Soccer sport keys — ordered by popularity
SOCCER_SPORTS = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "soccer_uefa_europa_league",
    "soccer_portugal_primeira_liga",
    "soccer_netherlands_eredivisie",
    "soccer_turkey_super_league",
    "soccer_saudi_premier_league",
    "soccer_morocco_botola_pro",
]

LEAGUE_MAP = {
    "premier league": ["soccer_epl"],
    "epl":            ["soccer_epl"],
    "la liga":        ["soccer_spain_la_liga"],
    "bundesliga":     ["soccer_germany_bundesliga"],
    "serie a":        ["soccer_italy_serie_a"],
    "ligue 1":        ["soccer_france_ligue_one"],
    "champions league": ["soccer_uefa_champs_league"],
    "ucl":            ["soccer_uefa_champs_league"],
    "europa league":  ["soccer_uefa_europa_league"],
    "botola":         ["soccer_morocco_botola_pro"],
}


def _normalize(s: str) -> str:
    return s.lower().strip()


def _teams_match(extracted: str, api_name: str) -> bool:
    e = _normalize(extracted)
    a = _normalize(api_name)
    return e in a or a in e or e == a


def _sport_keys_for_league(league: str) -> list[str]:
    league_low = league.lower()
    for key, sports in LEAGUE_MAP.items():
        if key in league_low:
            return sports
    return SOCCER_SPORTS  # fallback: try all


async def get_match_odds(home: str, away: str, league: str = "") -> dict | None:
    if not ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set — skipping odds fetch")
        return None

    sport_keys = _sport_keys_for_league(league)

    async with aiohttp.ClientSession() as session:
        for sport_key in sport_keys:
            try:
                params = {
                    "apiKey":      ODDS_API_KEY,
                    "regions":     "eu",
                    "markets":     "h2h,totals,btts",
                    "oddsFormat":  "decimal",
                }
                async with session.get(
                    f"{BASE_URL}/sports/{sport_key}/odds", params=params
                ) as resp:
                    if resp.status != 200:
                        continue

                    games = await resp.json()

                    for game in games:
                        g_home = game.get("home_team", "")
                        g_away = game.get("away_team", "")

                        home_match = _teams_match(home, g_home) or _teams_match(home, g_away)
                        away_match = _teams_match(away, g_home) or _teams_match(away, g_away)

                        if home_match and away_match:
                            logger.info(f"Found odds: {g_home} vs {g_away} [{sport_key}]")
                            return _parse_odds(game)

            except Exception as e:
                logger.error(f"Odds API error [{sport_key}]: {e}")
                continue

    logger.info(f"No odds found for {home} vs {away} — will use AI estimates")
    return None


def _parse_odds(game: dict) -> dict:
    """Collect best (highest) odds per outcome across all bookmakers."""
    result = {
        "home_team":      game["home_team"],
        "away_team":      game["away_team"],
        "commence_time":  game.get("commence_time"),
        "markets":        {},
    }

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            key = market["key"]
            if key not in result["markets"]:
                result["markets"][key] = {}

            for outcome in market.get("outcomes", []):
                name  = outcome["name"]
                price = outcome["price"]
                # Keep the best (highest) odds available
                if name not in result["markets"][key] or price > result["markets"][key][name]:
                    result["markets"][key][name] = price

    return result
