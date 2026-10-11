// map.js — the Candy-Crush-style level map on the world page: draws the
// winding road between level nodes, walks a "light" along the cleared part,
// and opens a level card when a node is tapped.
(function () {
  const map = document.getElementById("levelMap");
  if (!map) return;
  const VFX = window.VFX || {};
  const sound = (n, a) => VFX.sfx && VFX.sfx.play(n, a);
  const svg = map.querySelector(".map-road");
  const nodes = Array.from(map.querySelectorAll(".level-node"));
  const NS = "http://www.w3.org/2000/svg";

  // ---- road ---------------------------------------------------------------
  function drawRoad() {
    const box = map.getBoundingClientRect();
    svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
    svg.innerHTML = "";
    const pts = nodes.map((n) => {
      const r = n.getBoundingClientRect();
      return [r.left - box.left + r.width / 2, r.top - box.top + r.height / 2];
    });
    if (pts.length < 2) return;
    let d = `M ${pts[0][0]} ${pts[0][1]}`;
    for (let i = 1; i < pts.length; i++) {
      const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
      const my = (y0 + y1) / 2;
      d += ` C ${x0} ${my}, ${x1} ${my}, ${x1} ${y1}`;
    }
    // full road (dim), then the conquered stretch (glowing)
    const mk = (cls) => { const p = document.createElementNS(NS, "path"); p.setAttribute("d", d); p.setAttribute("class", cls); svg.appendChild(p); return p; };
    mk("road-base");
    mk("road-dash");
    const lit = mk("road-lit");
    const len = lit.getTotalLength();
    const doneCount = nodes.filter((n) => n.classList.contains("done")).length;
    const cur = nodes.findIndex((n) => n.classList.contains("current"));
    const reach = Math.max(doneCount, cur);
    // length up to the reached node
    let reachLen = 0;
    if (reach > 0) {
      const target = pts[Math.min(reach, pts.length - 1)];
      let best = Infinity;
      for (let l = 0; l <= len; l += 4) {
        const p = lit.getPointAtLength(l);
        const dd = Math.hypot(p.x - target[0], p.y - target[1]);
        if (dd < best) { best = dd; reachLen = l; }
      }
    }
    lit.style.strokeDasharray = `${reachLen} ${len}`;
    lit.style.setProperty("--road-len", reachLen);
    // a travelling spark along the conquered road
    if (reachLen > 0 && !VFX.reduced) {
      const spark = document.createElementNS(NS, "circle");
      spark.setAttribute("r", 5);
      spark.setAttribute("class", "road-spark");
      svg.appendChild(spark);
      let t = 0;
      (function run() {
        if (!spark.isConnected) return;
        t = (t + 2.2) % reachLen;
        const p = lit.getPointAtLength(t);
        spark.setAttribute("cx", p.x); spark.setAttribute("cy", p.y);
        requestAnimationFrame(run);
      })();
    }
  }
  drawRoad();
  let rt;
  addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(drawRoad, 120); });

  // scroll the current level into view
  const current = map.querySelector(".level-node.current");
  if (current) setTimeout(() => current.scrollIntoView({ behavior: "smooth", block: "center" }), 1200);

  // ---- level card ---------------------------------------------------------
  const sheet = document.getElementById("levelSheet");
  // Re-parent to <body>: the page's entrance animation gives .container its own
  // stacking context, which would otherwise trap the overlay under the map.
  document.body.appendChild(sheet);
  const $ = (id) => document.getElementById(id);
  function open(node) {
    const d = node.dataset;
    $("lsLevel").textContent = d.level;
    $("lsTier").textContent = d.tier;
    $("lsName").textContent = d.name;
    $("lsBlurb").textContent = d.blurb;
    $("lsDiff").textContent = "AI defence " + "★".repeat(+d.difficulty) + "☆".repeat(3 - d.difficulty);
    $("lsMult").textContent = "×" + d.mult + " XP";
    const stars = $("lsStars");
    stars.innerHTML = "";
    for (let i = 0; i < 3; i++) {
      const s = document.createElement("span");
      s.textContent = "★";
      s.className = i < +d.stars ? "on" : "";
      s.style.setProperty("--i", i);
      stars.appendChild(s);
    }
    const unlocked = d.unlocked === "1";
    $("lsPlay").hidden = !unlocked;
    $("lsPlay").href = d.play;
    renderPaper(d.id);
    $("lsLocked").hidden = unlocked;
    $("lsLocked").textContent = "🔒 Firewall lifts at Level " + d.unlock + ". Earn XP on earlier citadels or in the Arena.";
    $("lsPlay").textContent = +d.stars ? "Replay for more stars ▶" : "Play ▶";
    sheet.hidden = false;
    requestAnimationFrame(() => sheet.classList.add("open"));
    sound("select");
  }
  // This company's own paper: sections (with your accuracy here) + its DSA problems.
  const briefs = JSON.parse((document.getElementById("companyBriefs") || {}).textContent || "{}");
  function renderPaper(id) {
    const box = $("lsPaper");
    box.innerHTML = "";
    const b = briefs[id];
    if (!b) return;
    const head = document.createElement("p");
    head.className = "lp-head";
    head.textContent = (b.pattern === "dsa" ? "DSA pattern" : "MCQ pattern") + " · this company's paper" +
      (b.attempts ? " · best " + b.best_pct + "% in " + b.attempts + " attempt" + (b.attempts > 1 ? "s" : "") : "");
    box.appendChild(head);
    const list = document.createElement("div");
    list.className = "lp-sections";
    b.sections.forEach((s) => {
      const row = document.createElement("div");
      row.className = "lp-row";
      const name = document.createElement("span");
      name.textContent = s.label;
      const w = document.createElement("span");
      w.className = "m-weight";
      w.title = "How much this company tests it";
      for (let i = 0; i < 3; i++) { const bar = document.createElement("i"); if (i < s.weight) bar.className = "on"; w.appendChild(bar); }
      const acc = document.createElement("span");
      acc.className = "lp-acc";
      acc.textContent = s.accuracy === null ? "—" : s.accuracy + "%";
      row.append(name, w, acc);
      list.appendChild(row);
    });
    box.appendChild(list);
    if (b.problems.length) {
      const ph = document.createElement("p");
      ph.className = "lp-head";
      ph.textContent = "Coding problems in this paper";
      box.appendChild(ph);
      b.problems.forEach((p) => {
        const r = document.createElement("div");
        r.className = "lp-problem";
        const lv = document.createElement("span");
        lv.className = "dsa-level level-" + p.level.toLowerCase();
        lv.textContent = p.level;
        const t = document.createElement("span");
        t.textContent = p.title;
        r.append(lv, t);
        box.appendChild(r);
      });
    }
  }

  function close() {
    sheet.classList.remove("open");
    setTimeout(() => (sheet.hidden = true), 250);
  }
  nodes.forEach((n) => n.addEventListener("click", (e) => {
    const r = n.getBoundingClientRect();
    if (VFX.sparks) VFX.sparks(r.left + r.width / 2, r.top + r.height / 2, 14);
    if (n.classList.contains("locked")) {
      n.classList.remove("denied"); void n.offsetWidth; n.classList.add("denied");
      sound("wrong");
    }
    open(n);
  }));
  sheet.addEventListener("click", (e) => { if (e.target === sheet || e.target.closest(".ls-close")) close(); });
  addEventListener("keydown", (e) => { if (e.key === "Escape" && !sheet.hidden) close(); });
})();
