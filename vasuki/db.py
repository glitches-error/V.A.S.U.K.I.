"""SQLite layer: connection, schema, and typed query helpers."""
import sqlite3
from . import config


def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT UNIQUE NOT NULL,
    pass_hash  TEXT NOT NULL DEFAULT '',
    xp         INTEGER NOT NULL DEFAULT 0,
    created    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS companies (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT UNIQUE NOT NULL,
    tier      INTEGER NOT NULL,
    blurb     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    round      TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    prompt     TEXT NOT NULL,
    options    TEXT NOT NULL,   -- JSON array of choices
    answer     INTEGER NOT NULL,-- index into options
    explain    TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS achievements (
    code   TEXT PRIMARY KEY,
    title  TEXT NOT NULL,
    descr  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS player_achievements (
    player_id INTEGER NOT NULL REFERENCES players(id),
    code      TEXT NOT NULL REFERENCES achievements(code),
    earned    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (player_id, code)
);

CREATE TABLE IF NOT EXISTS drives (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id  INTEGER NOT NULL REFERENCES players(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    score      INTEGER NOT NULL,
    total      INTEGER NOT NULL,
    passed     INTEGER NOT NULL,
    xp_gained  INTEGER NOT NULL,
    played     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- DSA coding problems (company papers). Tests/solution are server-only.
CREATE TABLE IF NOT EXISTS problems (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    company    TEXT NOT NULL,
    title      TEXT NOT NULL,
    level      TEXT NOT NULL,
    topics     TEXT NOT NULL,      -- JSON array
    statement  TEXT NOT NULL,
    func       TEXT NOT NULL,
    starter    TEXT NOT NULL,
    compare    TEXT NOT NULL DEFAULT 'exact',
    tests      TEXT NOT NULL,      -- JSON array of {args, expected, sample}
    solution   TEXT NOT NULL,
    approach   TEXT NOT NULL DEFAULT '',
    UNIQUE (company, title)
);

-- In-progress drives, kept server-side (the session cookie is too small to
-- hold a paper with coding problems). Holds the answer key, so never send it.
CREATE TABLE IF NOT EXISTS active_drives (
    player_id  INTEGER PRIMARY KEY REFERENCES players(id),
    company_id INTEGER NOT NULL,
    data       TEXT NOT NULL,          -- JSON {questions, answer_key}
    created    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Prep practice: every answered practice MCQ / judged DSA run (combined pool).
CREATE TABLE IF NOT EXISTS practice_log (
    player_id  INTEGER NOT NULL REFERENCES players(id),
    round      TEXT NOT NULL,
    item       TEXT NOT NULL,          -- "q<id>" or "p<id>"
    correct    INTEGER NOT NULL,       -- MCQ: 0/1; DSA: tests passed
    total      INTEGER NOT NULL,       -- MCQ: 1;   DSA: tests run
    played     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Per-round results of each drive, used to build prep plans.
CREATE TABLE IF NOT EXISTS drive_rounds (
    player_id  INTEGER NOT NULL REFERENCES players(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    round      TEXT NOT NULL,
    correct    INTEGER NOT NULL,
    total      INTEGER NOT NULL,
    played     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Arena: head-to-head battles between two players on the same questions.
CREATE TABLE IF NOT EXISTS battles (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    challenger_id  INTEGER NOT NULL REFERENCES players(id),
    opponent_id    INTEGER NOT NULL REFERENCES players(id),
    status         TEXT NOT NULL DEFAULT 'open',   -- open | done | declined
    difficulty     INTEGER NOT NULL,
    question_ids   TEXT NOT NULL,                  -- JSON array
    winner_id      INTEGER,                        -- NULL = draw / undecided
    created        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per player per battle: their running progress.
CREATE TABLE IF NOT EXISTS battle_entries (
    battle_id    INTEGER NOT NULL REFERENCES battles(id),
    player_id    INTEGER NOT NULL REFERENCES players(id),
    q_index      INTEGER NOT NULL DEFAULT 0,       -- next question to answer
    served_at    REAL,                             -- epoch secs current q was shown
    score        INTEGER NOT NULL DEFAULT 0,
    correct      INTEGER NOT NULL DEFAULT 0,
    lives        INTEGER NOT NULL DEFAULT 3,
    combo        INTEGER NOT NULL DEFAULT 0,
    best_combo   INTEGER NOT NULL DEFAULT 0,
    finished     INTEGER NOT NULL DEFAULT 0,
    finished_at  TEXT,
    PRIMARY KEY (battle_id, player_id)
);

CREATE TABLE IF NOT EXISTS battle_answers (
    battle_id  INTEGER NOT NULL,
    player_id  INTEGER NOT NULL,
    q_index    INTEGER NOT NULL,
    chosen     INTEGER,
    correct    INTEGER NOT NULL,
    points     INTEGER NOT NULL,
    score_after INTEGER NOT NULL,
    PRIMARY KEY (battle_id, player_id, q_index)
);
"""


def init_schema():
    conn = get_conn()
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    conn.close()


def _migrate(conn):
    """Apply lightweight in-place migrations for older databases."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(players)").fetchall()}
    if "pass_hash" not in cols:
        conn.execute("ALTER TABLE players ADD COLUMN pass_hash TEXT NOT NULL DEFAULT ''")
    qcols = {r["name"] for r in conn.execute("PRAGMA table_info(questions)").fetchall()}
    if "company" not in qcols:
        # NULL = general bank (Arena); otherwise the company paper it belongs to.
        conn.execute("ALTER TABLE questions ADD COLUMN company TEXT")
    ccols = {r["name"] for r in conn.execute("PRAGMA table_info(companies)").fetchall()}
    if "active" not in ccols:
        # Retired companies stay for drive history but leave the map.
        conn.execute("ALTER TABLE companies ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    if "pattern" not in ccols:
        conn.execute("ALTER TABLE companies ADD COLUMN pattern TEXT NOT NULL DEFAULT 'mcq'")
    if "position" not in ccols:
        conn.execute("ALTER TABLE companies ADD COLUMN position INTEGER NOT NULL DEFAULT 0")


def is_seeded() -> bool:
    conn = get_conn()
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM questions").fetchone()
        return row["c"] > 0
    finally:
        conn.close()


# ---- players -------------------------------------------------------------

def get_player_by_name(name: str):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM players WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
    finally:
        conn.close()


def create_player(name: str, pass_hash: str):
    """Create a new player. Returns the row, or None if the name is taken."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO players(name, pass_hash) VALUES (?, ?)",
            (name, pass_hash),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        return conn.execute(
            "SELECT * FROM players WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
    finally:
        conn.close()


def get_player(player_id: int):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    finally:
        conn.close()


def add_xp(player_id: int, amount: int):
    conn = get_conn()
    try:
        conn.execute("UPDATE players SET xp = xp + ? WHERE id = ?", (amount, player_id))
        conn.commit()
    finally:
        conn.close()


# ---- companies -----------------------------------------------------------

def list_companies():
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM companies WHERE active = 1 ORDER BY position, tier, name"
        ).fetchall()
    finally:
        conn.close()


def get_company(company_id: int):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    finally:
        conn.close()


# ---- questions -----------------------------------------------------------

def pick_questions(round_name: str, difficulty: int, limit: int, company=None):
    """Pick up to `limit` random questions for a round.

    With `company`, draw from that company's own paper first and top up from
    the general bank only if the paper is short. Without it, use the general
    bank at (or below) `difficulty`.
    """
    conn = get_conn()
    try:
        rows = []
        if company:
            rows = conn.execute(
                "SELECT * FROM questions WHERE company = ? AND round = ? "
                "ORDER BY RANDOM() LIMIT ?",
                (company, round_name, limit),
            ).fetchall()
        if len(rows) < limit:
            have = [r["id"] for r in rows] or [-1]
            rows += conn.execute(
                "SELECT * FROM questions WHERE company IS NULL AND round = ? AND difficulty <= ? "
                f"AND id NOT IN ({','.join('?' * len(have))}) ORDER BY RANDOM() LIMIT ?",
                (round_name, difficulty, *have, limit - len(rows)),
            ).fetchall()
        return rows
    finally:
        conn.close()


def company_problems(company: str, limit: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM problems WHERE company = ? ORDER BY id LIMIT ?", (company, limit)
        ).fetchall()
    finally:
        conn.close()


def get_problem(problem_id: int):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    finally:
        conn.close()


def get_question(question_id: int):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    finally:
        conn.close()


# ---- achievements --------------------------------------------------------

def list_achievements():
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM achievements ORDER BY code").fetchall()
    finally:
        conn.close()


def player_achievement_codes(player_id: int):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT code FROM player_achievements WHERE player_id = ?", (player_id,)
        ).fetchall()
        return {r["code"] for r in rows}
    finally:
        conn.close()


def grant_achievement(player_id: int, code: str) -> bool:
    """Return True if newly granted, False if already had it."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO player_achievements(player_id, code) VALUES (?, ?)",
            (player_id, code),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---- drives --------------------------------------------------------------

def record_drive(player_id, company_id, score, total, passed, xp_gained):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO drives(player_id, company_id, score, total, passed, xp_gained) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (player_id, company_id, score, total, int(passed), xp_gained),
        )
        conn.commit()
    finally:
        conn.close()


def player_drives(player_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT d.*, c.name AS company FROM drives d "
            "JOIN companies c ON c.id = d.company_id "
            "WHERE d.player_id = ? ORDER BY d.played DESC",
            (player_id,),
        ).fetchall()
    finally:
        conn.close()


def player_passed_company(player_id: int, company_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM drives WHERE player_id = ? AND company_id = ? AND passed = 1",
            (player_id, company_id),
        ).fetchone()
        return row["c"] > 0
    finally:
        conn.close()


# ---- arena / battles -----------------------------------------------------

def pick_battle_questions(difficulty: int, limit: int):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id FROM questions WHERE difficulty <= ? AND company IS NULL "
            "ORDER BY RANDOM() LIMIT ?",
            (difficulty, limit),
        ).fetchall()
        return [r["id"] for r in rows]
    finally:
        conn.close()


def create_battle(challenger_id, opponent_id, difficulty, question_ids_json):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO battles(challenger_id, opponent_id, difficulty, question_ids) "
            "VALUES (?, ?, ?, ?)",
            (challenger_id, opponent_id, difficulty, question_ids_json),
        )
        bid = cur.lastrowid
        conn.executemany(
            "INSERT INTO battle_entries(battle_id, player_id) VALUES (?, ?)",
            [(bid, challenger_id), (bid, opponent_id)],
        )
        conn.commit()
        return bid
    finally:
        conn.close()


def get_battle(battle_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT b.*, pc.name AS challenger, po.name AS opponent FROM battles b "
            "JOIN players pc ON pc.id = b.challenger_id "
            "JOIN players po ON po.id = b.opponent_id WHERE b.id = ?",
            (battle_id,),
        ).fetchone()
    finally:
        conn.close()


def get_entry(battle_id: int, player_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM battle_entries WHERE battle_id = ? AND player_id = ?",
            (battle_id, player_id),
        ).fetchone()
    finally:
        conn.close()


def update_entry(battle_id: int, player_id: int, **fields):
    cols = ", ".join(f"{k} = ?" for k in fields)
    conn = get_conn()
    try:
        conn.execute(
            f"UPDATE battle_entries SET {cols} WHERE battle_id = ? AND player_id = ?",
            (*fields.values(), battle_id, player_id),
        )
        conn.commit()
    finally:
        conn.close()


def record_battle_answer(battle_id, player_id, q_index, chosen, correct, points, score_after):
    """Returns False if this question was already answered (no double-submit)."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO battle_answers"
            "(battle_id, player_id, q_index, chosen, correct, points, score_after) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (battle_id, player_id, q_index, chosen, int(correct), points, score_after),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def battle_answers(battle_id: int, player_id: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM battle_answers WHERE battle_id = ? AND player_id = ? ORDER BY q_index",
            (battle_id, player_id),
        ).fetchall()
    finally:
        conn.close()


def set_battle_status(battle_id: int, status: str, winner_id=None):
    conn = get_conn()
    try:
        conn.execute("UPDATE battles SET status = ?, winner_id = ? WHERE id = ?",
                     (status, winner_id, battle_id))
        conn.commit()
    finally:
        conn.close()


def player_battles(player_id: int, limit: int = 40):
    """Battles involving a player, newest first, with both players' progress."""
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT b.*, pc.name AS challenger, po.name AS opponent, "
            "  me.finished AS my_finished, me.score AS my_score, me.q_index AS my_index, "
            "  them.finished AS their_finished, them.score AS their_score "
            "FROM battles b "
            "JOIN players pc ON pc.id = b.challenger_id "
            "JOIN players po ON po.id = b.opponent_id "
            "JOIN battle_entries me ON me.battle_id = b.id AND me.player_id = ? "
            "JOIN battle_entries them ON them.battle_id = b.id AND them.player_id != ? "
            "ORDER BY b.id DESC LIMIT ?",
            (player_id, player_id, limit),
        ).fetchall()
    finally:
        conn.close()


def arena_leaderboard(limit: int = 10):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT p.name, p.xp, "
            "  SUM(CASE WHEN b.winner_id = p.id THEN 1 ELSE 0 END) AS wins, "
            "  COUNT(b.id) AS played "
            "FROM players p JOIN battle_entries e ON e.player_id = p.id "
            "JOIN battles b ON b.id = e.battle_id AND b.status = 'done' "
            "GROUP BY p.id ORDER BY wins DESC, p.xp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def activity_dates(player_id: int):
    """Distinct UTC dates (YYYY-MM-DD) on which a player finished a drive or battle."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT date(played) AS d FROM drives WHERE player_id = ? "
            "UNION SELECT date(finished_at) FROM battle_entries "
            "WHERE player_id = ? AND finished = 1 AND finished_at IS NOT NULL",
            (player_id, player_id),
        ).fetchall()
        return {r["d"] for r in rows if r["d"]}
    finally:
        conn.close()


# ---- prep plans ------------------------------------------------------------

def record_drive_rounds(player_id, company_id, per_round):
    """per_round: {round: (correct, total)}"""
    conn = get_conn()
    try:
        conn.executemany(
            "INSERT INTO drive_rounds(player_id, company_id, round, correct, total) VALUES (?, ?, ?, ?, ?)",
            [(player_id, company_id, r, c, t) for r, (c, t) in per_round.items()],
        )
        conn.commit()
    finally:
        conn.close()


def round_accuracy(player_id, company_id=None):
    """{round: (correct, total)} across the player's drives (optionally one company)."""
    conn = get_conn()
    try:
        sql = ("SELECT round, SUM(correct) AS c, SUM(total) AS t FROM drive_rounds "
               "WHERE player_id = ?")
        args = [player_id]
        if company_id is not None:
            sql += " AND company_id = ?"
            args.append(company_id)
        rows = conn.execute(sql + " GROUP BY round", args).fetchall()
        return {r["round"]: (r["c"], r["t"]) for r in rows}
    finally:
        conn.close()


def best_drive(player_id, company_id):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT MAX(CAST(score AS REAL) / total) AS best, COUNT(*) AS attempts "
            "FROM drives WHERE player_id = ? AND company_id = ?",
            (player_id, company_id),
        ).fetchone()
    finally:
        conn.close()


# ---- in-progress drives ----------------------------------------------------

def save_active_drive(player_id, company_id, data_json):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO active_drives(player_id, company_id, data) VALUES (?, ?, ?)",
            (player_id, company_id, data_json),
        )
        conn.commit()
    finally:
        conn.close()


def get_active_drive(player_id):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM active_drives WHERE player_id = ?", (player_id,)).fetchone()
    finally:
        conn.close()


def clear_active_drive(player_id):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM active_drives WHERE player_id = ?", (player_id,))
        conn.commit()
    finally:
        conn.close()


# ---- prep practice (combined pool) -------------------------------------------

def practice_question(round_name: str, exclude_ids):
    """One random MCQ for a topic from ALL sources (company papers + general bank)."""
    conn = get_conn()
    try:
        ex = list(exclude_ids) or [-1]
        row = conn.execute(
            f"SELECT * FROM questions WHERE round = ? AND id NOT IN ({','.join('?' * len(ex))}) "
            "ORDER BY RANDOM() LIMIT 1",
            (round_name, *ex),
        ).fetchone()
        if row is None and exclude_ids:          # pool exhausted: start over
            row = conn.execute(
                "SELECT * FROM questions WHERE round = ? ORDER BY RANDOM() LIMIT 1",
                (round_name,)).fetchone()
        return row
    finally:
        conn.close()


def topic_pool_sizes():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT round, COUNT(*) AS n FROM questions GROUP BY round").fetchall()
        return {r["round"]: r["n"] for r in rows}
    finally:
        conn.close()


def all_problems():
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT id, company, title, level, topics FROM problems "
            "ORDER BY CASE level WHEN 'Easy' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, title"
        ).fetchall()
    finally:
        conn.close()


def log_practice(player_id, round_name, item, correct, total):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO practice_log(player_id, round, item, correct, total) VALUES (?, ?, ?, ?, ?)",
            (player_id, round_name, item, int(correct), int(total)),
        )
        conn.commit()
    finally:
        conn.close()


def practice_accuracy(player_id):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT round, SUM(correct) AS c, SUM(total) AS t FROM practice_log "
            "WHERE player_id = ? GROUP BY round", (player_id,)).fetchall()
        return {r["round"]: (r["c"], r["t"]) for r in rows}
    finally:
        conn.close()


def solved_problems(player_id):
    """Problem ids the player has fully solved in practice."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT item FROM practice_log WHERE player_id = ? AND round = 'dsa' "
            "AND correct = total AND total > 0", (player_id,)).fetchall()
        return {int(r["item"][1:]) for r in rows}
    finally:
        conn.close()
