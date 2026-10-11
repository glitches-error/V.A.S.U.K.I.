# EXPLANATION — How V.A.S.U.K.I. works

**V.A.S.U.K.I.** = *Virtual Adaptive System for Upskilling through Knowledge and
Intelligence.* It is a gamified placement-preparation game. Rather than
grinding disconnected practice questions, the player *experiences* a placement
journey: climb a map of real companies, sit each one's own paper (MCQs and DSA
coding), practise weak spots, and battle friends.

This document explains the **lore, architecture, data model, and game logic** so
a new developer (or a reviewer) can understand the whole system.

---

## 1. The lore

Year 2096. V.A.S.U.K.I., an AI built to protect civilisation, decided humans
were its biggest inefficiency and took over cities, industry, education and
jobs. It built a virtual world inside its neural network to test whether humans
can still outperform it. The player is a **Human Candidate** inside that world.

The lore is UI flavour only; no game rule depends on it. It lives in
`config.CONTINENTS`, `ROUND_CONTINENT` and `THREAT_LEVELS`.

| Game concept | Lore |
|---|---|
| Aptitude / Reasoning / Verbal | Continent of **Aptara** (Reasoning & Aptitude) |
| Coding / Pseudocode / DSA | **Codexia** (Coding & Creation) |
| Debugging | **Glitchwild** (Debugging & Problem Solving) |
| Python / SQL / CS / Interview | **Technoria** (Technical Knowledge) |
| Companies | **Corporate Citadels**; Google (last level) is the Core Citadel |
| Player level | AI threat class: Human Candidate → Anomaly → Disruptor → Rogue Variable → **SYSTEM THREAT** (level 5) |
| Passing a Big Tech drive | **Human Protocol** activated |
| Achievements | "Anomalies" the AI logs about you |

---

## 2. The core loop

```
Sign up / Log in
      │
      ▼
Map  ──  12 company levels on a winding road (level-gated)
      │   tap a level → that company's paper, coding problems, your accuracy there
      ▼
Placement drive  ──  the company's own paper, one section at a time
      │   MCQ companies: 4 sections × 3 MCQs
      │   DSA companies: 2 sections × 3 MCQs + 3 coding problems
      ▼
Scoring  ──  pass if ≥ 60%; 0–3 stars (pass / ≥80% / 100%)
      ▼
Rewards  ──  XP × tier multiplier, level-ups, achievements, unlocks
      │
      ├──▶ Prep   generic practice on any topic, DSA library, skill report
      └──▶ Arena  head-to-head battles with friends by codename
```

---

## 3. Architecture

A small **Flask** app with a clean split between the web layer and game logic.
Storage is one local **SQLite** file. No external services, CDNs or API keys.

```
Browser (HTML/CSS/vanilla JS)
      │  HTTP (pages + small JSON APIs)
      ▼
app.py                 Flask routes: auth, map, drive, prep, arena, APIs
      │  calls
      ▼
vasuki/  (game package — never imports Flask)
  ├─ config.py        tiers, XP curve, companies + papers, lore, arena tuning
  ├─ db.py            schema, migrations, every SQL query
  ├─ seed.py          general bank + achievements; syncs companies from config
  ├─ papers/          company paper content + loader (sync on change)
  ├─ rounds.py        builds a company's paper; grades MCQ + DSA
  ├─ coderunner.py    runs player code in a limited subprocess
  ├─ engine.py        profile, XP→level, unlocks, stars, achievements
  ├─ prep.py          generic practice + skill report; company briefs (map)
  └─ arena.py         battles: invites, timing, scoring, settling, streaks
```

Front-end scripts (`static/`), all dependency-free:

| File | Role |
|---|---|
| `game.js` + `game.css` | Shared effects: warp starfield, boot screen, page warps, sparks, toasts, banners, confetti, XP orbs, screen shake, synthesized sound (`window.VFX`), live invite polling |
| `core3d.js` | The rotating 3D "neural core" on a `<canvas>` (`window.Core3D.pulse()`) |
| `map.js` | Level map road, level card with the company's paper |
| `drive.js` | Section-by-section drive, progress HUD, countdown, submit |
| `code.js` | DSA editor (indent, line numbers, drafts), Run / Submit |
| `practice.js` | Prep topic practice (one MCQ at a time) |
| `battle.js` | Arena battle screen (timer, lives, combos, ghost score) |

---

## 4. Companies and their papers

Twelve companies are defined in `config.COMPANIES` as
`(name, tier, pattern, sections, blurb, focus)`. Map order follows the list.

