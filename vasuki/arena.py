"""Arena: asynchronous head-to-head battles between two players.

Both players get the same questions in the same order. Each question is timed
server-side (the clock starts when the question is served), scored with a speed
bonus and a combo multiplier, and costs a life when missed. A player's run ends
when they finish every question or run out of lives. When both runs are over,
the battle is settled and XP is awarded.

Answers are graded here, never in the browser — the client only ever sees the
current question's prompt and options.
"""
import json
import time
from datetime import datetime, timezone, timedelta

from . import config, db


class ArenaError(Exception):
    """A user-facing problem (unknown codename, not your battle, ...)."""


# ---- creating / answering invites ---------------------------------------

def challenge(challenger_id: int, opponent_name: str, difficulty: int) -> int:
    opponent = db.get_player_by_name((opponent_name or "").strip())
    if opponent is None:
        raise ArenaError("No candidate with that codename exists in the simulation.")
    if opponent["id"] == challenger_id:
        raise ArenaError("You can't battle yourself. V.A.S.U.K.I. finds that amusing.")
    difficulty = difficulty if difficulty in config.BATTLE_MODES else 2
    qids = db.pick_battle_questions(difficulty, config.BATTLE_QUESTIONS)
    if not qids:
        raise ArenaError("The question bank is empty.")
    return db.create_battle(challenger_id, opponent["id"], difficulty, json.dumps(qids))


def decline(battle_id: int, player_id: int):
    b = _battle_for(battle_id, player_id)
    entry = db.get_entry(battle_id, player_id)
    if b["opponent_id"] != player_id or b["status"] != "open" or entry["q_index"] > 0:
        raise ArenaError("This battle can't be declined any more.")
    db.set_battle_status(battle_id, "declined")


# ---- playing ---------------------------------------------------------------

def state(battle_id: int, player_id: int) -> dict:
    """Everything the battle screen needs, including the current question."""
    b = _battle_for(battle_id, player_id)
    me = db.get_entry(battle_id, player_id)
    rival_id = b["opponent_id"] if b["challenger_id"] == player_id else b["challenger_id"]
    rival = db.get_entry(battle_id, rival_id)
    qids = json.loads(b["question_ids"])

    out = {
        "id": b["id"],
        "status": b["status"],
        "mode": config.BATTLE_MODES[b["difficulty"]]["name"],
        "total": len(qids),
        "time_limit": config.BATTLE_TIME_LIMIT,
        "me": _entry_view(me, db.get_player(player_id)["name"]),
        "rival": _entry_view(rival, db.get_player(rival_id)["name"]),
        "rival_trace": [a["score_after"] for a in db.battle_answers(battle_id, rival_id)],
        "question": None,
        "result": None,
    }

    if b["status"] == "open" and not me["finished"]:
        # Start this question's clock the first time it is served.
        served = me["served_at"]
        if served is None:
            served = time.time()
            db.update_entry(battle_id, player_id, served_at=served)
        q = db.get_question(qids[me["q_index"]])
        out["question"] = {
            "index": me["q_index"],
            "round": q["round"],
            "continent": config.CONTINENTS[config.ROUND_CONTINENT[q["round"]]]["name"],
            "prompt": q["prompt"],
            "options": json.loads(q["options"]),
            "remaining": max(0.0, config.BATTLE_TIME_LIMIT - (time.time() - served)),
        }
    if b["status"] == "done":
        out["result"] = _result_view(b, player_id)
    return out


def answer(battle_id: int, player_id: int, q_index: int, chosen) -> dict:
    """Grade one answer. `chosen` is an option index or None (timed out)."""
    b = _battle_for(battle_id, player_id)
    me = db.get_entry(battle_id, player_id)
    if b["status"] != "open" or me["finished"]:
        raise ArenaError("This run is already over.")
    if q_index != me["q_index"]:
        raise ArenaError("Out of sync — reload the battle.")

    qids = json.loads(b["question_ids"])
    q = db.get_question(qids[q_index])
    served = me["served_at"] or time.time()
    elapsed = time.time() - served
    timed_out = elapsed > config.BATTLE_TIME_LIMIT + 1.0   # 1s network grace
    try:
        chosen = None if chosen is None else int(chosen)
    except (TypeError, ValueError):
        chosen = None
    correct = (not timed_out) and chosen is not None and chosen == q["answer"]

    combo = me["combo"] + 1 if correct else 0
    points = 0
    mult = 1.0
    if correct:
        mult = min(config.BATTLE_MAX_COMBO_MULT, 1 + 0.25 * (combo - 1))
        speed = max(0.0, 1 - elapsed / config.BATTLE_TIME_LIMIT)
        points = round((config.BATTLE_BASE_POINTS + config.BATTLE_SPEED_BONUS * speed) * mult)
    score = me["score"] + points
    lives = me["lives"] - (0 if correct else 1)
    next_index = q_index + 1
    finished = lives <= 0 or next_index >= len(qids)

    if not db.record_battle_answer(battle_id, player_id, q_index, chosen, correct, points, score):
        raise ArenaError("Already answered.")
    db.update_entry(
        battle_id, player_id,
        q_index=next_index, served_at=None, score=score,
        correct=me["correct"] + (1 if correct else 0),
        lives=lives, combo=combo, best_combo=max(me["best_combo"], combo),
        finished=int(finished),
        finished_at=_now() if finished else None,
    )
    settled = _maybe_settle(battle_id) if finished else None

    return {
        "correct": correct,
        "timed_out": timed_out,
        "answer": q["answer"],
        "explain": q["explain"],
        "points": points,
        "multiplier": mult,
        "combo": combo,
        "score": score,
        "lives": lives,
        "finished": finished,
        "out_of_lives": lives <= 0,
        "settled": settled,
    }


