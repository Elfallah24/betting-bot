def _confidence_bar(pct: int) -> str:
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)


def format_tips_message(match_info: dict, tips: dict, odds_data: dict | None) -> str:
    home   = match_info["home_team"]
    away   = match_info["away_team"]
    league = match_info.get("league", "")

    has_real_odds = bool(odds_data and odds_data.get("markets"))
    source_line   = "📡 الكوتاسيونات: حية من الـ bookmakers" if has_real_odds else "🤖 الكوتاسيونات: تقدير بالذكاء الاصطناعي"

    lines = [f"⚽️ <b>{home} vs {away}</b>"]
    if league:
        lines.append(f"🏆 {league}")
    lines.append(source_line)

    context = tips.get("context", "")
    if context:
        lines.append(f"\n💡 <i>{context}</i>")

    lines.append("\n━━━━━━━━━━━━━━━━━━")
    lines.append("🎯 <b>أفضل 5 رهانات:</b>\n")

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    for i, bet in enumerate(tips.get("bets", [])):
        medal   = medals[i] if i < len(medals) else f"{i + 1}."
        pct     = bet.get("confidence_pct", 0)
        bar     = _confidence_bar(pct)

        # اسم السوق: عربي (English)
        market_display = f"{bet.get('market_ar', '')} ({bet.get('market', '')})"
        # الاختيار: عربي (English)
        pick_display   = f"{bet.get('pick_ar', '')} ({bet.get('pick', '')})"

        lines.append(
            f"{medal} <b>{pick_display}</b>\n"
            f"   📊 {market_display}\n"
            f"   💰 الكوتا: <code>{float(bet.get('odds', 0)):.2f}</code>\n"
            f"   {bar} <b>{pct}%</b>\n"
            f"   ✅ {bet.get('win_condition', '')}\n"
            f"   ❌ {bet.get('lose_condition', '')}\n"
        )

    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("⚠️ <i>للمعلومات فقط — راهن بمسؤولية.</i>")

    return "\n".join(lines)


def format_error(reason: str) -> str:
    messages = {
        "no_match":  "❌ ما قدرتش نتعرف على الفريقين في الصورة.\nجرب صورة أوضح فيها اسم الفريقين بشكل واضح.",
        "no_tips":   "❌ ما قدرتش نولد تيبسات لهذا الماتش. جرب مرة أخرى.",
        "no_image":  "📸 ابعث لي صورة screenshot ديال الماتش.",
        "not_admin": "⛔ ما مسموحكش تستخدم هذا البوت.",
        "general":   "❌ وقع خطأ غير متوقع. جرب مرة أخرى.",
    }
    return messages.get(reason, messages["general"])
