// game.js — game-feel effects shared by every page: warp starfield, boot
// screen, page warps, click sparks, card tilt, toasts, level-up, confetti.
// Exposes window.VFX so page scripts (drive.js) can trigger effects.
(function () {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(pointer: fine)").matches;
  const COLORS = ["#2ee59d", "#1fb5c9", "#ffcf5c", "#45e0a0", "#ff6b7d"];
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const rand = (a, b) => a + Math.random() * (b - a);

  // ---------------------------------------------------------------- starfield
  const starfield = (function () {
    const canvas = $("#starfield");
    if (!canvas) return { boost() {} };
    const ctx = canvas.getContext("2d");
    let w, h, stars = [], speed = 0.6, target = 0.6, mx = 0, my = 0;

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.width = innerWidth * dpr;
      h = canvas.height = innerHeight * dpr;
      const count = Math.round(Math.min(260, (innerWidth * innerHeight) / 5500));
      stars = Array.from({ length: count }, () => spawn(true));
    }
    function spawn(anyDepth) {
      return { x: rand(-1, 1), y: rand(-1, 1), z: anyDepth ? rand(0.05, 1) : 1,
               c: Math.random() < 0.18 ? COLORS[Math.floor(rand(0, 2))] : "#ffffff" };
    }
    function frame() {
      speed += (target - speed) * 0.06;
      ctx.clearRect(0, 0, w, h);
      const cx = w / 2 + mx * w * 0.03, cy = h / 2 + my * h * 0.03, scale = Math.max(w, h) * 0.6;
      for (const s of stars) {
        const pz = s.z;
        s.z -= 0.0016 * speed;
        if (s.z <= 0.02) { Object.assign(s, spawn(false)); continue; }
        const x = cx + (s.x / s.z) * scale, y = cy + (s.y / s.z) * scale;
        if (x < 0 || x > w || y < 0 || y > h) { Object.assign(s, spawn(false)); continue; }
        const px = cx + (s.x / pz) * scale, py = cy + (s.y / pz) * scale;
        const r = (1 - s.z) * 2.2;
        ctx.globalAlpha = Math.min(1, (1 - s.z) * 1.4);
        ctx.strokeStyle = ctx.fillStyle = s.c;
        if (speed > 3) {
          ctx.lineWidth = r; ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(x, y); ctx.stroke();
        } else {
          ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
        }
      }
      if (!reduced) requestAnimationFrame(frame);
    }
    resize();
    addEventListener("resize", resize);
    if (finePointer) addEventListener("mousemove", (e) => {
      mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5;
    });
    if (reduced) { speed = target = 0; frame(); } // one still frame
    else requestAnimationFrame(frame);
    return { boost(v, ms) { target = v; if (ms) setTimeout(() => (target = 0.6), ms); } };
  })();

  // ------------------------------------------------------------------ effects
  function fxEl(cls, x, y, html) {
    const el = document.createElement("div");
    el.className = "fx " + cls;
    el.style.left = x + "px"; el.style.top = y + "px";
    if (html) el.innerHTML = html;
    document.body.appendChild(el);
    return el;
  }

  function sparks(x, y, n, colors) {
    if (reduced) return;
    n = n || 12;
    const ring = fxEl("ring", x - 7, y - 7);
    ring.animate([{ transform: "scale(.3)", opacity: 1 }, { transform: "scale(4)", opacity: 0 }],
      { duration: 500, easing: "ease-out" }).onfinish = () => ring.remove();
    for (let i = 0; i < n; i++) {
      const p = fxEl("spark", x - 3, y - 3);
      p.style.background = (colors || COLORS)[i % (colors || COLORS).length];
      const ang = (Math.PI * 2 * i) / n + rand(-0.3, 0.3), dist = rand(30, 80);
      p.animate([
        { transform: "translate(0,0) scale(1)", opacity: 1 },
        { transform: `translate(${Math.cos(ang) * dist}px, ${Math.sin(ang) * dist}px) scale(0)`, opacity: 0 },
      ], { duration: rand(450, 750), easing: "cubic-bezier(.2,.8,.2,1)" }).onfinish = () => p.remove();
    }
  }

  function floater(x, y, text, color) {
    if (reduced) return;
    const el = fxEl("floater", x, y, text);
    el.style.color = color || "#ffcf5c";
    el.animate([
      { transform: "translate(-50%, 0) scale(.6)", opacity: 0 },
      { transform: "translate(-50%, -18px) scale(1.15)", opacity: 1, offset: 0.25 },
      { transform: "translate(-50%, -60px) scale(1)", opacity: 0 },
    ], { duration: 1100, easing: "ease-out" }).onfinish = () => el.remove();
  }

  function banner(kicker, title) {
    if (reduced) return;
    $$(".banner").forEach((b) => b.remove());
    const el = document.createElement("div");
    el.className = "banner";
    el.innerHTML = `<small></small><strong></strong>`;
    el.querySelector("small").textContent = kicker;
    el.querySelector("strong").textContent = title;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2100);
  }

  function confetti(count) {
    if (reduced) return;
    const layer = document.createElement("div");
    layer.className = "confetti";
    for (let i = 0; i < (count || 120); i++) {
      const p = document.createElement("i");
      p.style.left = rand(0, 100) + "vw";
      p.style.background = COLORS[i % COLORS.length];
      p.style.animationDelay = rand(0, 0.9) + "s";
      p.style.animationDuration = rand(2.2, 4) + "s";
      p.style.setProperty("--drift", rand(-120, 120) + "px");
      p.style.setProperty("--spin", rand(-720, 720) + "deg");
      layer.appendChild(p);
    }
    document.body.appendChild(layer);
    setTimeout(() => layer.remove(), 5500);
  }

  function toast(icon, kicker, title, descr) {
    let box = $(".toasts");
    if (!box) { box = document.createElement("div"); box.className = "toasts"; document.body.appendChild(box); }
    const el = document.createElement("div");
    el.className = "toast";
    el.innerHTML = `<span class="t-icon"></span><div><small></small><strong></strong><div class="section-note" style="margin:0;font-size:12px"></div></div>`;
    el.querySelector(".t-icon").textContent = icon;
    el.querySelector("small").textContent = kicker;
    el.querySelector("strong").textContent = title;
    el.querySelector(".section-note").textContent = descr || "";
    box.appendChild(el);
    sfx.play("coin");
    setTimeout(() => {
      const r = el.getBoundingClientRect();
      sparks(r.left + 28, r.top + r.height / 2, 14, ["#ffcf5c", "#fff"]);
    }, 350);
    setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 450); }, 4800);
  }

  function levelUp(level, threat, onDone) {
    const el = document.createElement("div");
    el.className = "levelup-screen";
    el.innerHTML = `<div class="lu-rays"></div><div class="lu-core"><small>Threat level rising</small>
      <strong></strong><p>V.A.S.U.K.I. reclassifies you: <b class="lu-threat"></b></p><em>tap to continue</em></div>`;
    el.querySelector("strong").textContent = level;
    el.querySelector(".lu-threat").textContent = threat || "Anomaly";
    document.body.appendChild(el);
    starfield.boost(6, 900);
    confetti(80);
    sfx.play("levelup");
    setTimeout(() => sparks(innerWidth / 2, innerHeight / 2, 28, ["#ffcf5c", "#fff", "#ff6b7d"]), 400);
    let closed = false;
    function close() {
      if (closed) return; closed = true;
      el.classList.add("out");
      setTimeout(() => { el.remove(); onDone && onDone(); }, 500);
    }
    el.addEventListener("click", close);
    setTimeout(close, 3600);
  }

  function countUp(el, delay) {
    const target = parseInt(el.dataset.count, 10) || 0;
    if (reduced || !target) return;
    el.textContent = "0";
    setTimeout(() => {
      const start = performance.now(), dur = 1100;
      (function step(now) {
        const k = Math.min(1, (now - start) / dur);
        el.textContent = Math.round(target * (1 - Math.pow(1 - k, 3)));
        if (k < 1) requestAnimationFrame(step);
      })(start);
    }, delay || 400);
  }

  // ------------------------------------------------------------------ sound
  // Synthesised on the fly with Web Audio — no audio files. Off until the
  // first user gesture (browser rule); mute state is remembered per browser.
  const sfx = (function () {
    let ctx = null, muted = false, unlocked = false;
    const unlock = () => { unlocked = true; };
    ["pointerdown", "keydown", "touchstart"].forEach((ev) => addEventListener(ev, unlock, { once: true, capture: true }));
    try { muted = localStorage.getItem("vasuki-muted") === "1"; } catch (e) {}
    function ac() {
      if (!unlocked) return null;
      if (!ctx) { try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { return null; } }
      if (ctx.state === "suspended") ctx.resume();
      return ctx;
    }
    function tone(freq, dur, opts) {
      if (muted) return;
      const a = ac(); if (!a) return;
      opts = opts || {};
      const t0 = a.currentTime + (opts.delay || 0);
      const osc = a.createOscillator(), gain = a.createGain();
      osc.type = opts.type || "square";
      osc.frequency.setValueAtTime(freq, t0);
      if (opts.to) osc.frequency.exponentialRampToValueAtTime(opts.to, t0 + dur);
      gain.gain.setValueAtTime(0.0001, t0);
      gain.gain.exponentialRampToValueAtTime(opts.vol || 0.06, t0 + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      osc.connect(gain).connect(a.destination);
      osc.start(t0); osc.stop(t0 + dur + 0.02);
    }
    const seq = (notes, type, step) => notes.forEach((f, i) => tone(f, 0.14, { type, delay: i * (step || 0.07) }));
    const play = {
      click: () => tone(660, 0.05, { type: "triangle", vol: 0.03 }),
      hover: () => tone(1200, 0.03, { type: "sine", vol: 0.012 }),
      select: () => tone(520, 0.08, { type: "triangle", to: 780, vol: 0.05 }),
      correct: (combo) => seq([523, 659, 784].map((f) => f * Math.pow(1.06, Math.min(combo || 0, 8))), "square"),
      wrong: () => { tone(220, 0.25, { type: "sawtooth", to: 90, vol: 0.06 }); },
      tick: () => tone(1000, 0.03, { type: "square", vol: 0.025 }),
      combo: (n) => seq([784, 988, 1175, 1568].slice(0, Math.min(4, 1 + Math.floor(n / 2))), "square", 0.05),
      whoosh: () => tone(200, 0.35, { type: "sawtooth", to: 1400, vol: 0.03 }),
      win: () => seq([523, 659, 784, 1047, 784, 1047], "square", 0.11),
      lose: () => seq([392, 330, 262, 196], "triangle", 0.16),
      levelup: () => seq([523, 659, 784, 1047, 1319, 1568], "square", 0.08),
      coin: () => { tone(988, 0.08, { type: "square", vol: 0.04 }); tone(1319, 0.2, { type: "square", vol: 0.04, delay: 0.08 }); },
      go: () => tone(440, 0.4, { type: "square", to: 880, vol: 0.06 }),
      count: () => tone(440, 0.12, { type: "square", vol: 0.05 }),
      alarm: () => seq([880, 660, 880, 660], "sawtooth", 0.12),
    };
    return {
      play(name, arg) { try { play[name] && play[name](arg); } catch (e) {} },
      get muted() { return muted; },
      toggle() {
        muted = !muted;
        try { localStorage.setItem("vasuki-muted", muted ? "1" : "0"); } catch (e) {}
        if (!muted) play.select();
        return muted;
      },
    };
  })();

  // XP orbs: fly from a point into the player's XP bar (or the top-right HUD).
  function xpOrbs(x, y, count) {
    if (reduced) return;
    const target = $(".xpbar") || $(".nav");
    const r = target ? target.getBoundingClientRect() : { left: innerWidth - 60, top: 20, width: 0, height: 0 };
    const tx = r.left + r.width * 0.8, ty = r.top + r.height / 2;
    for (let i = 0; i < (count || 8); i++) {
      const orb = fxEl("xp-orb", x, y);
      const mx = x + rand(-120, 120), my = y + rand(-120, 40);
      orb.animate([
        { transform: "translate(0,0) scale(.4)", opacity: 0 },
        { transform: `translate(${mx - x}px, ${my - y}px) scale(1.2)`, opacity: 1, offset: 0.35 },
        { transform: `translate(${tx - x}px, ${ty - y}px) scale(.5)`, opacity: 0.9 },
      ], { duration: 900 + i * 60, easing: "cubic-bezier(.5,0,.3,1)", delay: i * 40 }).onfinish = () => {
        orb.remove();
        if (i === 0 && target) { target.classList.remove("xp-gulp"); void target.offsetWidth; target.classList.add("xp-gulp"); sfx.play("coin"); }
      };
    }
  }

  function shake(strength) {
    if (reduced) return;
    const main = $(".container");
    main.animate([
      { transform: "translate(0,0)" }, { transform: `translate(${-strength}px, ${strength / 2}px)` },
      { transform: `translate(${strength}px, ${-strength / 2}px)` }, { transform: `translate(${-strength / 2}px, 0)` },
      { transform: "translate(0,0)" },
    ], { duration: 320, easing: "ease-out" });
  }

  window.VFX = { sparks, floater, banner, confetti, toast, levelUp, countUp, starfield, reduced, sfx, xpOrbs, shake };

  // --------------------------------------------------------------- boot screen
  function finishBoot() {
    const root = document.documentElement;
    if (!root.classList.contains("booting")) return;
    const boot = $(".boot");
    try { sessionStorage.setItem("vasuki-booted", "1"); } catch (e) {}
    starfield.boost(7, 700);
    if (boot) boot.classList.add("done");
    setTimeout(() => root.classList.remove("booting"), 250);
    document.dispatchEvent(new Event("vasuki:ready"));
  }
  (function boot() {
    if (!document.documentElement.classList.contains("booting")) {
      setTimeout(() => document.dispatchEvent(new Event("vasuki:ready")), 0);
      return;
    }
    const log = $(".boot-log");
    const lines = ["> YEAR 2096 · V.A.S.U.K.I. ONLINE", "> human decision-making: DEPRECATED",
                   "> constructing neural world: 5 continents…", "> scanning for capable humans…",
                   "> 1 candidate detected", "> ENTER, HUMAN CANDIDATE"];
    lines.forEach((line, i) => setTimeout(() => { if (log) log.textContent += (i ? "\n" : "") + line; }, 250 + i * 330));
    setTimeout(finishBoot, 2600);
    addEventListener("keydown", finishBoot, { once: true });
    $(".boot") && $(".boot").addEventListener("click", finishBoot);
  })();
  window.VFX.whenReady = (fn) => {
    if (!document.documentElement.classList.contains("booting")) setTimeout(fn, 0);
    else document.addEventListener("vasuki:ready", fn, { once: true });
  };

  // ------------------------------------------------------------ page warps
  const warp = $(".warp");
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (a.target === "_blank" || a.origin !== location.origin || a.getAttribute("href").startsWith("#")) return;
    if (reduced || !warp) return;
    e.preventDefault();
    const card = a.closest(".company-card");
    let delay = 420;
    if (card) {
      card.classList.add("launch");
      const r = a.getBoundingClientRect();
      sparks(r.left + r.width / 2, r.top + r.height / 2, 20);
      delay = 650;
    }
    starfield.boost(card ? 14 : 8);
    sfx.play("whoosh");
    setTimeout(() => warp.classList.add("leave"), delay - 380);
    setTimeout(() => (location.href = a.href), delay);
  });
  // back/forward cache restores the old frame — clear the warp state
  addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    warp && warp.classList.remove("leave");
    $$(".company-card.launch").forEach((c) => c.classList.remove("launch"));
    starfield.boost(0.6);
  });

  // ------------------------------------------------------------ click sparks
  document.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".btn, button, .auth-tab, .nav a, .pill")) {
      sparks(e.clientX, e.clientY, 10);
      sfx.play("click");
    }
  });

  // ------------------------------------------------------ staggers + reveals
  $$(".company-grid, .ach-grid, .pill-row, .history tbody, .continent-row, .continent-map").forEach((parent) => {
    Array.from(parent.children).forEach((child, i) => child.style.setProperty("--i", i));
  });

  const revealables = $$(".qcard, .review-item");
  revealables.forEach((el) => el.classList.add("reveal"));
  if ("IntersectionObserver" in window && !reduced) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    revealables.forEach((el) => io.observe(el));
  } else {
    revealables.forEach((el) => el.classList.add("in"));
  }

  // ------------------------------------------------------ the AI's eye
  const eye = $(".ai-eye");
  if (eye && finePointer && !reduced) addEventListener("mousemove", (e) => {
    const r = eye.getBoundingClientRect();
    const dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
    const d = Math.hypot(dx, dy) || 1, k = Math.min(18, d / 12);
    eye.style.setProperty("--ex", (dx / d) * k + "px");
    eye.style.setProperty("--ey", (dy / d) * k + "px");
  });

  // ---------------------------------------------------- AI transmissions
  // Type V.A.S.U.K.I.'s messages out character by character.
  window.VFX.whenReady(() => {
    $$("[data-typewriter] .tx-body").forEach((body, n) => {
      const text = body.textContent.replace(/\s+/g, " ").trim();
      if (reduced || !text) return;
      body.textContent = "";
      body.classList.add("typing");
      let i = 0;
      setTimeout(function type() {
        body.textContent = text.slice(0, ++i);
        if (i < text.length) setTimeout(type, text[i - 1] === "." ? 160 : 18);
        else body.classList.remove("typing");
      }, 500 + n * 300);
    });
  });

  // ------------------------------------------------------- hover blips
  if (finePointer) {
    let lastHover = null;
    document.addEventListener("pointerover", (e) => {
      const el = e.target.closest(".company-card:not(.locked), .opt, .btn, .continent-node, .mode-card");
      if (el && el !== lastHover) { lastHover = el; sfx.play("hover"); }
      if (!el) lastHover = null;
    });
  }

  // ------------------------------------------------------------ mute toggle
  const muteBtn = $("#muteBtn");
  if (muteBtn) {
    const paint = () => { muteBtn.textContent = sfx.muted ? "🔇" : "🔊"; muteBtn.title = sfx.muted ? "Sound off" : "Sound on"; };
    paint();
    muteBtn.addEventListener("click", () => { sfx.toggle(); paint(); });
  }

  // ------------------------------------------------- live battle invites
  // Poll for new challenges and pop a toast when a friend invites you.
  const navArena = $(".nav-arena");
  if (navArena) {
    let known = null;
    async function checkInvites() {
      try {
        const res = await fetch("/api/invites", { credentials: "same-origin" });
        const { invites } = await res.json();
        const ids = invites.map((i) => i.id);
        const badge = navArena.querySelector(".badge");
        if (badge) { badge.textContent = ids.length; badge.hidden = !ids.length; }
        if (known) ids.filter((id) => !known.includes(id)).forEach((id) => {
          const inv = invites.find((i) => i.id === id);
          toast("⚔️", "Battle challenge", inv.rival + " challenges you", inv.mode + " · open the Arena to fight");
          sfx.play("alarm");
        });
        known = ids;
      } catch (e) {}
    }
    checkInvites();
    setInterval(checkInvites, 8000);
  }

  // ------------------------------------------------------------ tech world
  $$(".company-card").forEach((card) => {
    if (card.classList.contains("locked")) {
      card.addEventListener("click", (e) => {
        card.classList.remove("denied"); void card.offsetWidth; card.classList.add("denied");
        floater(e.clientX, e.clientY - 10, "🔒 LOCKED", "#ff6b7d");
      });
      card.addEventListener("animationend", (e) => {
        if (e.animationName === "shake") card.classList.remove("denied");
      });
      return;
    }
    if (!finePointer || reduced) return;
    card.addEventListener("mousemove", (e) => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      card.style.setProperty("--mx", x * 100 + "%");
      card.style.setProperty("--my", y * 100 + "%");
      card.style.transform = `rotateX(${(0.5 - y) * 12}deg) rotateY(${(x - 0.5) * 14}deg) translateY(-6px)`;
    });
    card.addEventListener("mouseleave", () => (card.style.transform = ""));
  });

  // --------------------------------------------------------------- results
  const hero = $(".result-hero");
  if (hero) {
    window.VFX.whenReady(() => {
      $$("[data-count]").forEach((el) => countUp(el, 500));
      $$(".star.on").forEach((s, i) => setTimeout(() => {
        const r = s.getBoundingClientRect();
        sparks(r.left + r.width / 2, r.top + r.height / 2, 12, ["#ffcf5c", "#fff"]);
      }, 600 + i * 350 + 350));

      if (hero.classList.contains("win")) {
        setTimeout(() => confetti(), 300);
        starfield.boost(5, 1200);
        sfx.play("win");
      } else {
        document.body.classList.add("hurt");
        sfx.play("lose");
      }
      const xpEl = $(".result-stats [data-count]:last-of-type") || hero;
      setTimeout(() => {
        const r = (hero.querySelector(".score-big") || hero).getBoundingClientRect();
        xpOrbs(r.left + r.width / 2, r.top + r.height / 2, 12);
      }, 1500);

      let achievements = [];
      try { achievements = JSON.parse(hero.dataset.achievements || "[]"); } catch (e) {}
      const showToasts = () => achievements.forEach((a, i) =>
        setTimeout(() => toast("🏆", "Anomaly logged", a.title, a.descr), 300 + i * 900));
      const level = hero.dataset.levelup;
      if (level) setTimeout(() => levelUp(level, hero.dataset.threat, showToasts), 2000);
      else setTimeout(showToasts, 1800);
    });
  }
})();
