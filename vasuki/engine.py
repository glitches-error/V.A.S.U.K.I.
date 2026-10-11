"""Game engine: player profiles, XP/level, company unlocking, achievements."""
from . import config, db


def profile(player_id: int) -> dict:
    """Return a rich player profile dict for the UI."""
    p = db.get_player(player_id)
    if p is None:
        return {}
    xp = p["xp"]
    level = config.level_for_xp(xp)
    cur_base = config.xp_for_level(level)
    next_base = config.xp_for_level(level + 1)
    span = max(1, next_base - cur_base)
    into = xp - cur_base
    codes = db.player_achievement_codes(player_id)
    ach = [
        {"code": a["code"], "title": a["title"], "descr": a["descr"],
         "earned": a["code"] in codes}
        for a in db.list_achievements()
    ]
    return {
        "id": p["id"],
        "name": p["name"],
        "xp": xp,
        "level": level,
        "xp_into_level": into,
        "xp_needed": span,
        "xp_to_next": max(0, next_base - xp),
        "progress_pct": round(100 * into / span),
        "achievements": ach,
        "achievements_earned": len(codes),
        "achievements_total": len(ach),
    }


def companies_with_status(player_id: int):
    """List companies annotated with unlock/completion status for this player."""
    level = config.level_for_xp(db.get_player(player_id)["xp"])
    out = []
    for c in db.list_companies():
        tier = config.TIERS[c["tier"]]
        unlocked = level >= tier["unlock_level"]
        out.append({
            "id": c["id"],
            "name": c["name"],
            "tier": c["tier"],
            "tier_name": tier["name"],
            "blurb": c["blurb"],
            "difficulty": tier["difficulty"],
            "xp_mult": tier["xp_mult"],
            "unlock_level": tier["unlock_level"],
            "unlocked": unlocked,
            "passed": db.player_passed_company(player_id, c["id"]),
            "stars": _stars(db.best_drive(player_id, c["id"])["best"]),
            "pattern": config.COMPANY_PATTERN.get(c["name"], "mcq"),
        })
    return out


def _stars(best):
    """0-3 stars for a best score fraction (None = never played)."""
    if best is None:
        return 0
    if best >= 1:
        return 3
    if best >= 0.8:
        return 2
    return 1 if best >= config.PASS_THRESHOLD else 0


def award_drive(player_id, company, score, total):
    """Compute XP, persist the drive, grant achievements. Returns a summary."""
    # Recorded drives store a whole-number score; decide pass/fail on that same
    # value so the map's stars and history always agree with this result.
    score = round(score)
    passed = total > 0 and (score / total) >= config.PASS_THRESHOLD
    tier = config.TIERS[company["tier"]]
    base = round(score * config.XP_PER_CORRECT)
    bonus = config.DRIVE_CLEAR_BONUS if passed else 0
    xp_gained = int((base + bonus) * tier["xp_mult"])

    before = db.get_player(player_id)["xp"]
    level_before = config.level_for_xp(before)
    db.add_xp(player_id, xp_gained)
    db.record_drive(player_id, company["id"], round(score), total, passed, xp_gained)
    after = db.get_player(player_id)["xp"]
    level_after = config.level_for_xp(after)

    new_achievements = _check_achievements(
        player_id, company, score, total, passed, level_after
    )

    return {
        "score": score,
        "total": total,
        "passed": passed,
        "xp_gained": xp_gained,
        "leveled_up": level_after > level_before,
        "level": level_after,
        "new_achievements": new_achievements,
    }


def _check_achievements(player_id, company, score, total, passed, level):
    granted = []

    def give(code):
        if db.grant_achievement(player_id, code):
            a = next((x for x in db.list_achievements() if x["code"] == code), None)
            if a:
                granted.append({"title": a["title"], "descr": a["descr"]})

    drives = db.player_drives(player_id)
    give("first_steps")
    if total > 0 and score == total:
        give("perfect_round")
    if passed and company["tier"] == 4:
        give("giant_slayer")
    if level >= 5:
        give("level_5")
    if len(drives) >= 5:
        give("grinder")
    passed_companies = {d["company_id"] for d in drives if d["passed"]}
    if len(passed_companies) >= 3:
        give("polyglot")
    return granted
