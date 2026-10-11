"""Build a placement drive (a company's paper) and score answers."""
import json
from . import config, coderunner, db


def sections_for(company):
    """Ordered section keys for a company's paper (legacy companies: all rounds)."""
    return config.COMPANY_PAPERS.get(company["name"], config.ROUNDS)


def build_drive(company):
    """Assemble a company's paper.

    Returns a list of question dicts that are safe for the client (no answer
    index, no hidden tests), plus an internal answer key keyed by question id.
    MCQ ids are plain question ids; DSA ids are "p<problem id>".
    """
    difficulty = config.TIERS[company["tier"]]["difficulty"]
    questions = []
    answer_key = {}
    for section in sections_for(company):
        if section == "dsa":
            for row in db.company_problems(company["name"], config.DSA_PER_PAPER):
                tests = json.loads(row["tests"])
                qid = "p%d" % row["id"]
                questions.append({
                    "id": qid,
                    "kind": "dsa",
                    "round": "dsa",
                    "round_label": config.ROUND_LABELS["dsa"],
                    "title": row["title"],
                    "level": row["level"],
                    "topics": json.loads(row["topics"]),
                    "prompt": row["statement"],
                    "starter": row["starter"],
                    "func": row["func"],
                    "samples": [{"args": t["args"], "expected": t["expected"]}
                                for t in tests if t.get("sample")],
                    "hidden_count": sum(1 for t in tests if not t.get("sample")),
                })
                answer_key[qid] = {"problem_id": row["id"], "explain": row["approach"]}
            continue
        rows = db.pick_questions(section, difficulty, config.QUESTIONS_PER_ROUND,
                                 company=company["name"])
        for row in rows:
            questions.append({
                "id": row["id"],
                "kind": "mcq",
                "round": section,
                "round_label": config.ROUND_LABELS[section],
                "difficulty": row["difficulty"],
                "prompt": row["prompt"],
                "options": json.loads(row["options"]),
            })
            answer_key[str(row["id"])] = {
                "answer": row["answer"],
                "explain": row["explain"],
            }
    return questions, answer_key


def run_samples(problem_id: int, code: str) -> dict:
    """'Run' button: the player's code against the visible sample tests only."""
    p = db.get_problem(problem_id)
    tests = [t for t in json.loads(p["tests"]) if t.get("sample")]
    res = coderunner.run(code, p["func"], tests, p["compare"])
    if "error" in res:
        return res
    return {"results": [dict(r, args=t["args"], expected=t["expected"])
                        for r, t in zip(res["results"], tests)]}


def score_drive(questions, answer_key, submitted):
    """Grade a submitted paper.

    `submitted` maps question id (str) -> chosen option index, or for DSA
    problems -> the player's code. An MCQ is worth 1; a DSA problem is worth
    1 split across its tests (fraction of all tests passed).
    Returns (score, total, per-question review list). Score may be fractional.
    """
    review = []
    score = 0.0
    for q in questions:
        qid = str(q["id"])
        key = answer_key.get(qid, {})
        if q.get("kind") == "dsa":
            review.append(_grade_dsa(q, key, submitted.get(qid) or ""))
            score += review[-1]["credit"]
            continue
        correct_idx = key.get("answer")
        chosen = submitted.get(qid)
        try:
            chosen = int(chosen)
        except (TypeError, ValueError):
            chosen = None
        is_correct = chosen is not None and chosen == correct_idx
        if is_correct:
            score += 1
        review.append({
            "kind": "mcq",
            "round": q["round"],
            "round_label": q["round_label"],
            "prompt": q["prompt"],
            "options": q["options"],
            "chosen": chosen,
            "correct": correct_idx,
            "is_correct": is_correct,
            "explain": key.get("explain", ""),
        })
    return round(score, 2), len(questions), review


def _grade_dsa(q, key, code):
    p = db.get_problem(key["problem_id"])
    tests = json.loads(p["tests"])
    blank = not code.strip() or _same_code(code, p["starter"] or "")
    if blank:
        res = {"error": "No solution submitted."}
    else:
        res = coderunner.run(code, p["func"], tests, p["compare"])
    if "error" in res:
        passed, error = 0, res["error"]
    else:
        passed, error = sum(1 for r in res["results"] if r["ok"]), None
    credit = passed / len(tests) if tests else 0
    first_fail = None
    if "results" in res and not blank:
        for r, t in zip(res["results"], tests):
            if not r["ok"] and t.get("sample"):
                first_fail = {"args": t["args"], "expected": t["expected"],
                              "got": r.get("got"), "error": r.get("error")}
                break
    return {
        "kind": "dsa",
        "round": "dsa",
        "round_label": q["round_label"],
        "prompt": q["title"],
        "level": q["level"],
        "passed": passed,
        "total_tests": len(tests),
        "credit": credit,
        "is_correct": passed == len(tests),
        "error": error,
        "first_fail": first_fail,
        "code": "" if blank else code,
        "explain": key.get("explain", ""),
    }


def _same_code(a: str, b: str) -> bool:
    """Equal ignoring trailing whitespace on each line (browsers normalise newlines)."""
    norm = lambda s: "\n".join(line.rstrip() for line in s.replace("\r\n", "\n").strip().split("\n"))
    return norm(a) == norm(b)
