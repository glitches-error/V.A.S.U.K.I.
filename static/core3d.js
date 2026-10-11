// core3d.js — V.A.S.U.K.I.'s "neural core": a rotating 3D wireframe
// icosphere with orbit rings and a serpent coiled around it, rendered on a
// <canvas class="core3d"> with a tiny hand-rolled projector (no libraries).
//
//   <canvas class="core3d" data-mood="calm|alert|hostile" data-size="260"></canvas>
//
// window.Core3D.pulse(kind)  -> "good" | "bad" | "hit" flashes every core.
(function () {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canvases = Array.from(document.querySelectorAll("canvas.core3d"));
  const cores = [];

  // ---- geometry: icosahedron subdivided once, projected onto a sphere ----
  function icosphere() {
    const t = (1 + Math.sqrt(5)) / 2;
    let v = [[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t],
             [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]];
    let f = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4],
             [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8],
             [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]];
    const cache = {};
    const mid = (a, b) => {
      const k = a < b ? a + "_" + b : b + "_" + a;
      if (cache[k] === undefined) {
        cache[k] = v.length;
        v.push([(v[a][0] + v[b][0]) / 2, (v[a][1] + v[b][1]) / 2, (v[a][2] + v[b][2]) / 2]);
      }
      return cache[k];
    };
    const nf = [];
    f.forEach(([a, b, c]) => {
      const ab = mid(a, b), bc = mid(b, c), ca = mid(c, a);
      nf.push([a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]);
    });
    v = v.map(([x, y, z]) => { const l = Math.hypot(x, y, z); return [x / l, y / l, z / l]; });
    const edges = new Set();
    nf.forEach(([a, b, c]) => [[a, b], [b, c], [c, a]].forEach(([p, q]) =>
      edges.add(p < q ? p + "," + q : q + "," + p)));
    return { verts: v, edges: Array.from(edges, (e) => e.split(",").map(Number)) };
  }
  const GEO = icosphere();

  const MOODS = {
    calm:    { a: [46, 229, 157], b: [31, 181, 201], spin: 1 },
    alert:   { a: [255, 207, 92], b: [46, 229, 157], spin: 1.6 },
    hostile: { a: [255, 107, 125], b: [255, 160, 90], spin: 2.2 },
  };
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

  function rotate([x, y, z], ax, ay) {
    let cy = Math.cos(ay), sy = Math.sin(ay);
    [x, z] = [x * cy + z * sy, -x * sy + z * cy];
    const cx = Math.cos(ax), sx = Math.sin(ax);
    [y, z] = [y * cx - z * sx, y * sx + z * cx];
    return [x, y, z];
  }

  function make(canvas) {
    const ctx = canvas.getContext("2d");
    const core = { canvas, ctx, ax: 0.4, ay: 0, tx: 0, ty: 0, flash: 0, flashColor: null, t: 0, shake: 0 };
    function size() {
      const css = parseInt(canvas.dataset.size || "240", 10);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.style.width = canvas.style.height = css + "px";
      canvas.width = canvas.height = css * dpr;
      core.s = css * dpr;
    }
    size();
    canvas.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      core.tx = ((e.clientY - r.top) / r.height - 0.5) * 1.2;
      core.ty = ((e.clientX - r.left) / r.width - 0.5) * 1.6;
    });
    canvas.addEventListener("pointerleave", () => { core.tx = core.ty = 0; });
    canvas.addEventListener("click", () => pulse("good"));
    return core;
  }

  function draw(core, dt) {
    const { ctx, s } = core;
    const mood = MOODS[core.canvas.dataset.mood] || MOODS.calm;
    core.t += dt;
    core.ay += dt * 0.5 * mood.spin + core.ty * dt;
    core.ax += (0.35 + core.tx - core.ax) * 0.05;
    core.flash = Math.max(0, core.flash - dt * 1.8);
    core.shake = Math.max(0, core.shake - dt * 3);

    ctx.clearRect(0, 0, s, s);
    const jitter = core.shake * s * 0.02;
    const cx = s / 2 + (Math.random() - 0.5) * jitter, cy = s / 2 + (Math.random() - 0.5) * jitter;
    const beat = 1 + Math.sin(core.t * 2.4) * 0.025 + core.flash * 0.12;
    const R = s * 0.27 * beat;
    const fov = 3.2;
    const project = ([x, y, z]) => {
      const k = fov / (fov + z);
      return [cx + x * R * k, cy + y * R * k, z];
    };
    const ca = core.flash && core.flashColor ? core.flashColor : mood.a;

    // halo
    const g = ctx.createRadialGradient(cx, cy, R * 0.2, cx, cy, R * 1.9);
    g.addColorStop(0, rgba(ca, 0.28 + core.flash * 0.4));
    g.addColorStop(1, rgba(ca, 0));
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, R * 1.9, 0, Math.PI * 2); ctx.fill();

    // orbit rings (back half first, then sphere, then front half)
    const rings = [[1.45, 0.9, 0.0], [1.7, -0.5, 1.2]].map(([rr, tilt, ph]) => {
      const pts = [];
      for (let i = 0; i <= 72; i++) {
        const a = (i / 72) * Math.PI * 2 + core.t * 0.3 + ph;
        let p = [Math.cos(a) * rr, 0, Math.sin(a) * rr];
        p = rotate(p, tilt, core.ay * 0.3);
        pts.push(project(p));
      }
      return pts;
    });
    const drawRing = (pts, front) => {
      ctx.strokeStyle = rgba(mood.b, front ? 0.55 : 0.18);
      ctx.lineWidth = s * 0.004;
      ctx.beginPath();
      let pen = false;
      pts.forEach(([x, y, z]) => {
        if ((z < 0) === front) { if (!pen) { ctx.moveTo(x, y); pen = true; } else ctx.lineTo(x, y); }
        else pen = false;
      });
      ctx.stroke();
    };
    rings.forEach((r) => drawRing(r, false));

    // sphere wireframe, depth-shaded
    const P = GEO.verts.map((v) => project(rotate(v, core.ax, core.ay)));
    ctx.lineWidth = s * 0.0035;
    GEO.edges.forEach(([i, j]) => {
      const z = (P[i][2] + P[j][2]) / 2;
      const alpha = 0.12 + (1 - (z + 1) / 2) * 0.75;
      ctx.strokeStyle = rgba(z < 0 ? ca : mood.b, alpha);
      ctx.beginPath(); ctx.moveTo(P[i][0], P[i][1]); ctx.lineTo(P[j][0], P[j][1]); ctx.stroke();
    });
    P.forEach(([x, y, z]) => {
      if (z > 0.2) return;
      ctx.fillStyle = rgba(ca, 0.9);
      ctx.beginPath(); ctx.arc(x, y, s * 0.006, 0, Math.PI * 2); ctx.fill();
    });

    // the eye at the centre
    const eyeR = R * (0.22 + core.flash * 0.08);
    const eg = ctx.createRadialGradient(cx, cy, 0, cx, cy, eyeR);
    eg.addColorStop(0, "rgba(255,240,240,1)");
    eg.addColorStop(0.35, "rgba(255,107,125,1)");
    eg.addColorStop(1, "rgba(120,10,30,0)");
    ctx.fillStyle = eg;
    ctx.beginPath(); ctx.arc(cx, cy, eyeR, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#070d0b";
    ctx.beginPath(); ctx.ellipse(cx, cy, eyeR * 0.16, eyeR * 0.5, 0, 0, Math.PI * 2); ctx.fill();

    rings.forEach((r) => drawRing(r, true));

    // serpent: a helix of shrinking segments spiralling around the core
    const segs = 34;
    for (let i = segs - 1; i >= 0; i--) {
      const k = i / segs;
      const a = core.t * 1.4 - k * 5.2;
      const p = project(rotate([Math.cos(a) * 1.22, Math.sin(a * 0.5 + core.t * 0.6) * 0.55,
                                Math.sin(a) * 1.22], core.ax * 0.6, 0));
      const front = p[2] < 0;
      const r = s * (0.022 - k * 0.016) * (front ? 1.1 : 0.85);
      ctx.fillStyle = rgba(i === 0 ? [255, 207, 92] : ca, front ? 0.95 - k * 0.5 : 0.25);
      ctx.beginPath(); ctx.arc(p[0], p[1], Math.max(r, 1), 0, Math.PI * 2); ctx.fill();
    }
  }

  function pulse(kind) {
    const color = kind === "bad" || kind === "hit" ? [255, 107, 125] : kind === "gold" ? [255, 207, 92] : [46, 229, 157];
    cores.forEach((c) => {
      c.flash = 1; c.flashColor = color;
      if (kind === "hit" || kind === "bad") c.shake = 1;
    });
  }

  canvases.forEach((c) => cores.push(make(c)));
  window.Core3D = { pulse };
  if (!cores.length) return;

  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    cores.forEach((c) => draw(c, dt));
    if (!reduced) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
