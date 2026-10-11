"""Seed the database with companies, achievements, and the question bank."""
import json
from . import config, db, papers

# Companies live in config.COMPANIES (with their paper patterns).

ACHIEVEMENTS = [
    ("first_steps",  "First Contact",     "Complete your first trial inside V.A.S.U.K.I.'s world."),
    ("perfect_round","Unpredictable",     "Score 100% on a drive. The AI didn't see it coming."),
    ("giant_slayer", "Human Protocol",    "Breach the Core Citadel (pass a Big Tech drive)."),
    ("polyglot",     "Citadel Breaker",   "Pass drives at 3 different Corporate Citadels."),
    ("grinder",      "Persistent Signal", "Attempt 5 drives. Humans don't give up."),
    ("level_5",      "System Threat",     "Reach level 5. V.A.S.U.K.I. now considers you a threat."),
]


def _q(round_name, difficulty, prompt, options, answer, explain=""):
    return (round_name, difficulty, prompt, json.dumps(options), answer, explain)


def seed_all():
    """Idempotent: seeds the general bank once, then syncs companies + papers."""
    db.init_schema()
    if not db.is_seeded():
        conn = db.get_conn()
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO achievements(code, title, descr) VALUES (?, ?, ?)",
                ACHIEVEMENTS,
            )
            conn.executemany(
                "INSERT INTO questions(round, difficulty, prompt, options, answer, explain) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                QUESTIONS,
            )
            conn.commit()
        finally:
            conn.close()
    _sync_flavour_text()
    _sync_companies()
    papers.sync()


def _sync_flavour_text():
    """Refresh achievement text on existing databases (progress untouched)."""
    conn = db.get_conn()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO achievements(code, title, descr) VALUES (?, ?, ?)",
            ACHIEVEMENTS,
        )
        conn.executemany("UPDATE achievements SET title = ?, descr = ? WHERE code = ?",
                         [(title, descr, code) for code, title, descr in ACHIEVEMENTS])
        conn.commit()
    finally:
        conn.close()


def _sync_companies():
    """Make the companies table match config.COMPANIES.

    Companies not in the list are retired (active = 0): they leave the map but
    keep their rows so old drive history still resolves.
    """
    conn = db.get_conn()
    try:
        names = []
        for pos, (name, tier, pattern, _sections, blurb, _focus) in enumerate(config.COMPANIES):
            names.append(name)
            conn.execute(
                "INSERT INTO companies(name, tier, blurb, pattern, position, active) "
                "VALUES (?, ?, ?, ?, ?, 1) "
                "ON CONFLICT(name) DO UPDATE SET tier = excluded.tier, blurb = excluded.blurb, "
                "pattern = excluded.pattern, position = excluded.position, active = 1",
                (name, tier, blurb, pattern, pos),
            )
        conn.execute(
            f"UPDATE companies SET active = 0 WHERE name NOT IN ({','.join('?' * len(names))})",
            names,
        )
        conn.commit()
    finally:
        conn.close()


