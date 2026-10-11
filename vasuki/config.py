"""Central configuration: tiers, XP curve, round definitions."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "vasuki.db")

# The six stages of every placement drive, in order.
ROUNDS = ["aptitude", "coding", "debugging", "python", "sql", "interview"]

ROUND_LABELS = {
    "aptitude": "Aptitude",
    "coding": "Coding Logic",
    "debugging": "Debugging",
    "python": "Python",
    "sql": "SQL",
    "interview": "Technical Interview",
    # company-paper sections
    "reasoning": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "pseudocode": "Pseudocode",
    "cs": "CS Fundamentals",
    "dsa": "DSA Coding",
}

# --- Lore (UI flavour only; game rules don't depend on it) -----------------
# Year 2096. V.A.S.U.K.I. has built a virtual world inside its neural network
# to test whether humans can still outperform AI. Each drive round takes
# place on one of its continents; companies are the Corporate Citadels.
CONTINENTS = {
    "aptara":     {"name": "Aptara",     "skill": "Reasoning & Aptitude",           "icon": "🧭"},
    "technoria":  {"name": "Technoria",  "skill": "Technical Knowledge",            "icon": "⚙️"},
    "glitchwild": {"name": "Glitchwild", "skill": "Debugging & Problem Solving",    "icon": "🐞"},
    "codexia":    {"name": "Codexia",    "skill": "Coding & Creation",              "icon": "⌨️"},
    "citadels":   {"name": "Corporate Citadels", "skill": "Company placement challenges", "icon": "🏙️"},
}

# Which continent each drive round belongs to.
ROUND_CONTINENT = {
    "aptitude": "aptara",
    "coding": "codexia",
    "debugging": "glitchwild",
    "python": "technoria",
    "sql": "technoria",
    "interview": "technoria",
    "reasoning": "aptara",
    "verbal": "aptara",
    "pseudocode": "codexia",
    "cs": "technoria",
    "dsa": "codexia",
}

# How V.A.S.U.K.I. classifies the player, by level (highest match wins).
THREAT_LEVELS = [
    (1, "Human Candidate", "Monitoring"),
    (2, "Anomaly", "Low"),
    (3, "Disruptor", "Elevated"),
    (4, "Rogue Variable", "High"),
    (5, "SYSTEM THREAT", "Critical"),
]


def threat_for_level(level: int) -> dict:
    title, status = THREAT_LEVELS[0][1], THREAT_LEVELS[0][2]
    for min_level, t, s in THREAT_LEVELS:
        if level >= min_level:
            title, status = t, s
    return {"title": title, "status": status, "critical": level >= THREAT_LEVELS[-1][0]}

# ---- Companies and their placement papers ---------------------------------
# Each company sits a different paper. "mcq" companies follow the service-
# company pattern (4 MCQ sections); "dsa" companies set 3 coding problems
# plus 2 MCQ sections. A paper is an ordered list of section keys; "dsa" is
# the coding section. Questions are tagged with the company they belong to.
# (name, tier, pattern, sections, blurb, focus weights for prep plans)
COMPANIES = [
    ("TCS",        1, "mcq", ["aptitude", "reasoning", "verbal", "coding"],
     "Mass-recruiter citadel. Speed and accuracy across four MCQ sections.",
     {"aptitude": 3, "reasoning": 2, "verbal": 2, "coding": 2}),
    ("Infosys",    1, "mcq", ["aptitude", "reasoning", "pseudocode", "verbal"],
     "Puzzles and pseudocode guard this gate. Read every line twice.",
     {"reasoning": 3, "pseudocode": 3, "aptitude": 2, "verbal": 1}),
    ("Wipro",      1, "mcq", ["aptitude", "reasoning", "verbal", "cs"],
     "A wide outer citadel. Fundamentals over tricks.",
     {"aptitude": 2, "reasoning": 2, "verbal": 2, "cs": 2}),
    ("Accenture",  2, "mcq", ["reasoning", "cs", "pseudocode", "verbal"],
     "Cognitive and technical rings. Cloud and security questions lurk here.",
     {"cs": 3, "pseudocode": 2, "reasoning": 2, "verbal": 1}),
    ("Cognizant",  2, "mcq", ["aptitude", "reasoning", "sql", "coding"],
     "A data-heavy citadel. Bring your SQL.",
     {"sql": 3, "aptitude": 2, "coding": 2, "reasoning": 1}),
    ("Capgemini",  2, "mcq", ["aptitude", "pseudocode", "cs", "debugging"],
     "Pseudocode traps and buggy snippets. Trace carefully.",
     {"pseudocode": 3, "debugging": 2, "cs": 2, "aptitude": 1}),
    ("Optum",      3, "dsa", ["aptitude", "cs", "dsa"],
     "Healthcare-tech citadel. Your first real coding gate: 3 DSA problems.",
     {"dsa": 3, "cs": 2, "aptitude": 2}),
    ("Adobe",      3, "dsa", ["cs", "python", "dsa"],
     "Creative-cloud citadel. Strings, arrays and sharp language semantics.",
     {"dsa": 3, "python": 2, "cs": 2}),
    ("Flipkart",   3, "dsa", ["cs", "sql", "dsa"],
     "E-commerce citadel. Systems thinking, SQL, and DP under pressure.",
     {"dsa": 3, "sql": 2, "cs": 2}),
    ("Amazon",     4, "dsa", ["cs", "interview", "dsa"],
     "Leadership principles and hard DSA. Customer obsession is non-negotiable.",
     {"dsa": 3, "interview": 2, "cs": 2}),
    ("Microsoft",  4, "dsa", ["cs", "debugging", "dsa"],
     "Precision engineering citadel. Find the bug, then solve the problem.",
     {"dsa": 3, "debugging": 2, "cs": 2}),
    ("Google",     4, "dsa", ["aptitude", "cs", "dsa"],
     "The Core Citadel. Clear it and the Human Protocol awakens.",
     {"dsa": 3, "cs": 3, "aptitude": 2}),
]
COMPANY_PAPERS = {name: sections for name, _t, _p, sections, _b, _f in COMPANIES}
COMPANY_PATTERN = {name: pattern for name, _t, pattern, _s, _b, _f in COMPANIES}
COMPANY_FOCUS = {name: focus for name, *_rest, focus in COMPANIES}
DSA_PER_PAPER = 3
# Each passed hidden test is worth this many "marks"; a DSA problem counts as
# one question in the score, earning the fraction of its tests passed.
CODE_TIME_LIMIT = 2.0        # seconds of CPU per submission run

# Study pointers shown in prep plans, per round.
ROUND_TIPS = {
    "aptitude":  ["Percentages, ratios and speed-distance-time", "Number series and patterns", "Time-box: 60s per question"],
    "coding":    ["Trace loops and recursion by hand", "Big-O of common operations", "Arrays, strings and hash maps"],
    "debugging": ["Read the error type first (TypeError, NameError…)", "Off-by-one and mutable-default traps", "Predict output before running"],
    "python":    ["Built-in types and their methods", "Slicing, comprehensions, // vs /", "Mutability and references"],
    "sql":       ["SELECT / WHERE / GROUP BY / HAVING order", "JOIN types and when rows disappear", "Aggregates and NULL behaviour"],
    "interview": ["OOP basics and SOLID", "HTTP, REST and what happens on a request", "Explain a project in 60 seconds"],
    "reasoning": ["Syllogisms: draw the Venn diagram", "Seating & blood relations: sketch it", "Series: check differences, then ratios"],
    "verbal":    ["Subject–verb agreement and tenses", "Read the question before the passage", "Eliminate options in para-jumbles"],
    "pseudocode": ["Track every variable in a table", "Watch integer division and modulo", "Count loop iterations exactly"],
    "cs":        ["OS: processes, threads, deadlock, paging", "DBMS: ACID, normalization, indexes", "Networks: OSI layers, TCP vs UDP"],
    "dsa":       ["Arrays, hashing and two pointers", "Sliding window and prefix sums", "DP: define state, transition, base case", "Always state time & space complexity"],
}

# Company tiers. Higher tier = tougher questions + bigger rewards, but gated
# behind a minimum player level so you must earn your way up.
TIERS = {
    1: {"name": "Startup",    "difficulty": 1, "xp_mult": 1.0, "unlock_level": 1},
    2: {"name": "Mid-Cap",    "difficulty": 2, "xp_mult": 1.5, "unlock_level": 2},
    3: {"name": "Product",    "difficulty": 2, "xp_mult": 2.0, "unlock_level": 3},
    4: {"name": "Big Tech",   "difficulty": 3, "xp_mult": 3.0, "unlock_level": 5},
}

# XP awarded per correct answer, scaled by round + company difficulty.
XP_PER_CORRECT = 20
# Bonus XP for clearing an entire drive (all rounds attempted).
DRIVE_CLEAR_BONUS = 100
# A drive is "passed" if the player scores at least this fraction correct.
PASS_THRESHOLD = 0.6

# --- Arena (head-to-head battles) ------------------------------------------
BATTLE_QUESTIONS = 10
BATTLE_TIME_LIMIT = 20          # seconds per question
BATTLE_LIVES = 3                # wrong answer / timeout costs a life
BATTLE_BASE_POINTS = 100
BATTLE_SPEED_BONUS = 50         # max extra points for an instant answer
BATTLE_MAX_COMBO_MULT = 2.0     # combo multiplier cap (+0.25 per streak step)
BATTLE_XP = {"win": 150, "draw": 80, "loss": 40}
BATTLE_MODES = {
    1: {"name": "Skirmish",   "descr": "Easy questions. A friendly warm-up."},
    2: {"name": "Duel",       "descr": "Mixed difficulty. The standard fight."},
    3: {"name": "Deathmatch", "descr": "Everything, including the hardest."},
}

# Questions asked per round.
QUESTIONS_PER_ROUND = 3


def level_for_xp(xp: int) -> int:
    """Level curve: each level needs progressively more XP.

    Level 1 -> 0 XP, Level 2 -> 200, Level 3 -> 500, Level 4 -> 900, ...
    """
    level = 1
    needed = 0
    step = 200
    while xp >= needed + step:
        needed += step
        step += 100
        level += 1
    return level


def xp_for_level(level: int) -> int:
    """Total XP required to reach the start of a given level."""
    needed = 0
    step = 200
    for _ in range(1, level):
        needed += step
        step += 100
    return needed
