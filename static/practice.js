// practice.js — Prep topic practice: one MCQ at a time from the combined
// pool, graded by the server, with streaks, XP and the usual game effects.
(function () {
  const root = document.getElementById("practice");
  if (!root) return;
  const VFX = window.VFX || {};
  const fx = (n, ...a) => VFX[n] && VFX[n](...a);
  const sound = (n, a) => VFX.sfx && VFX.sfx.play(n, a);
  const $ = (id) => document.getElementById(id);
  const topic = root.dataset.topic;
  const seen = [];
  let current = null, locked = false;
  const stats = { correct: 0, streak: 0, best: 0, xp: 0 };

  const post = (url, body) => fetch(url, {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }).then((r) => r.json());

  function paint() {
    $("phCorrect").textContent = stats.correct;
    $("phStreak").textContent = stats.streak;
    $("phBest").textContent = stats.best;
    $("phXp").textContent = stats.xp;
  }

  async function next() {
    locked = false;
    $("pNext").hidden = true;
    $("pExplain").hidden = true;
    const q = await post("/api/practice/next", { topic, seen });
    if (q.error) { $("pPrompt").textContent = q.error; return; }
    current = q;
    seen.push(q.id);
    const card = $("pCard");
    card.classList.remove("in"); void card.offsetWidth; card.classList.add("in");
    $("pSource").textContent = q.label + " · from " + q.source;
    $("pPrompt").textContent = q.prompt;
    const opts = $("pOptions");
    opts.innerHTML = "";
    q.options.forEach((text, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "bq-opt";
      b.style.setProperty("--i", i);
      b.innerHTML = '<span class="bq-key"></span><span class="bq-text"></span>';
      b.querySelector(".bq-key").textContent = "ABCD"[i];
      b.querySelector(".bq-text").textContent = text;
      b.addEventListener("click", () => answer(i, b));
      opts.appendChild(b);
    });
  }

  async function answer(i, btn) {
    if (locked || !current) return;
    locked = true;
    const buttons = document.querySelectorAll("#pOptions .bq-opt");
    buttons.forEach((b) => (b.disabled = true));
    btn.classList.add("picked");
    const res = await post("/api/practice/answer", { id: current.id, chosen: i });
    if (res.error) { $("pPrompt").textContent = res.error; return; }
    buttons[res.answer] && buttons[res.answer].classList.add("right");
    const r = btn.getBoundingClientRect();
    if (res.correct) {
      stats.correct++; stats.streak++; stats.best = Math.max(stats.best, stats.streak); stats.xp += res.xp;
      sound("correct", stats.streak);
      fx("sparks", r.left + r.width / 2, r.top + r.height / 2, 12 + stats.streak * 2, ["#2ee59d", "#ffcf5c", "#fff"]);
      fx("floater", r.left + r.width / 2, r.top, "+" + res.xp + " XP", "#ffcf5c");
      fx("xpOrbs", r.left + r.width / 2, r.top + r.height / 2, 3);
      if (stats.streak >= 3 && stats.streak % 3 === 0) { sound("combo", stats.streak); fx("banner", "ON FIRE", "STREAK ×" + stats.streak); }
      if (window.Core3D) Core3D.pulse("good");
    } else {
      btn.classList.add("wrong");
      stats.streak = 0;
      sound("wrong");
      fx("shake", 8);
      fx("floater", r.left + r.width / 2, r.top, "MISS", "#ff6b7d");
    }
    if (res.explain) { $("pExplain").textContent = "💡 " + res.explain; $("pExplain").hidden = false; }
    paint();
    $("pNext").hidden = false;
    $("pNext").focus();
  }

  $("pNext").addEventListener("click", next);
  addEventListener("keydown", (e) => {
    if (e.target.matches("input, textarea")) return;
    if (e.key === "Enter" && locked && !$("pNext").hidden) { e.preventDefault(); next(); return; }
    const idx = "ABCD".indexOf(e.key.toUpperCase());
    const b = document.querySelectorAll("#pOptions .bq-opt")[idx];
    if (idx >= 0 && b && !locked) b.click();
  });

  paint();
  next();
})();