# The question bank is assembled below. Each entry: round, difficulty (1-3),
# prompt, list of options, index of correct option, explanation.
QUESTIONS = [
    # ---- APTITUDE -------------------------------------------------------
    _q("aptitude", 1, "What is 15% of 200?",
       ["20", "30", "25", "35"], 1, "15% of 200 = 0.15 x 200 = 30."),
    _q("aptitude", 1, "A train travels 60 km in 45 minutes. Its speed in km/h is?",
       ["60", "75", "80", "90"], 2, "60 km in 0.75 h = 80 km/h."),
    _q("aptitude", 1, "Next in the series: 2, 4, 8, 16, ?",
       ["24", "30", "32", "20"], 2, "Each term doubles: 16 x 2 = 32."),
    _q("aptitude", 1, "If 5 pens cost 75, what do 8 pens cost?",
       ["100", "110", "120", "125"], 2, "One pen = 15, so 8 x 15 = 120."),
    _q("aptitude", 2, "The average of 10, 20, 30, 40, 50 is?",
       ["25", "30", "35", "40"], 1, "Sum 150 / 5 = 30."),
    _q("aptitude", 2, "A sum doubles in 5 years at simple interest. The rate is?",
       ["10%", "15%", "20%", "25%"], 2, "100% growth over 5 yrs = 20%/yr."),
    _q("aptitude", 2, "Odd one out: 3, 5, 11, 14, 17, 21",
       ["11", "14", "17", "21"], 1, "14 is even; the rest are odd."),
    _q("aptitude", 3, "In how many ways can the letters of 'DATA' be arranged?",
       ["24", "12", "6", "4"], 1, "4!/2! = 12 (A repeats twice)."),
    _q("aptitude", 3, "Probability of getting a sum of 7 with two dice?",
       ["1/6", "1/9", "1/12", "5/36"], 0, "6 favorable / 36 = 1/6."),

    # ---- CODING (logic / output prediction) ------------------------------
    _q("coding", 1, "What does this print? for i in range(3): print(i, end='')",
       ["123", "012", "0 1 2", "111"], 1, "range(3) yields 0,1,2 with no space."),
    _q("coding", 1, "Value of len('vasuki')?",
       ["5", "6", "7", "0"], 1, "'vasuki' has 6 characters."),
    _q("coding", 1, "Result of 7 // 2 in Python?",
       ["3.5", "4", "3", "2"], 2, "// is floor division: 3."),
    _q("coding", 2, "Output of: print(sorted([3,1,2], reverse=True))",
       ["[1, 2, 3]", "[3, 2, 1]", "[2, 1, 3]", "[3, 1, 2]"], 1,
       "Sorted descending."),
    _q("coding", 2, "What is 2 ** 3 ** 2?",
       ["64", "512", "256", "81"], 1, "** is right-associative: 2**(3**2)=2**9=512."),
    _q("coding", 2, "Which loop runs at least once regardless of condition?",
       ["for", "while", "Python has no such loop", "do-while"], 2,
       "Python has no do-while; for/while may run zero times."),
    _q("coding", 3, "Time complexity of binary search on a sorted array?",
       ["O(n)", "O(log n)", "O(n log n)", "O(1)"], 1,
       "It halves the search space each step."),
    _q("coding", 3, "A stack follows which order?",
       ["FIFO", "LIFO", "Random", "Sorted"], 1, "Last In, First Out."),

    # ---- DEBUGGING (find the bug / fix) ----------------------------------
    _q("debugging", 1, "Bug: for i in range(1,5) print(i)  \u2014 what's missing?",
       ["A colon ':'", "Parentheses", "Nothing", "A semicolon"], 0,
       "Python for-statements need a ':' before the block."),
    _q("debugging", 1, "x = '5' + 5 raises what?",
       ["TypeError", "ValueError", "5 5", "10"], 0,
       "Cannot concatenate str and int."),
    _q("debugging", 1, "To fix a NameError for an undefined 'total', you should:",
       ["Import it", "Define/initialize it first", "Use global", "Restart"], 1,
       "Assign the variable before using it."),
    _q("debugging", 2, "Why does list.append(1)(2) fail?",
       ["append returns None", "Too many args", "1 is invalid", "It works"], 0,
       "append returns None, so calling (2) on None fails."),
    _q("debugging", 2, "Loop 'while x < 10:' never ends. Likely cause?",
       ["x is a string", "x is never incremented", "10 is too big", "Missing colon"], 1,
       "Without changing x, the condition stays true forever."),
    _q("debugging", 2, "IndentationError usually means:",
       ["Wrong file name", "Inconsistent spaces/tabs", "Missing import", "Syntax ok"], 1,
       "Mixed or wrong indentation breaks Python blocks."),
    _q("debugging", 3, "d = {}; d['a'] += 1 raises what?",
       ["KeyError", "TypeError", "IndexError", "Nothing"], 0,
       "'a' doesn't exist yet; use d.get('a',0)+1 or defaultdict."),
    _q("debugging", 3, "Mutable default arg 'def f(x, acc=[])' bug is:",
       ["acc is shared across calls", "acc is None", "x is required", "No bug"], 0,
       "Default list is created once and reused \u2014 classic gotcha."),

    # ---- PYTHON (language knowledge) ------------------------------------
    _q("python", 1, "Which creates a tuple?",
       ["[1, 2]", "(1, 2)", "{1, 2}", "{1: 2}"], 1, "Parentheses make a tuple."),
    _q("python", 1, "Keyword to define a function?",
       ["func", "def", "function", "lambda"], 1, "'def' defines a function."),
    _q("python", 1, "type(3.0) returns?",
       ["<class 'int'>", "<class 'float'>", "<class 'str'>", "number"], 1,
       "3.0 is a float."),
    _q("python", 2, "list comprehension for squares 0..4?",
       ["[x*2 for x in range(5)]", "[x**2 for x in range(5)]",
        "[x^2 for x in range(5)]", "{x**2 for x in range(5)}"], 1,
       "** is power; [] makes a list."),
    _q("python", 2, "What does dict.get('k', 0) do if 'k' missing?",
       ["Raises KeyError", "Returns 0", "Returns None", "Adds 'k'"], 1,
       "Returns the default 0."),
    _q("python", 2, "'*args' in a signature captures:",
       ["Keyword args", "Positional args as tuple", "One arg", "Nothing"], 1,
       "Extra positional args become a tuple."),
    _q("python", 3, "A generator is created with which keyword?",
       ["return", "yield", "async", "gen"], 1, "yield produces a generator."),
    _q("python", 3, "What is the output of bool([])?",
       ["True", "False", "None", "Error"], 1, "Empty containers are falsy."),

    # ---- SQL ------------------------------------------------------------
    _q("sql", 1, "Which clause filters rows?",
       ["ORDER BY", "WHERE", "GROUP BY", "SELECT"], 1, "WHERE filters rows."),
    _q("sql", 1, "Retrieve all columns from 'users':",
       ["GET * FROM users", "SELECT * FROM users", "FETCH users", "READ users"], 1,
       "SELECT * FROM users."),
    _q("sql", 1, "Which keyword removes duplicate rows?",
       ["UNIQUE", "DISTINCT", "ONLY", "NODUP"], 1, "SELECT DISTINCT ..."),
    _q("sql", 2, "Count rows in 'orders':",
       ["COUNT(orders)", "SELECT COUNT(*) FROM orders",
        "SELECT SUM(*) FROM orders", "LEN(orders)"], 1, "COUNT(*) counts rows."),
    _q("sql", 2, "Which JOIN keeps all left-table rows?",
       ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"], 1,
       "LEFT JOIN keeps unmatched left rows with NULLs."),
    _q("sql", 2, "To sort results descending by 'age':",
       ["ORDER BY age DESC", "SORT age DOWN", "ORDER age -1", "GROUP BY age"], 0,
       "ORDER BY age DESC."),
    _q("sql", 3, "HAVING differs from WHERE because it:",
       ["Is faster", "Filters aggregated groups", "Sorts rows", "Joins tables"], 1,
       "HAVING filters after GROUP BY aggregation."),
    _q("sql", 3, "A PRIMARY KEY guarantees values are:",
       ["Sorted", "Unique and not null", "Indexed only", "Foreign"], 1,
       "Primary keys are unique and non-null."),

    # ---- TECHNICAL INTERVIEW (concepts) ---------------------------------
    _q("interview", 1, "OOP pillar that hides internal state is:",
       ["Inheritance", "Encapsulation", "Polymorphism", "Abstraction"], 1,
       "Encapsulation hides internal details."),
    _q("interview", 1, "Which data structure uses key-value pairs?",
       ["Array", "Hash map", "Stack", "Queue"], 1, "Hash maps store key-value pairs."),
    _q("interview", 1, "Version control tool most used in industry?",
       ["SVN", "Git", "Mercurial", "CVS"], 1, "Git is the industry standard."),
    _q("interview", 2, "REST APIs typically communicate over:",
       ["FTP", "HTTP", "SMTP", "SSH"], 1, "REST rides on HTTP."),
    _q("interview", 2, "Big-O of accessing an array element by index:",
       ["O(n)", "O(1)", "O(log n)", "O(n^2)"], 1, "Direct indexing is O(1)."),
    _q("interview", 2, "Normalization in databases reduces:",
       ["Speed", "Redundancy", "Security", "Indexes"], 1,
       "It reduces data redundancy."),
    _q("interview", 3, "Deadlock requires all EXCEPT:",
       ["Mutual exclusion", "Hold and wait", "Preemption allowed", "Circular wait"], 2,
       "Deadlock needs NO preemption; allowing it prevents deadlock."),
    _q("interview", 3, "ACID's 'D' stands for:",
       ["Distribution", "Durability", "Direction", "Delegation"], 1,
       "Durability: committed data survives crashes."),
]
