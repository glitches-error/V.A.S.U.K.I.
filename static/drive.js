// Drive interactivity: highlight chosen options, track round progress,
// confirm before submitting an incomplete drive, and the game effects
// (countdown, round banners, ripples, floaters) via window.VFX from game.js.
// Rounds are shown one section at a time.
(function () {
  const form = document.getElementById("driveForm");
  if (!form) return;
  const VFX = window.VFX || {};
  const fx = (name, ...args) => VFX[name] && VFX[name](...args);
  const sound = (name, arg) => VFX.sfx && VFX.sfx.play(name, arg);
  let streak = 0;

  const cards = Array.from(form.querySelectorAll(".qcard"));
  const total = cards.length;
  const progress = document.getElementById("driveProgress");
  const hudCount = document.getElementById("hudCount");
  const trackerSteps = Array.from(document.querySelectorAll(".rt-step"));
  const submitBtn = document.getElementById("submitBtn");
  const head = document.querySelector(".drive-head");
  let countdownDone = false;

  // A card is answered when an option is picked, or (DSA) the code was edited.
  function isAnswered(card) {
    if (card.classList.contains("dsa-card")) return card.dataset.edited === "1";
    return !!card.querySelector("input[type=radio]:checked");
  }

  function answeredCount() {
    let n = 0;
    cards.forEach((card) => {
      if (isAnswered(card)) n++;
    });
    return n;
  }

  // Which rounds are fully answered -> mark tracker steps done.
  function updateTracker() {
    const byRound = {};
    cards.forEach((card) => {
      const r = card.dataset.round;
      byRound[r] = byRound[r] || { total: 0, done: 0 };
      byRound[r].total++;
      if (isAnswered(card)) byRound[r].done++;
    });
    trackerSteps.forEach((step) => {
      const r = step.dataset.round;
      const info = byRound[r];
      const complete = info && info.done === info.total;
      if (complete && !step.classList.contains("done")) {
        step.classList.add("done", "pop");
        step.addEventListener("animationend", () => step.classList.remove("pop"), { once: true });
        const rect = step.getBoundingClientRect();
        fx("sparks", rect.left + rect.width / 2, rect.top + rect.height / 2, 16, ["#45e0a0", "#fff"]);
        fx("floater", rect.left + rect.width / 2, rect.top + 24, "ZONE CLEARED", "#45e0a0");
        sound("combo", 6);
        if (window.Core3D) Core3D.pulse("gold");
      } else if (!complete) {
        step.classList.remove("done");
      }
    });
  }

  function refresh() {
    const n = answeredCount();
    const pct = total ? Math.round((n / total) * 100) : 0;
    if (progress) progress.style.width = pct + "%";
    if (hudCount) hudCount.textContent = n + "/" + total;
    if (submitBtn) submitBtn.classList.toggle("ready", pct === 100);
    updateTracker();
    // Glow "Next round" once every question in the visible round is answered.
    const panel = form.querySelector(".round-panel.active");
    const nextRound = document.getElementById("nextRound");
    if (panel && nextRound) {
      const done = Array.from(panel.querySelectorAll(".qcard")).every(
        (c) => isAnswered(c));
      nextRound.classList.toggle("ready", done);
    }
  }

  // Click ripple inside an option.
  form.addEventListener("pointerdown", (e) => {
    const opt = e.target.closest(".opt");
    if (!opt || VFX.reduced) return;
    const r = opt.getBoundingClientRect();
    const size = Math.max(r.width, r.height) * 2;
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.width = ripple.style.height = size + "px";
    ripple.style.left = e.clientX - r.left - size / 2 + "px";
    ripple.style.top = e.clientY - r.top - size / 2 + "px";
    opt.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove());
  });

  form.addEventListener("change", (e) => {
    if (e.target.matches("input[type=radio]")) {
      const card = e.target.closest(".qcard");
      const first = !card.classList.contains("answered");
      card.querySelectorAll(".opt").forEach((o) => o.classList.remove("chosen"));
      const opt = e.target.closest(".opt");
      opt.classList.add("chosen");
      card.classList.add("answered");
      sound("select");
      if (first) {
        const r = opt.getBoundingClientRect();
        streak++;
        fx("floater", r.right - 50, r.top, streak >= 3 ? "STREAK ×" + streak : "UNPREDICTED", streak >= 3 ? "#ffcf5c" : "#2ee59d");
        if (streak >= 3) sound("combo", streak);
        if (window.Core3D) Core3D.pulse("good");
        if (hudCount) {
          hudCount.classList.remove("bump"); void hudCount.offsetWidth; hudCount.classList.add("bump");
        }
      }
      refresh();
    }
  });

  form.addEventListener("submit", (e) => {
    const left = total - answeredCount();
    if (left > 0) {
      const ok = confirm(
        left + " question(s) unanswered. Submit anyway? Blanks count as wrong."
      );
      if (!ok) {
        e.preventDefault();
        const blank = cards.find((c) => !isAnswered(c));
        if (blank) showRound(panels.indexOf(blank.closest(".round-panel")), true);
        return;
      }
    }
    if (VFX.reduced) return;
    // Hold the submit briefly for the "evaluating" screen.
    e.preventDefault();
    const overlay = document.createElement("div");
    overlay.className = "evaluating";
    overlay.innerHTML = '<div class="eval-ring"></div><div class="eval-text">V.A.S.U.K.I. IS ANALYSING YOUR ANSWERS…</div>';
    document.body.appendChild(overlay);
    if (VFX.starfield) VFX.starfield.boost(10);
    sound("whoosh");
    setTimeout(() => HTMLFormElement.prototype.submit.call(form), 1300);
  });

  // Section-wise flow: show one round at a time, navigate with
  // Previous / Next or by clicking a round in the tracker.
  const panels = Array.from(form.querySelectorAll(".round-panel"));
  const prevBtn = document.getElementById("prevRound");
  const nextBtn = document.getElementById("nextRound");
  const roundPos = document.getElementById("roundPos");
  const submitRow = form.querySelector(".submit-row");
  let current = -1;

  function showRound(idx, announce) {
    if (idx < 0 || idx >= panels.length || idx === current) return;
    const dir = idx > current ? "from-right" : "from-left";
    panels.forEach((p, i) => {
      p.classList.remove("active", "from-right", "from-left");
      if (i === idx) { p.classList.add("active"); if (current !== -1) p.classList.add(dir); }
    });
    current = idx;
    const round = panels[idx].dataset.round;
    const heading = panels[idx].querySelector(".round-heading");
    trackerSteps.forEach((s) => s.classList.toggle("current", s.dataset.round === round));
    requestAnimationFrame(() => heading && heading.classList.add("lit"));
    if (prevBtn) prevBtn.hidden = idx === 0;
    if (nextBtn) nextBtn.hidden = idx === panels.length - 1;
    if (roundPos) roundPos.textContent = "Zone " + (idx + 1) + " of " + panels.length + " · " + panels[idx].dataset.continent;
    if (submitRow) submitRow.classList.toggle("locked", idx !== panels.length - 1);
    const top = document.querySelector(".drive-head");
    if (top && window.scrollY > top.offsetTop) window.scrollTo({ top: top.offsetTop, behavior: "smooth" });
    refresh();
    if (announce && countdownDone) {
      fx("banner", "ZONE " + (idx + 1) + " / " + panels.length + " · " + panels[idx].dataset.continent, roundName(idx));
    }
  }
  function roundName(idx) {
    const step = trackerSteps.find((s) => s.dataset.round === panels[idx].dataset.round);
    return step ? step.textContent.replace(/^\S+\s/, "").trim() : "";
  }

  if (prevBtn) prevBtn.addEventListener("click", () => showRound(current - 1, true));
  if (nextBtn) nextBtn.addEventListener("click", () => showRound(current + 1, true));
  trackerSteps.forEach((step) => step.addEventListener("click", () => {
    showRound(panels.findIndex((p) => p.dataset.round === step.dataset.round), true);
  }));
  showRound(0, false);

  // 3-2-1-GO countdown before the drive starts.
  function countdown() {
    if (VFX.reduced || !head) { countdownDone = true; return; }
    const el = document.createElement("div");
    el.className = "countdown";
    el.innerHTML = '<p class="cd-label">Infiltrating Corporate Citadel</p><div class="cd-company"></div>' +
      '<p class="cd-meta"></p><div class="cd-num"></div>';
    el.querySelector(".cd-company").textContent = head.dataset.company;
    el.querySelector(".cd-meta").textContent =
      head.dataset.tier + " · " + "★".repeat(+head.dataset.stars || 1) + " · " + total + " challenges";
    document.body.appendChild(el);
    const num = el.querySelector(".cd-num");
    const steps = ["3", "2", "1", "GO!"];
    let i = 0, timer;
    function finish() {
      if (countdownDone) return;
      countdownDone = true;
      clearTimeout(timer);
      el.classList.add("out");
      setTimeout(() => el.remove(), 450);
      if (panels.length) fx("banner", "ZONE 1 / " + panels.length + " · " + panels[0].dataset.continent, roundName(0));
    }
    function tick() {
      if (countdownDone) return;
      if (i >= steps.length) return finish();
      num.textContent = steps[i];
      num.className = "cd-num tick" + (steps[i] === "GO!" ? " go" : "");
      sound(steps[i] === "GO!" ? "go" : "count");
      void num.offsetWidth;
      if (steps[i] === "GO!") {
        fx("sparks", innerWidth / 2, innerHeight / 2 + 60, 26);
        if (VFX.starfield) VFX.starfield.boost(9, 700);
      }
      i++;
      timer = setTimeout(tick, 800);
    }
    el.addEventListener("click", finish);
    timer = setTimeout(tick, 900);
  }
  (VFX.whenReady || ((fn) => fn()))(countdown);

  document.addEventListener("vasuki:code-edited", refresh);
  refresh();
})();
