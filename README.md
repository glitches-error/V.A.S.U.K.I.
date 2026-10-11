# V.A.S.U.K.I.

**Virtual Adaptive System for Upskilling through Knowledge and Intelligence**

A Python + Flask, story-driven, gamified placement-preparation game. It's the
year 2096: an AI called V.A.S.U.K.I. has taken over and built a virtual world to
test whether humans can still outthink it. You are a **Human Candidate** working
your way along a Candy-Crush-style map of **12 real companies**, from TCS to
Google. Each company has its own paper: service companies set MCQ papers;
product companies also set **3 DSA coding problems** that you solve in an
in-browser Python editor. Practise any topic in **Prep**, and challenge friends
by codename in the **Arena**.

> *"The AI knows everything. Can you still outthink it?"*

## Documentation

| File | What it covers |
|------|----------------|
| **README.md** (this file) | Overview, features, quick start, structure. |
| **INITIATE.md** | Step-by-step setup on a fresh **Windows** or **Mac** machine. |
| **EXPLANATION.md** | How it works: lore, architecture, data model, game logic. |
| **HANDOFF.md** | Project status, what's done / not done, where things live. |

## Features

- 🗺️ **Level map** — 12 companies as levels on a winding road, 0–3 stars each,
  tap a level to see *that company's* paper (sections, coding problems, your
  accuracy there) and play it.
- 🏢 **Company-specific papers**
  - **MCQ pattern:** TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini —
    4 sections × 3 questions, different sections per company.
  - **DSA + MCQ pattern:** Optum, Adobe, Flipkart, Amazon, Microsoft, Google —
    2 MCQ sections + **3 coding problems** (partial marks per test passed).
- ⌨️ **DSA code editor** — line numbers, auto-indent, Tab/Shift+Tab, **Run**
  against sample tests, hidden tests on submit. Code runs server-side in a
  time/memory-limited subprocess.
- 📋 **Prep (generic)** — practise any of 10 topics from a combined pool of
  every company's questions plus a general bank; instant feedback, streaks, XP;
  a DSA library of all 18 problems; a combined skill report (weakest first).
- ⚔️ **Arena** — challenge a friend by codename: same 10 questions, 20 s each,
  3 lives, speed bonuses and combos, live invite pop-ups, leaderboard.
- 🔒 **Level-gated unlocks** — earn XP to reach tougher companies.
- 🏆 **XP, levels, achievements, daily streak 🔥** — plus a full answer review
  after every drive.
- 🤖 **Lore & game feel** — threat levels up to *SYSTEM THREAT*, five
  continents, a 3D neural core, synthesized sound effects (mute button), warp
  transitions, confetti, combos, screen shake.
- 🔐 **Accounts** — codename + hashed password.

## Requirements

- Python 3.9+ (tested on 3.13)
- Flask (`pip install flask`) — the only third-party dependency. Storage uses the
  built-in `sqlite3` module. No CDN or internet needed at runtime.

## Run

```bash
cd vasuki
python3 app.py
```

Then open **http://127.0.0.1:5000** in your browser. Press **Ctrl + C** in the
terminal to stop.

On first launch the app creates a local SQLite database (`vasuki.db`), seeds the
general question bank and achievements, and loads every company paper from
`vasuki/papers/`.

> **Mac users:** macOS's *AirPlay Receiver* also uses port 5000. If the browser
> shows a "403 Forbidden" page, the game isn't running — or change the port at
> the bottom of `app.py` (see INITIATE.md → Troubleshooting).

## Game flow

```
Enter V.A.S.U.K.I.'s world (sign up / log in)
        v
Map: pick a company level        (locked until you reach its level)
        v
Its placement paper, section by section
   MCQ companies:  4 MCQ sections
   DSA companies:  2 MCQ sections + 3 coding problems
        v
Score >= 60% to breach the citadel  ->  stars, XP, level-ups, achievements
        v
Prep: practise weak topics / solve DSA problems     Arena: battle friends
        v
Climb to Google — the Core Citadel — and activate the Human Protocol
```

## Project structure

```
vasuki/
  app.py               Flask app + all routes (entry point)
  run.bat              One-click launcher for Windows
  vasuki/
    config.py          Tiers, XP curve, companies + their papers, lore, arena settings
    db.py              SQLite schema, migrations, all queries
    seed.py            General question bank, achievements, company sync
    papers/            Company papers (content)
      __init__.py      Loads the papers into the DB when the files change
      mcq_service.py   MCQs for the 6 service companies (72)
      mcq_product.py   MCQs for the 6 product companies (36)
      dsa.py           18 DSA problems with hidden tests + reference solutions
    rounds.py          Builds a company's paper, grades MCQs + DSA
    coderunner.py      Runs player code in a limited subprocess
    engine.py          Profile, XP/levels, unlocks, stars, achievements
    prep.py            Generic practice + skill report; company briefs for the map
    arena.py           Head-to-head battles, scoring, streaks
  templates/           Jinja2 pages (map, drive, result, prep, practice, arena, battle, …)
  static/              style.css + game.css (visuals), game.js (shared FX/sound),
                       drive.js, code.js (editor), map.js, practice.js,
                       battle.js, core3d.js (3D core)
  vasuki.db            Created on first run (delete to reset)
```

## Notes

- Progress is saved automatically to `vasuki.db`.
- Delete `vasuki.db` to reset all progress (everything re-seeds on next launch).

## Adding questions

**A company's paper** — edit the files in `vasuki/papers/` and restart the app.
They're re-loaded automatically when their content changes; no reset needed.

```python
# mcq_service.py / mcq_product.py
("TCS", "aptitude", "Prompt?", ["A", "B", "C", "D"], 2, "why C")
#  company  section                     correct-index ^  explanation ^
```

DSA problems in `dsa.py` are dicts with `statement`, `func`, `starter`,
`tests` (`{"args", "expected", "sample"}`), `solution` and `approach` — see the
existing entries.

**The general bank** (used by the Arena and Prep) — add `_q(...)` entries to
`QUESTIONS` in `vasuki/seed.py`, then delete `vasuki.db` so it re-seeds.
