"""Company placement papers: per-company MCQs and DSA coding problems.

Content lives in sibling modules:
  mcq_service.py  QUESTIONS  -> MCQ papers for service companies
  mcq_product.py  QUESTIONS  -> MCQ sections for product companies
  dsa.py          PROBLEMS   -> coding problems with hidden tests

`sync()` loads them into the database. It is idempotent and re-runs cheaply:
company questions are replaced only when the content changes (tracked by a
fingerprint), so editing a paper file and restarting the app is enough.
"""
import hashlib
import json

from .. import db

try:
    from .mcq_service import QUESTIONS as _SERVICE
except ImportError:          # content not written yet
    _SERVICE = []
try:
    from .mcq_product import QUESTIONS as _PRODUCT
except ImportError:
    _PRODUCT = []
try:
    from .dsa import PROBLEMS as _DSA
except ImportError:
    _DSA = []

# Papers are graded by difficulty tier of the company they belong to.
_TIER_DIFFICULTY = {1: 1, 2: 2, 3: 2, 4: 3}


def _fingerprint():
    blob = json.dumps([_SERVICE, _PRODUCT, _DSA], sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def sync():
    conn = db.get_conn()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        row = conn.execute("SELECT value FROM meta WHERE key = 'papers_fp'").fetchone()
        fp = _fingerprint()
        if row and row["value"] == fp:
            return
        tiers = {r["name"]: r["tier"] for r in conn.execute("SELECT name, tier FROM companies")}

        conn.execute("DELETE FROM questions WHERE company IS NOT NULL")
        conn.executemany(
            "INSERT INTO questions(round, difficulty, prompt, options, answer, explain, company) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(section, _TIER_DIFFICULTY.get(tiers.get(company, 1), 1), prompt,
              json.dumps(options), answer, explain, company)
             for company, section, prompt, options, answer, explain in _SERVICE + _PRODUCT],
        )

        conn.execute("DELETE FROM problems")
        conn.executemany(
            "INSERT INTO problems(company, title, level, topics, statement, func, starter, "
            "compare, tests, solution, approach) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(p["company"], p["title"], p["level"], json.dumps(p["topics"]), p["statement"],
              p["func"], p["starter"], p.get("compare", "exact"), json.dumps(p["tests"]),
              p["solution"], p.get("approach", ""))
             for p in _DSA],
        )
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('papers_fp', ?)", (fp,))
        conn.commit()
    finally:
        conn.close()