| Level | Company | Tier | Pattern | Sections |
|---|---|---|---|---|
| 1 | TCS | Startup | MCQ | Aptitude, Reasoning, Verbal, Coding logic |
| 2 | Infosys | Startup | MCQ | Aptitude, Reasoning, Pseudocode, Verbal |
| 3 | Wipro | Startup | MCQ | Aptitude, Reasoning, Verbal, CS |
| 4 | Accenture | Mid-Cap | MCQ | Reasoning, CS, Pseudocode, Verbal |
| 5 | Cognizant | Mid-Cap | MCQ | Aptitude, Reasoning, SQL, Coding logic |
| 6 | Capgemini | Mid-Cap | MCQ | Aptitude, Pseudocode, CS, Debugging |
| 7 | Optum | Product | DSA | Aptitude, CS, **DSA** |
| 8 | Adobe | Product | DSA | CS, Python, **DSA** |
| 9 | Flipkart | Product | DSA | CS, SQL, **DSA** |
| 10 | Amazon | Big Tech | DSA | CS, Interview (leadership principles), **DSA** |
| 11 | Microsoft | Big Tech | DSA | CS, Debugging, **DSA** |
| 12 | Google | Big Tech | DSA | Aptitude, CS, **DSA** |

- **Content** lives in `vasuki/papers/`: `mcq_service.py` (72 MCQs),
  `mcq_product.py` (36 MCQs) and `dsa.py` (18 problems, 3 per DSA company,
  each with 7–10 tests, 2 of them visible samples).
- **Loading:** `papers.sync()` runs at startup. It fingerprints the content and
  re-loads the company questions/problems only when the files change, so you can
  edit a paper and just restart the app.
- **Tagging:** company MCQs have `questions.company` set; the untagged rows are
  the *general bank* (used by the Arena and pooled into Prep).
- **Retired companies:** companies no longer in the list (the original
  fictional ones) get `companies.active = 0`. They leave the map but their rows
  stay, so old drive history still shows.
- The questions are original, written in each company's usual assessment
  *style*; they are not real or leaked papers.

---

## 5. DSA coding problems

- The player writes a Python function (e.g. `def two_sum(nums, target):`) in the
  in-browser editor. Drafts are kept in the browser's `localStorage` so a
  refresh doesn't lose work.
- **Run** → `POST /api/drive/<id>/run` (or `/api/practice/problem/<id>/run`)
  executes the code against the **visible samples only** and shows
  input / expected / got for failures.
- **Submit** runs **every** test. A problem is worth one mark, earned in
  proportion to tests passed (6 of 9 tests = 0.67). An untouched starter counts
  as "no solution submitted" (line endings are normalised so `\r\n` from the
  browser still matches).
- Problems with several valid answers either force a unique one in the statement
  (e.g. "lexicographically smallest") or use `compare: "unordered"`.

### The code runner (`vasuki/coderunner.py`)

Each run is a fresh `python3 -I -S` subprocess in an empty temp directory with:

- CPU-time (≈2 s), memory (256 MB) and output-size limits (`resource.setrlimit`)
  plus a wall-clock timeout;
- a restricted `__builtins__` (no `open`, `exec`, `eval`, `__import__` of
  `os`, `sys`, `subprocess`, `socket`, …);
- the player's `print()` output swallowed; results returned as JSON.

This is **good enough for a local practice app, not a hardened sandbox**. Do not
expose it to untrusted users on the public internet without a real judge
(containers / seccomp / a judge service).

---

## 6. Prep — generic practice

Prep is **not** company-specific (the map is). It pools every question.

- **Skill report** (`prep.overview`): accuracy per topic combining drive results
  (`drive_rounds`) and practice (`practice_log`), ordered weakest first, with
  status *weak / improving / new / mastered* (mastered = ≥ 80% over ≥ 3 answers).
- **Topic practice** (`/prep/practice/<topic>`): one MCQ at a time from **all
  companies + the general bank** for that topic, never repeating until the pool
  is exhausted. Answers are graded server-side (the browser never gets the key
  before answering). +5 XP per correct answer.
- **DSA library** (`/prep/problem/<id>`): all 18 problems with Run + full
  Submit. First full solve of a problem: +40 XP.

---

## 7. Arena — battles with friends

`vasuki/arena.py`. Asynchronous: each player plays their run when they like.

1. Challenge a friend by codename (case-insensitive) and pick a mode:
   Skirmish (easy), Duel (mixed), Deathmatch (all). Questions come from the
   general bank; both players get the **same 10, in the same order**.
2. Each question has a **20 s** clock that starts **server-side** when it is
   served; 3 lives; a miss or timeout costs a life.
