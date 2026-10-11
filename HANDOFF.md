# HANDOFF — V.A.S.U.K.I.

A quick-orientation doc for whoever picks this project up next: the **current
state, how to run it, what's done, what's not, and where to look**.

- **What it is:** a Flask web game, a gamified placement-prep simulator with
  real-company papers, DSA coding, practice, and friend battles.
- **Concept & internals:** see `EXPLANATION.md`.
- **Setup from a blank Windows/Mac machine:** see `INITIATE.md`.
- **Feature overview:** see `README.md`.

---

## 1. Current status

**Working and tested end-to-end** (landing → auth → map → drive (MCQ and DSA) →
submit → results → prep practice → DSA library → arena battle → profile).
Tested both through scripted HTTP runs against a copy of the database and with
real mouse clicks in a browser. The only dependency beyond the Python standard
library is **Flask**.

## 2. Run it (short version)

```bash
cd vasuki
python3 -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install flask
python3 app.py            # Windows: python app.py  (or double-click run.bat)
```

Open <http://127.0.0.1:5000>. Stop with **Ctrl + C**. The first launch creates
and seeds `vasuki.db`; later launches migrate it in place.

## 3. Where things live

| Area | File(s) |
|---|---|
| Routes / web layer | `app.py` |
| Constants, tiers, XP curve, **companies + papers**, lore, arena tuning | `vasuki/config.py` |
| Database schema, migrations, queries | `vasuki/db.py` |
| General question bank, achievements, company sync | `vasuki/seed.py` |
| **Company paper content** (MCQs + DSA problems) and loader | `vasuki/papers/` |
| Paper assembly + grading (MCQ + DSA) | `vasuki/rounds.py` |
| Code execution for DSA | `vasuki/coderunner.py` |
| XP/levels, unlocks, stars, achievements | `vasuki/engine.py` |
| Prep (generic practice, skill report) + map company briefs | `vasuki/prep.py` |
| Arena battles + daily streak | `vasuki/arena.py` |
| Pages | `templates/*.html` (`_dsa_problem.html` is the shared editor partial) |
| Base styles / game styles | `static/style.css`, `static/game.css` |
| Shared FX + sound (`window.VFX`) | `static/game.js` |
| 3D core (`window.Core3D`) | `static/core3d.js` |
| Map / drive / editor / practice / battle JS | `static/map.js`, `drive.js`, `code.js`, `practice.js`, `battle.js` |
| Runtime database (generated) | `vasuki.db` |

## 4. What's implemented

- Password auth, hashed passwords, case-insensitive codenames; stale sessions
  (deleted player) are cleared instead of crashing.
- **Map:** 12 real companies on a Candy-Crush-style level road, MCQ/DSA badges,
  0–3 stars, level-gated; each level card shows that company's paper, coding
  problems and the player's accuracy there.
- **Company papers:** 6 MCQ-pattern companies (4 sections × 3), 6 DSA-pattern
  companies (2 MCQ sections × 3 + 3 coding problems). 108 company MCQs, 18 DSA
  problems with 151 tests; every reference solution verified through the real
  grader, and no starter template passes.
- **DSA editor:** auto-indent, Tab/Shift+Tab, line numbers, drafts, Run on
  samples, hidden tests on submit, partial marks.
- **Prep (generic):** topic practice from the combined pool, skill report,
  DSA library with judged submits, study notes.
- **Arena:** codename challenges, 3 modes, server-timed questions, lives,
  combos, ghost race, live invites, leaderboard, battle log.
- XP, level curve, 6 achievements, daily streak, results review.
- Lore UI, sound effects + mute, 3D core, animations throughout; respects
  `prefers-reduced-motion`.
- Idempotent seeding, auto-migration, paper re-load on content change.

## 5. What's NOT done (candidate next steps)

- **Code runner isn't a real sandbox.** Fine on a local machine; needs
  containers / seccomp / a judge service before any public deployment.
- **DSA is Python-only.** No C++/Java.
- **Arena uses the general bank**, not company papers.
- **No timer on company drives** (only the Arena is timed).
- **"Coins and lives"** from the lore aren't implemented outside the Arena.
- **No account management** (change password, delete account).
- **Prep plans start empty** for players whose drives predate per-section
  tracking; accuracy fills in from new drives and practice.
- **Dev server only** (`app.run`); see section 7.
- **No automated test suite committed** (validated with scripted HTTP
  simulations and browser runs during development).

## 6. Gotchas / things to know

- **Port 5000 on macOS** is also used by *AirPlay Receiver*. A "403 Forbidden"
  page at 127.0.0.1:5000 means the game isn't running (or AirPlay grabbed the
  port).
- **Debug vs launcher mode:** plain `python3 app.py` runs in debug mode with the
  auto-reloader. `VASUKI_LAUNCHER=1` (set by `run.bat`) runs without it, and
  then **template changes need a restart**.
- **Company papers hot-load on restart** (fingerprinted). The **general bank**
  only seeds into an empty DB, so delete `vasuki.db` after editing `seed.py`'s
  `QUESTIONS`.
- **Answer keys and hidden tests stay server-side** (`active_drives`, the
  `problems` table). Don't send them to templates or the client.
- **Hidden attributes:** `game.css` has `[hidden] { display: none !important; }`.
  Keep it, or overlays styled with `display:` will block clicks while "hidden".
- **Overlays on the map** are re-parented to `<body>` (`map.js`), because the
  page's entrance animation creates a stacking context that traps them.
- **Windows:** the code runner's CPU/memory limits use `resource`, which is
  POSIX-only; on Windows only the wall-clock timeout applies. `run.bat` must keep
  CRLF line endings (enforced by `.gitattributes`).
- **Not committed** (`.gitignore`): `vasuki.db` (player accounts and progress),
  `.venv/`, `__pycache__/`, and the `.playwright-mcp/` test screenshots.
- **Pre-auth accounts:** players created before password login existed have an
  empty `pass_hash` and can't log in. Fresh DBs are unaffected.

## 7. Before any real deployment

- Set a strong secret: `export VASUKI_SECRET=...` (it defaults to a dev value).
- Run behind a production WSGI server (gunicorn / waitress), not `app.run`.
- Replace `coderunner.py` with a proper sandbox / judge.
- Consider a real database for many concurrent users.

## 8. Provenance

Built from scratch as an implementation of the V.A.S.U.K.I. concept. All logic
is in this folder; there are no external services, CDNs or API keys. Company
questions are original practice questions in each company's usual style, not
real or leaked papers.
