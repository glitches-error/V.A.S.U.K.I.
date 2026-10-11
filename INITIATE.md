# INITIATE — Running V.A.S.U.K.I. from scratch

This guide takes a **brand-new Windows or Mac machine** (nothing installed) and
gets V.A.S.U.K.I. running in the browser. Follow the section for your OS.

The app needs two things: **Python 3.9+** and **Flask**. That's it. Storage uses
Python's built-in `sqlite3`, the database seeds itself on first launch, and no
internet connection is needed once Flask is installed.

---

## 1. Get the project onto the machine

Copy the whole `vasuki/` folder to the new machine (USB, zip, cloud, or Git).
Everything you need lives inside that folder. Open a terminal **inside** it.

---

## 2A. Windows setup

### Install Python
1. Go to <https://www.python.org/downloads/> and download the latest Python 3.
2. Run the installer. **IMPORTANT:** tick **"Add python.exe to PATH"** on the
   first screen, then click *Install Now*.
3. Verify — open **PowerShell** (or Command Prompt) and run:
   ```powershell
   python --version
   ```
   You should see `Python 3.x.x`. (If `python` isn't found, try `py --version`.)

### Easiest: one-click launcher (recommended)
After Python is installed, just **double-click `run.bat`** in the `vasuki`
folder. On first run it creates a virtual environment, installs Flask, starts the
server, and opens <http://127.0.0.1:5000> in your browser automatically. Keep the
black window open while you play; press **Ctrl + C** there to stop.

### Or set it up manually
In PowerShell, `cd` into the `vasuki` folder, then:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install flask
python app.py
```
> If activation is blocked by execution policy, run this once, then retry:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

Now open **http://127.0.0.1:5000** in your browser.

---

## 2B. macOS setup

### Install Python
macOS may already have Python 3. Check first:
```bash
python3 --version
```
If it prints `Python 3.9` or higher, skip ahead. Otherwise install it:
- **Easiest:** download from <https://www.python.org/downloads/> and run the
  installer, **or**
- **Homebrew:** `brew install python` (install Homebrew from <https://brew.sh>
  if you don't have it).

### Set up and run
In Terminal, `cd` into the `vasuki` folder, then:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask
python3 app.py
```

Now open **http://127.0.0.1:5000** in your browser.

---

## 3. Using it

1. On the landing page, click **New Candidate**, choose a codename + password
   (min 4 chars), and press **Enter the Simulation**.
2. You land on the **Map**. Tap the first level (TCS) to see its paper, then
   press **Play**.
3. Work through the paper section by section and submit. Product companies
   (Optum onwards) include **3 coding problems**: write a Python function, press
   **▶ Run sample tests**, and submit.
4. Earn XP and stars, level up, and unlock tougher companies.
5. Use **Prep** to practise any topic or solve DSA problems, and the **⚔️ Arena**
   to challenge a friend by their codename.
6. Next time, use **Returning Candidate** with the same codename + password.

To stop the server: press **Ctrl + C** in the terminal.

---

## 4. Everyday restart (after first setup)

You don't reinstall each time — just activate the environment and run:

**Windows**
```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```
**macOS**
```bash
source .venv/bin/activate
python3 app.py
```

---

## 5. Reset all progress

Stop the server and delete the database file; it re-seeds on next launch:

**Windows:** `del vasuki.db`
**macOS:** `rm vasuki.db`

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `python` not recognized (Windows) | Reinstall Python with *Add to PATH* ticked, or use `py`. |
| `ModuleNotFoundError: flask` | Activate the venv, then `pip install flask`. |
| Port 5000 already in use | Change the port in the last line of `app.py` (`port=5000` → `port=5001`) and open http://127.0.0.1:5001. |
| **Mac:** "403 Forbidden" at 127.0.0.1:5000 | That's macOS *AirPlay Receiver*, not the game. Start the game (`python3 app.py`), or turn off *System Settings → General → AirDrop & Handoff → AirPlay Receiver*, or use another port as above. |
| DSA "Run" says time limit exceeded | Your code has an infinite loop or is too slow; each run gets about 2 seconds. |
| Browser shows nothing | Make sure the terminal says "Running on http://127.0.0.1:5000" and use that exact URL. |
| Activation blocked (Windows) | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. |
| Old login stops working after an update | Delete `vasuki.db` to reset (see section 5). |
