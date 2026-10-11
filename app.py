"""V.A.S.U.K.I. — Flask web application entry point.

Run:  cd vasuki && python3 app.py   then open http://127.0.0.1:5000
"""
import json
import os
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

from vasuki import seed, db, engine, rounds, arena, prep

app = Flask(__name__)
app.secret_key = os.environ.get("VASUKI_SECRET", "vasuki-dev-secret-change-me")


@app.context_processor
def inject_lore():
    """Lore data available to every template."""
    from vasuki import config
    pid = session.get("player_id")
    return {
        "invite_count": len(arena.pending_invites(pid)) if pid and db.get_player(pid) else 0,
        "streak": arena.daily_streak(pid) if pid and db.get_player(pid) else 0,
        "continents": config.CONTINENTS,
        "round_continent": config.ROUND_CONTINENT,
        "threat_for_level": config.threat_for_level,
    }

# Bootstrap the database + question bank on startup.
seed.seed_all()


def current_player_id():
    pid = session.get("player_id")
    # A session can outlive its player (e.g. the database was reset).
    if pid and db.get_player(pid) is None:
        session.clear()
        return None
    return pid


@app.route("/")
def index():
    if current_player_id():
        return redirect(url_for("world"))
    return render_template("index.html")


@app.route("/signup", methods=["POST"])
def signup():
    name = (request.form.get("name") or "").strip()
    password = request.form.get("password") or ""
    if not name or not password:
        flash("Enter a codename and a password to sign up.")
        return redirect(url_for("index"))
    if len(password) < 4:
        flash("Password must be at least 4 characters.")
        return redirect(url_for("index"))
    player = db.create_player(name[:32], generate_password_hash(password))
    if player is None:
        flash("That codename is already taken. Try logging in instead.")
        return redirect(url_for("index"))
    session["player_id"] = player["id"]
    session.pop("drive", None)
    return redirect(url_for("world"))


@app.route("/login", methods=["POST"])
def login():
    name = (request.form.get("name") or "").strip()
    password = request.form.get("password") or ""
    player = db.get_player_by_name(name)
    if player is None or not check_password_hash(player["pass_hash"], password):
        flash("Invalid codename or password.")
        return redirect(url_for("index"))
    session["player_id"] = player["id"]
    session.pop("drive", None)
    return redirect(url_for("world"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/world")
def world():
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    companies = engine.companies_with_status(pid)
    briefs = {c["id"]: prep.company_brief(pid, db.get_company(c["id"])) for c in companies}
    return render_template(
        "world.html",
        profile=engine.profile(pid),
        companies=companies,
        briefs=briefs,
    )


@app.route("/profile")
def profile_page():
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    return render_template(
        "profile.html",
        profile=engine.profile(pid),
        drives=db.player_drives(pid),
    )


@app.route("/drive/<int:company_id>")
def start_drive(company_id):
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    company = db.get_company(company_id)
    if company is None:
        flash("Unknown company.")
        return redirect(url_for("world"))

    # Enforce the level gate.
    status = next((c for c in engine.companies_with_status(pid)
                   if c["id"] == company_id), None)
    if status and not status["unlocked"]:
        flash(f"{company['name']} is locked. Reach level "
              f"{status['unlock_level']} to unlock it.")
        return redirect(url_for("world"))

    questions, answer_key = rounds.build_drive(company)
    db.save_active_drive(pid, company_id, json.dumps(
        {"questions": questions, "answer_key": answer_key}))
    session.pop("drive", None)       # legacy cookie-stored drives
    from vasuki import config
    return render_template(
        "drive.html",
        company=company,
        tier=config.TIERS[company["tier"]],
        questions=questions,
        round_labels=config.ROUND_LABELS,
        rounds_order=rounds.sections_for(company),
        pattern=config.COMPANY_PATTERN.get(company["name"], "mcq"),
    )


@app.route("/api/drive/<int:company_id>/run", methods=["POST"])
def api_run_code(company_id):
    """Run the player's code for one DSA problem against its sample tests."""
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "not logged in"}), 401
    active = db.get_active_drive(pid)
    data = request.get_json(silent=True) or {}
    if not active or active["company_id"] != company_id:
        return jsonify({"error": "This drive has expired. Restart it from the map."}), 409
    key = json.loads(active["data"])["answer_key"].get(str(data.get("qid")))
    if not key or "problem_id" not in key:
        return jsonify({"error": "Unknown problem."}), 404
    return jsonify(rounds.run_samples(key["problem_id"], str(data.get("code") or "")))


@app.route("/drive/<int:company_id>/submit", methods=["POST"])
def submit_drive(company_id):
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    active = db.get_active_drive(pid)
    drive = json.loads(active["data"]) if active else None
    if not drive or active["company_id"] != company_id:
        flash("Your drive session expired. Start again.")
        return redirect(url_for("world"))

    submitted = {k[2:]: v for k, v in request.form.items() if k.startswith("q_")}
    submitted.update({k[5:]: v for k, v in request.form.items() if k.startswith("code_")})
    company = db.get_company(company_id)
    score, total, review = rounds.score_drive(
        drive["questions"], drive["answer_key"], submitted
    )
    result = engine.award_drive(pid, company, score, total)
    per_round = {}
    for r in review:
        c, t = per_round.get(r["round"], (0, 0))
        if r["kind"] == "dsa":      # DSA accuracy is measured in tests passed
            per_round[r["round"]] = (c + r["passed"], t + r["total_tests"])
        else:
            per_round[r["round"]] = (c + int(r["is_correct"]), t + 1)
    db.record_drive_rounds(pid, company_id, per_round)
    db.clear_active_drive(pid)
    return render_template(
        "result.html",
        company=company,
        result=result,
        review=review,
        profile=engine.profile(pid),
    )