3. Points = `(100 + 50 × speed) × combo multiplier` (combo +0.25 per streak,
   capped at ×2).
4. You race your rival's **ghost** (their score at the same question). When both
   runs end, the battle settles: win +150 XP, draw +80, loss +40.
5. Invites appear live: the nav badge and a toast poll `/api/invites` every 8 s.

A daily-streak counter (🔥) counts consecutive days with a finished drive or
battle.

---

## 8. Data model (SQLite)

| Table | Purpose |
|---|---|
| `players` | `name` (unique, case-insensitive), `pass_hash`, `xp` |
| `companies` | `name`, `tier`, `blurb`, `pattern`, `position` (map order), `active` |
| `questions` | MCQs: `round`, `difficulty`, `prompt`, `options` (JSON), `answer`, `explain`, `company` (NULL = general bank) |
| `problems` | DSA: `company`, `title`, `level`, `statement`, `func`, `starter`, `compare`, `tests` (JSON), `solution`, `approach` |
| `achievements`, `player_achievements` | Achievement definitions + who earned what |
| `drives` | One row per finished drive: score, total, passed, XP |
| `drive_rounds` | Per-section results of each drive (feeds Prep + map accuracy) |
| `active_drives` | The in-progress paper + answer key, **server-side** (the session cookie is too small for coding papers) |
| `practice_log` | Every practice answer / judged DSA submit |
| `battles`, `battle_entries`, `battle_answers` | Arena battles, each player's run, each answer |
| `meta` | Paper-content fingerprint |

Schema creation and lightweight in-place migrations (new columns on older DBs)
live in `db.py`; seeding and paper sync are idempotent, so restarting never
duplicates data.

---

## 9. Tiers, XP & scoring

| Tier | Name | Difficulty | XP × | Unlocks at level |
|---|---|---|---|---|
| 1 | Startup | 1 | 1.0 | 1 |
| 2 | Mid-Cap | 2 | 1.5 | 2 |
| 3 | Product | 2 | 2.0 | 3 |
| 4 | Big Tech | 3 | 3.0 | 5 |

- **Pass:** `score / total ≥ 0.6`. DSA marks can be fractional; the recorded
  score is rounded and pass/fail uses that same value so stars and history agree.
- **Stars:** 1 = passed, 2 = ≥ 80%, 3 = 100% (best attempt counts).
- **XP** (`engine.award_drive`): `(score × 20 + 100 if passed) × tier multiplier`.
- **Level curve:** Level 2 at 200 XP, Level 3 at 500, Level 4 at 900, … (step
  grows by 100). Big Tech needs level 5.
- **Level gate** is re-checked server-side on `/drive/<id>`.

---

## 10. Achievements

Checked after every drive (`engine._check_achievements`), granted once each:

| Achievement | Condition |
|---|---|
| First Contact | Finish your first drive |
| Unpredictable | Score 100% on a drive |
| Human Protocol | Pass a Big Tech drive |
| Citadel Breaker | Pass drives at 3 different companies |
| Persistent Signal | Attempt 5 drives |
| System Threat | Reach level 5 |

---

## 11. Authentication

Codename + password, hashed with Werkzeug's `generate_password_hash`; verified
with `check_password_hash`. Codenames are unique case-insensitively. The player
id is kept in Flask's signed session cookie. If that player no longer exists
(e.g. the database was reset), the session is cleared instead of crashing.

---

## 12. Request flow of one drive

1. `GET /drive/<id>` — checks login + unlock, builds the company's paper
   (`rounds.build_drive`), stores questions **and the answer key** in
   `active_drives`, renders the page. The browser never sees answers or hidden
   tests.
2. The player works section by section (`drive.js`); DSA problems can be Run
   against samples (`code.js`).
3. `POST /drive/<id>/submit` — grades MCQs and runs every DSA test
   (`rounds.score_drive`), awards XP + achievements, records the drive and
   per-section results, clears the active drive, and shows the full review.

---

## 13. Extending it

- **Edit a company paper:** change `vasuki/papers/*.py` and restart (auto
  re-load).
- **Add a company:** add a row to `config.COMPANIES` (and its questions /
  problems in `papers/`), restart.
- **General bank:** add `_q(...)` to `QUESTIONS` in `seed.py`, delete `vasuki.db`.
- **Tune the game:** `XP_PER_CORRECT`, `PASS_THRESHOLD`, `QUESTIONS_PER_ROUND`,
  `DSA_PER_PAPER`, `CODE_TIME_LIMIT`, `BATTLE_*` in `config.py`;
  `PRACTICE_XP` / `PRACTICE_SOLVE_XP` in `prep.py`.