# ---- lists / lobby -------------------------------------------------------

def lobby(player_id: int) -> dict:
    invites, active, history = [], [], []
    for r in db.player_battles(player_id):
        mine = r["challenger_id"] == player_id
        row = {
            "id": r["id"],
            "rival": r["opponent"] if mine else r["challenger"],
            "mode": config.BATTLE_MODES[r["difficulty"]]["name"],
            "my_score": r["my_score"],
            "their_score": r["their_score"],
            "my_finished": bool(r["my_finished"]),
            "their_finished": bool(r["their_finished"]),
            "status": r["status"],
            "outcome": _outcome(r, player_id),
            "created": r["created"],
        }
        if r["status"] == "open" and not mine and not r["my_finished"] and r["my_index"] == 0:
            invites.append(row)
        elif r["status"] == "open":
            active.append(row)
        else:
            history.append(row)
    return {"invites": invites, "active": active, "history": history}


def pending_invites(player_id: int):
    return lobby(player_id)["invites"]


def record(player_id: int) -> dict:
    wins = losses = draws = 0
    for r in db.player_battles(player_id, limit=1000):
        o = _outcome(r, player_id)
        wins += o == "win"
        losses += o == "loss"
        draws += o == "draw"
    return {"wins": wins, "losses": losses, "draws": draws}


def daily_streak(player_id: int) -> int:
    """Consecutive days (ending today or yesterday) with a finished drive/battle."""
    days = db.activity_dates(player_id)
    today = datetime.now(timezone.utc).date()
    day = today if today.isoformat() in days else today - timedelta(days=1)
    streak = 0
    while day.isoformat() in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


# ---- internals -------------------------------------------------------------

def _battle_for(battle_id: int, player_id: int):
    b = db.get_battle(battle_id)
    if b is None or player_id not in (b["challenger_id"], b["opponent_id"]):
        raise ArenaError("Battle not found.")
    return b


def _entry_view(e, name):
    return {"name": name, "score": e["score"], "lives": e["lives"], "correct": e["correct"],
            "combo": e["combo"], "best_combo": e["best_combo"], "index": e["q_index"],
            "finished": bool(e["finished"])}


def _maybe_settle(battle_id: int):
    """If both runs are over, decide the winner and award XP once."""
    b = db.get_battle(battle_id)
    if b["status"] != "open":
        return None
    a = db.get_entry(battle_id, b["challenger_id"])
    o = db.get_entry(battle_id, b["opponent_id"])
    if not (a["finished"] and o["finished"]):
        return None
    if a["score"] == o["score"]:
        winner = None
    else:
        winner = b["challenger_id"] if a["score"] > o["score"] else b["opponent_id"]
    db.set_battle_status(battle_id, "done", winner)
    for pid in (b["challenger_id"], b["opponent_id"]):
        key = "draw" if winner is None else ("win" if winner == pid else "loss")
        db.add_xp(pid, config.BATTLE_XP[key])
    return {"winner_id": winner}


def _result_view(b, player_id):
    if b["winner_id"] is None:
        outcome = "draw"
    else:
        outcome = "win" if b["winner_id"] == player_id else "loss"
    return {"outcome": outcome, "xp": config.BATTLE_XP[outcome]}


def _outcome(r, player_id):
    if r["status"] == "declined":
        return "declined"
    if r["status"] != "done":
        return None
    if r["winner_id"] is None:
        return "draw"
    return "win" if r["winner_id"] == player_id else "loss"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