# ---- Prep: generic practice across the combined question pool ---------------

@app.route("/prep")
def prep_page():
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    return render_template("prep.html", profile=engine.profile(pid), prep=prep.overview(pid))


@app.route("/prep/<int:company_id>")
def prep_company_redirect(company_id):
    # Company-specific info now lives on the map's level card.
    return redirect(url_for("world"))


@app.route("/prep/practice/<topic>")
def practice_page(topic):
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    from vasuki import config
    if topic not in prep.TOPICS or topic == "dsa":
        return redirect(url_for("prep_page"))
    ov = prep.overview(pid)
    info = next(t for t in ov["topics"] if t["key"] == topic)
    return render_template("practice.html", profile=engine.profile(pid), topic=info)


@app.route("/prep/problem/<int:problem_id>")
def practice_problem_page(problem_id):
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    p = prep.problem_view(problem_id)
    if p is None:
        return redirect(url_for("prep_page"))
    return render_template("practice_problem.html", profile=engine.profile(pid), q=p,
                           solved=problem_id in db.solved_problems(pid))


@app.route("/api/practice/next", methods=["POST"])
def api_practice_next():
    if not current_player_id():
        return jsonify({"error": "not logged in"}), 401
    data = request.get_json(silent=True) or {}
    seen = [int(x) for x in (data.get("seen") or []) if str(x).isdigit()][-200:]
    out = prep.practice_next(str(data.get("topic")), seen)
    return jsonify(out), (400 if "error" in out else 200)


@app.route("/api/practice/answer", methods=["POST"])
def api_practice_answer():
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "not logged in"}), 401
    data = request.get_json(silent=True) or {}
    try:
        qid = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"error": "bad id"}), 400
    out = prep.practice_answer(pid, qid, data.get("chosen"))
    return jsonify(out), (404 if "error" in out else 200)


@app.route("/api/practice/problem/<int:problem_id>/run", methods=["POST"])
def api_practice_run(problem_id):
    if not current_player_id():
        return jsonify({"error": "not logged in"}), 401
    if db.get_problem(problem_id) is None:
        return jsonify({"error": "Unknown problem."}), 404
    data = request.get_json(silent=True) or {}
    return jsonify(rounds.run_samples(problem_id, str(data.get("code") or "")))


@app.route("/api/practice/problem/<int:problem_id>/submit", methods=["POST"])
def api_practice_submit(problem_id):
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "not logged in"}), 401
    data = request.get_json(silent=True) or {}
    out = prep.judge_problem(pid, problem_id, str(data.get("code") or ""))
    return jsonify(out)


# ---- Arena: head-to-head battles ------------------------------------------

@app.route("/arena")
def arena_page():
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    from vasuki import config
    return render_template(
        "arena.html",
        profile=engine.profile(pid),
        lobby=arena.lobby(pid),
        record=arena.record(pid),
        leaderboard=db.arena_leaderboard(),
        modes=config.BATTLE_MODES,
        battle_cfg={"questions": config.BATTLE_QUESTIONS, "time": config.BATTLE_TIME_LIMIT,
                    "lives": config.BATTLE_LIVES, "xp": config.BATTLE_XP},
    )


@app.route("/arena/challenge", methods=["POST"])
def arena_challenge():
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    try:
        mode = int(request.form.get("mode", 2))
    except ValueError:
        mode = 2
    try:
        bid = arena.challenge(pid, request.form.get("codename", ""), mode)
    except arena.ArenaError as e:
        flash(str(e))
        return redirect(url_for("arena_page"))
    return redirect(url_for("battle_page", battle_id=bid))


@app.route("/arena/<int:battle_id>")
def battle_page(battle_id):
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    try:
        st = arena.state(battle_id, pid)
    except arena.ArenaError as e:
        flash(str(e))
        return redirect(url_for("arena_page"))
    return render_template("battle.html", battle=st)


@app.route("/arena/<int:battle_id>/decline", methods=["POST"])
def battle_decline(battle_id):
    pid = current_player_id()
    if not pid:
        return redirect(url_for("index"))
    try:
        arena.decline(battle_id, pid)
        flash("Challenge declined.")
    except arena.ArenaError as e:
        flash(str(e))
    return redirect(url_for("arena_page"))


@app.route("/api/battle/<int:battle_id>")
def api_battle_state(battle_id):
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "not logged in"}), 401
    try:
        return jsonify(arena.state(battle_id, pid))
    except arena.ArenaError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/battle/<int:battle_id>/answer", methods=["POST"])
def api_battle_answer(battle_id):
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "not logged in"}), 401
    data = request.get_json(silent=True) or {}
    try:
        result = arena.answer(battle_id, pid, int(data.get("index", -1)), data.get("chosen"))
    except arena.ArenaError as e:
        return jsonify({"error": str(e)}), 409
    result["state"] = arena.state(battle_id, pid)
    return jsonify(result)


@app.route("/api/invites")
def api_invites():
    pid = current_player_id()
    if not pid:
        return jsonify({"invites": []})
    return jsonify({"invites": arena.pending_invites(pid)})


@app.route("/api/profile")
def api_profile():
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "no player"}), 401
    return jsonify(engine.profile(pid))


if __name__ == "__main__":
    # The one-click launcher sets VASUKI_LAUNCHER=1 so we run without the debug
    # auto-reloader (which would otherwise restart the process and throw off the
    # browser-open timing). Plain `python app.py` still runs in debug mode.
    launched = os.environ.get("VASUKI_LAUNCHER") == "1"
    app.run(port=5000, debug=not launched, use_reloader=not launched)
