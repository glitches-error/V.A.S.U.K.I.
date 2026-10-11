"""Prep: generic practice across the combined question pool, and company briefs.

* overview()  -> the Prep page: every topic, combined accuracy (drives +
  practice), weakest-first, plus the full DSA library. Not tied to a company.
* practice_*  -> serve / grade one practice MCQ at a time from ALL sources
  (every company's paper + the general bank). Answers are graded server-side.
* company_brief() -> what one company's paper looks like, for its card on the
  map (the map is the company-specific view).
"""
import json

from . import config, coderunner, db

MASTERY = 0.8          # accuracy at which a topic counts as mastered
MIN_SAMPLES = 3        # answers needed before we trust an accuracy figure
PRACTICE_XP = 5        # per correct practice MCQ
PRACTICE_SOLVE_XP = 40 # first full solve of a DSA problem in practice

# Topics shown on the Prep page, in a sensible study order.
TOPICS = ["aptitude", "reasoning", "verbal", "pseudocode", "coding", "debugging",
          "python", "sql", "cs", "interview", "dsa"]


def _combined_accuracy(player_id):
    acc = {}
    for source in (db.round_accuracy(player_id), db.practice_accuracy(player_id)):
        for rnd, (c, t) in source.items():
            pc, pt = acc.get(rnd, (0, 0))
            acc[rnd] = (pc + (c or 0), pt + (t or 0))
    return acc


def _status(c, t):
    if t < MIN_SAMPLES:
        return "untested"
    a = c / t
    if a >= MASTERY:
        return "mastered"
    return "weak" if a < 0.5 else "improving"


def _companies_testing(topic):
    return [name for name, sections in config.COMPANY_PAPERS.items() if topic in sections]


def overview(player_id: int) -> dict:
    acc = _combined_accuracy(player_id)
    pools = db.topic_pool_sizes()
    topics = []
    for t in TOPICS:
        c, n = acc.get(t, (0, 0))
        topics.append({
            "key": t,
            "label": config.ROUND_LABELS[t],
            "continent": config.CONTINENTS[config.ROUND_CONTINENT[t]],
            "continent_key": config.ROUND_CONTINENT[t],
            "accuracy": round(100 * c / n) if n else None,
            "answered": n,
            "status": _status(c, n),
            "pool": pools.get(t, 0) if t != "dsa" else len(db.all_problems()),
            "companies": _companies_testing(t),
            "tips": config.ROUND_TIPS.get(t, []),
        })
    # Weakest first: weak, then improving, then untested, then mastered.
    order = {"weak": 0, "improving": 1, "untested": 2, "mastered": 3}
    focus = sorted(topics, key=lambda x: (order[x["status"]], x["accuracy"] if x["accuracy"] is not None else 50))
    tested = [x for x in topics if x["accuracy"] is not None]
    solved = db.solved_problems(player_id)
    problems = [{"id": p["id"], "title": p["title"], "level": p["level"], "company": p["company"],
                 "topics": json.loads(p["topics"]), "solved": p["id"] in solved}
                for p in db.all_problems()]
    return {
        "topics": topics,
        "focus": focus[:3],
        "overall": round(sum(x["accuracy"] for x in tested) / len(tested)) if tested else 0,
        "mastered": sum(1 for x in topics if x["status"] == "mastered"),
        "problems": problems,
        "solved": len(solved),
    }


# ---- practice MCQs -----------------------------------------------------------

def practice_next(topic: str, seen_ids) -> dict:
    if topic not in config.ROUND_LABELS or topic == "dsa":
        return {"error": "Unknown topic."}
    row = db.practice_question(topic, seen_ids)
    if row is None:
        return {"error": "No questions for this topic yet."}
    return {
        "id": row["id"],
        "topic": topic,
        "label": config.ROUND_LABELS[topic],
        "source": row["company"] or "General bank",
        "prompt": row["prompt"],
        "options": json.loads(row["options"]),
    }


def practice_answer(player_id: int, question_id: int, chosen) -> dict:
    q = db.get_question(question_id)
    if q is None:
        return {"error": "Unknown question."}
    try:
        chosen = int(chosen)
    except (TypeError, ValueError):
        chosen = None
    correct = chosen is not None and chosen == q["answer"]
    db.log_practice(player_id, q["round"], "q%d" % q["id"], int(correct), 1)
    if correct:
        db.add_xp(player_id, PRACTICE_XP)
    return {"correct": correct, "answer": q["answer"], "explain": q["explain"],
            "xp": PRACTICE_XP if correct else 0}


# ---- practice DSA --------------------------------------------------------------

def problem_view(problem_id: int):
    p = db.get_problem(problem_id)
    if p is None:
        return None
    tests = json.loads(p["tests"])
    return {
        "id": "p%d" % p["id"], "pid": p["id"], "kind": "dsa", "round": "dsa",
        "title": p["title"], "level": p["level"], "company": p["company"],
        "topics": json.loads(p["topics"]), "prompt": p["statement"], "starter": p["starter"],
        "func": p["func"],
        "samples": [{"args": t["args"], "expected": t["expected"]} for t in tests if t.get("sample")],
        "hidden_count": sum(1 for t in tests if not t.get("sample")),
        "approach": p["approach"],
    }


def judge_problem(player_id: int, problem_id: int, code: str) -> dict:
    """Practice 'Submit': run every test, log it, reward a first full solve."""
    p = db.get_problem(problem_id)
    if p is None:
        return {"error": "Unknown problem."}
    tests = json.loads(p["tests"])
    res = coderunner.run(code, p["func"], tests, p["compare"])
    if "error" in res:
        return res
    passed = sum(1 for r in res["results"] if r["ok"])
    first_solve = passed == len(tests) and problem_id not in db.solved_problems(player_id)
    db.log_practice(player_id, "dsa", "p%d" % problem_id, passed, len(tests))
    if first_solve:
        db.add_xp(player_id, PRACTICE_SOLVE_XP)
    fail = None
    for r, t in zip(res["results"], tests):
        if not r["ok"] and t.get("sample"):
            fail = {"args": t["args"], "expected": t["expected"], "got": r.get("got"), "error": r.get("error")}
            break
    return {"passed": passed, "total": len(tests), "solved": passed == len(tests),
            "xp": PRACTICE_SOLVE_XP if first_solve else 0, "first_fail": fail,
            "approach": p["approach"] if passed == len(tests) else None}


# ---- company brief (for the map) -------------------------------------------------

def company_brief(player_id: int, company) -> dict:
    name = company["name"]
    sections = config.COMPANY_PAPERS.get(name, config.ROUNDS)
    focus = config.COMPANY_FOCUS.get(name, {})
    mine = db.round_accuracy(player_id, company["id"])
    rows = []
    for s in sections:
        c, t = mine.get(s, (0, 0))
        rows.append({"label": config.ROUND_LABELS[s], "weight": focus.get(s, 1),
                     "accuracy": round(100 * c / t) if t else None})
    best = db.best_drive(player_id, company["id"])
    return {
        "pattern": config.COMPANY_PATTERN.get(name, "mcq"),
        "sections": rows,
        "problems": [{"title": p["title"], "level": p["level"]}
                     for p in db.company_problems(name, config.DSA_PER_PAPER)],
        "attempts": best["attempts"] if best else 0,
        "best_pct": round(best["best"] * 100) if best and best["best"] is not None else None,
    }
