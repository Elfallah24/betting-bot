import sqlite3
from datetime import datetime, timedelta
from config import CACHE_HOURS

DB_PATH = "betting_bot.db"


class Database:

    def init(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tips_cache (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_key  TEXT UNIQUE,
                    response   TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests_log (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team  TEXT,
                    away_team  TEXT,
                    had_odds   INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    # ── helpers ──────────────────────────────────────────────────

    def _key(self, home: str, away: str) -> str:
        return f"{home.lower().strip()}_vs_{away.lower().strip()}"

    # ── cache ─────────────────────────────────────────────────────

    def get_cached_tips(self, home: str, away: str) -> str | None:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT response FROM tips_cache WHERE match_key=? AND expires_at > ?",
                (self._key(home, away), datetime.now())
            ).fetchone()
        return row[0] if row else None

    def cache_tips(self, home: str, away: str, response: str):
        expires = datetime.now() + timedelta(hours=CACHE_HOURS)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO tips_cache (match_key, response, expires_at) VALUES (?,?,?)",
                (self._key(home, away), response, expires)
            )
            conn.commit()

    # ── log ───────────────────────────────────────────────────────

    def log_request(self, home: str, away: str, had_odds: bool):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO requests_log (home_team, away_team, had_odds) VALUES (?,?,?)",
                (home, away, int(had_odds))
            )
            conn.commit()
