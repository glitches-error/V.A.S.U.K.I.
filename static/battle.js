// battle.js — the Arena battle screen. One timed question at a time; the
// server owns the clock and the answer key, this file only renders, counts
// down, and plays the effects (combo meter, lives, tug-of-war vs the ghost).
(function () {
  const root = document.getElementById("battle");
  if (!root) return;
  const VFX = window.VFX || {};
  const fx = (name, ...a) => VFX[name] && VFX[name](...a);
  const sound = (n, a) => VFX.sfx && VFX.sfx.play(n, a);
  const core = (k) => window.Core3D && Core3D.pulse(k);
  const $ = (id) => document.getElementById(id);

  let state = JSON.parse($("battleState").textContent);
  let deadline = 0, timerId = null, locked = false;
  const LIVES = 3;

  function hearts(n) { return "❤️".repeat(Math.max(0, n)) + "🖤".repeat(Math.max(0, LIVES - n)); }

  // Rival's score at the same point in the run (their "ghost").
  function ghostAt(index) {
    const t = state.rival_trace;
    if (!t.length || index <= 0) return 0;
    return t[Math.min(index, t.length) - 1];
  }

  function paintHud() {
    const me = state.me, rival = state.rival;
    $("myLives").textContent = hearts(me.lives);
    $("rivalLives").textContent = rival.finished ? hearts(rival.lives) : "";
    $("myScore").textContent = me.score;
    $("qPos").textContent = "Q" + Math.min(me.index + 1, state.total) + " / " + state.total;
    const over = me.finished || state.status !== "open";
    const ghost = over && rival.finished ? rival.score : ghostAt(me.index);
    const hasGhost = state.rival_trace.length > 0;
    $("rivalScore").textContent = hasGhost ? ghost : "?";
    $("ghostNote").textContent = over
      ? (rival.finished ? "final scores" : "waiting for " + rival.name)
      : hasGhost
      ? (me.score >= ghost ? "ahead of " + rival.name + "'s ghost" : "behind " + rival.name + "'s ghost")
      : rival.name + " hasn't played yet — set the score to beat";
    // tug of war: 50% = level
    const a = me.score, b = hasGhost ? ghost : a;
    const pct = a + b === 0 ? 50 : Math.max(8, Math.min(92, (a / (a + b)) * 100));
    $("tugFill").style.width = pct + "%";
    $("tugKnot").style.left = pct + "%";
  }

  function showCombo(combo, mult) {
    const m = $("comboMeter");
    if (combo < 2) { m.hidden = true; return; }
    m.hidden = false;
    $("comboText").textContent = "COMBO ×" + combo + "  ·  " + mult.toFixed(2) + "× points";
    m.classList.remove("bump"); void m.offsetWidth; m.classList.add("bump");
    m.dataset.heat = Math.min(4, Math.floor(combo / 2));
  }

  function renderQuestion() {
    const q = state.question;
    if (!q) return finish();
    locked = false;
    $("timerRing").classList.remove("stopped");
    const card = $("qCard");
    card.classList.remove("in"); void card.offsetWidth; card.classList.add("in");
    $("qZone").textContent = q.continent + " · " + q.round;
    $("qPrompt").textContent = q.prompt;
    $("qExplain").hidden = true;
    const opts = $("qOptions");
    opts.innerHTML = "";
    q.options.forEach((text, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "bq-opt";
      b.style.setProperty("--i", i);
      b.innerHTML = '<span class="bq-key"></span><span class="bq-text"></span>';
      b.querySelector(".bq-key").textContent = "ABCD"[i] || i + 1;
      b.querySelector(".bq-text").textContent = text;
      b.addEventListener("click", () => submit(i, b));
      opts.appendChild(b);
    });
    paintHud();
    startTimer(q.remaining);
  }

  function startTimer(seconds) {
    clearInterval(timerId);
    deadline = performance.now() + seconds * 1000;
    const arc = $("timerArc"), num = $("timerNum"), ring = $("timerRing");
    const C = 2 * Math.PI * 52;
    arc.style.strokeDasharray = C;
    let lastWhole = null;
    timerId = setInterval(() => {
      const left = Math.max(0, (deadline - performance.now()) / 1000);
      arc.style.strokeDashoffset = C * (1 - left / state.time_limit);
      const whole = Math.ceil(left);
      num.textContent = whole;
      ring.classList.toggle("danger", left <= 5);
      if (left <= 5 && whole !== lastWhole && whole > 0) sound("tick");
      lastWhole = whole;
      if (left <= 0) { clearInterval(timerId); submit(null, null); }
    }, 100);
  }

  async function submit(choice, btn) {
    if (locked) return;
    locked = true;
    clearInterval(timerId);
    $("timerRing").classList.add("stopped");
    const q = state.question;
    document.querySelectorAll(".bq-opt").forEach((b) => (b.disabled = true));
    if (btn) btn.classList.add("picked");
    let res;
    try {
      const r = await fetch("/api/battle/" + state.id + "/answer", {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index: q.index, chosen: choice }),
      });
      res = await r.json();
      if (!r.ok) throw new Error(res.error || "error");
    } catch (e) {
      location.reload();
      return;
    }
    reveal(res, btn);
    state = res.state;
    setTimeout(() => (state.question ? renderQuestion() : finish()), res.correct ? 1100 : 2200);
  }

  function reveal(res, btn) {
    const opts = document.querySelectorAll(".bq-opt");
    opts[res.answer] && opts[res.answer].classList.add("right");
    const rect = (btn || $("qCard")).getBoundingClientRect();
    const x = rect.left + rect.width / 2, y = rect.top + rect.height / 2;
    if (res.correct) {
      sound("correct", res.combo);
      core("good");
      fx("sparks", x, y, 14 + res.combo * 2, ["#2ee59d", "#ffcf5c", "#fff"]);
      fx("floater", x, rect.top, "+" + res.points, res.combo >= 3 ? "#ffcf5c" : "#2ee59d");
      if (res.combo >= 3) { sound("combo", res.combo); fx("banner", "UNPREDICTABLE", "COMBO ×" + res.combo); }
      fx("xpOrbs", x, y, Math.min(6, 2 + res.combo));
    } else {
      if (btn) btn.classList.add("wrong");
      sound("wrong");
      core("hit");
      fx("shake", 10);
      document.body.classList.remove("hurt"); void document.body.offsetWidth; document.body.classList.add("hurt");
      fx("floater", x, rect.top, res.timed_out ? "TIME OUT  −❤️" : "MISS  −❤️", "#ff6b7d");
      const lives = $("myLives");
      lives.classList.remove("lose-life"); void lives.offsetWidth; lives.classList.add("lose-life");
      if (res.explain) { $("qExplain").textContent = "💡 " + res.explain; $("qExplain").hidden = false; }
    }
    showCombo(res.combo, res.multiplier);
    state.me.score = res.score; state.me.lives = res.lives;
    paintHud();
  }

  function finish() {
    clearInterval(timerId);
    $("stage").hidden = true;
    $("comboMeter").hidden = true;
    const end = $("endScreen");
    end.hidden = false;
    const me = state.me, rival = state.rival;
    $("endMine").textContent = me.score;
    $("endTheirs").textContent = rival.finished ? rival.score : "?";
    $("endStats").innerHTML = "";
    [["✅", me.correct + " correct"], ["🔥", "best combo ×" + me.best_combo], ["❤️", me.lives + " lives left"]]
      .forEach(([i, t]) => { const s = document.createElement("span"); s.textContent = i + " " + t; $("endStats").appendChild(s); });

    const r = state.result;
    if (!r) {
      $("endKicker").textContent = "RUN COMPLETE";
      $("endTitle").textContent = "Score locked in: " + me.score;
      $("endNote").textContent = rival.name + " hasn't finished yet. Their invite is waiting — you'll see the verdict in the Arena.";
      sound("coin");
      core("gold");
      pollForVerdict();
      return;
    }
    end.dataset.outcome = r.outcome;
    $("endKicker").textContent = { win: "VICTORY", loss: "DEFEAT", draw: "DRAW" }[r.outcome];
    $("endTitle").textContent = { win: "You outthought " + rival.name + "!", loss: rival.name + " adapted faster.", draw: "Perfectly balanced." }[r.outcome];
    $("endNote").textContent = "+" + r.xp + " XP added to your profile.";
    if (r.outcome === "win") { sound("win"); fx("confetti", 140); core("gold"); VFX.starfield && VFX.starfield.boost(8, 1200); }
    else if (r.outcome === "loss") { sound("lose"); core("hit"); document.body.classList.add("hurt"); }
    else sound("coin");
    const er = end.getBoundingClientRect();
    setTimeout(() => fx("xpOrbs", er.left + er.width / 2, er.top + 80, 12), 700);
  }

  // While waiting for the rival, check occasionally so the verdict lands live.
  function pollForVerdict() {
    const id = setInterval(async () => {
      try {
        const s = await (await fetch("/api/battle/" + state.id, { credentials: "same-origin" })).json();
        if (s.result) { clearInterval(id); state = s; finish(); }
      } catch (e) {}
    }, 6000);
  }

  // Keyboard: A-D / 1-4 to answer.
  addEventListener("keydown", (e) => {
    if (locked || !state.question) return;
    const k = e.key.toUpperCase();
    const i = "ABCD".indexOf(k) >= 0 ? "ABCD".indexOf(k) : "1234".indexOf(k);
    const btn = document.querySelectorAll(".bq-opt")[i];
    if (btn) btn.click();
  });

  // Intro: show the matchup, then drop into the first question.
  function intro() {
    if (!state.question || VFX.reduced || state.me.index > 0) return renderQuestion();
    const el = document.createElement("div");
    el.className = "countdown";
    el.innerHTML = '<p class="cd-label">Arena battle · ' + state.mode + '</p><div class="cd-company"></div><p class="cd-meta"></p><div class="cd-num"></div>';
    el.querySelector(".cd-company").textContent = state.me.name + "  vs  " + state.rival.name;
    el.querySelector(".cd-meta").textContent = state.total + " questions · " + state.time_limit + "s each · 3 lives";
    document.body.appendChild(el);
    const num = el.querySelector(".cd-num");
    let i = 0;
    const steps = ["3", "2", "1", "FIGHT!"];
    (function tick() {
      if (i >= steps.length) { el.classList.add("out"); setTimeout(() => el.remove(), 450); return renderQuestion(); }
      num.textContent = steps[i];
      num.className = "cd-num tick" + (i === 3 ? " go" : "");
      sound(i === 3 ? "go" : "count");
      if (i === 3) { core("hit"); fx("sparks", innerWidth / 2, innerHeight / 2 + 60, 26); }
      i++;
      setTimeout(tick, 750);
    })();
  }

  paintHud();
  if (state.status !== "open" || state.me.finished) finish();
  else (VFX.whenReady || ((f) => f()))(intro);
})();
