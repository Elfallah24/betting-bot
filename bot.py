import asyncio
import base64
import io
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from config import TELEGRAM_BOT_TOKEN, ADMIN_ID
from database.db import Database
from services.vision import extract_match_info
from services.odds import get_match_odds
from services.analyzer import generate_tips
from utils.formatter import format_tips_message, format_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp  = Dispatcher()
db  = Database()


# ── auth ─────────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ── handlers ─────────────────────────────────────────────────────────────────

@dp.message(Command("start", "help"))
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "👋 <b>أهلاً!</b>\n\n"
        "ابعث لي <b>صورة screenshot</b> ديال الماتش وأنا نعطيك:\n\n"
        "🎯 أفضل 5 رهانات مرتبين\n"
        "💰 الكوتاسيون ديال كل رهان\n"
        "📊 نسبة النجاح\n\n"
        "<i>الصورة خاصها تكون واضحة وفيها اسم الفريقين.</i>",
        parse_mode="HTML",
    )


@dp.message(F.photo)
async def handle_photo(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(format_error("not_admin"))
        return

    status = await message.answer("⏳ كنقرأ الصورة...")

    try:
        # ── 1. Download image ─────────────────────────────────────
        photo      = message.photo[-1]           # highest resolution
        file_info  = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        image_b64  = base64.b64encode(
            file_bytes.read() if hasattr(file_bytes, "read") else file_bytes
        ).decode("utf-8")

        # ── 2. Extract match info from image ──────────────────────
        await status.edit_text("🔍 كنتعرف على الماتش...")
        match_info = await extract_match_info(image_b64)

        if not match_info:
            await status.edit_text(format_error("no_match"))
            return

        home   = match_info["home_team"]
        away   = match_info["away_team"]
        league = match_info.get("league", "")

        # ── 3. Check cache ────────────────────────────────────────
        cached = db.get_cached_tips(home, away)
        if cached:
            logger.info(f"Cache hit: {home} vs {away}")
            await status.delete()
            await message.answer(cached, parse_mode="HTML")
            return

        # ── 4. Fetch bookmaker odds ───────────────────────────────
        await status.edit_text(f"📡 كنجيب الكوتاسيونات: {home} vs {away}...")
        odds_data = await get_match_odds(home, away, league)

        # ── 5. Generate tips ──────────────────────────────────────
        await status.edit_text("🧠 كنحلل ونولد التيبسات...")
        tips = await generate_tips(match_info, odds_data)

        if not tips or not tips.get("bets"):
            await status.edit_text(format_error("no_tips"))
            return

        # ── 6. Format + send ──────────────────────────────────────
        response = format_tips_message(match_info, tips, odds_data)

        db.cache_tips(home, away, response)
        db.log_request(home, away, bool(odds_data))

        await status.delete()
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        await status.edit_text(format_error("general"))


@dp.message(F.text)
async def handle_text(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(format_error("no_image"))


# ── main ─────────────────────────────────────────────────────────────────────

async def main():
    db.init()
    logger.info("Bot is starting...")
    await dp.start_polling(bot, allowed_updates=["message"])


if __name__ == "__main__":
    asyncio.run(main())
