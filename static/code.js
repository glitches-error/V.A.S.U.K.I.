// code.js — the DSA coding editor, used on drive pages and in Prep practice:
// a lightweight textarea editor (tab/auto-indent, line numbers) plus
// "Run sample tests". Each .dsa-card says where to post via data-run-url;
// practice cards also have data-submit-url for a full judged submit.
(function () {
  const cards = document.querySelectorAll(".dsa-card");
  if (!cards.length) return;
  const form = document.getElementById("driveForm");
  const VFX = window.VFX || {};
  const sound = (n, a) => VFX.sfx && VFX.sfx.play(n, a);
  const INDENT = "    ";
  const post = (url, body) => fetch(url, {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }).then((r) => r.json()).catch(() => ({ error: "Could not reach the server." }));

  cards.forEach((card) => {
    const ta = card.querySelector(".ce-input");
    const gutter = card.querySelector(".ce-gutter");
    const out = card.querySelector(".run-output");
    const status = card.querySelector(".run-status");
    const runBtn = card.querySelector(".run-btn");
    const starter = ta.value;
    const storeKey = "vasuki-code-" + card.dataset.store;

    // Restore an unsent draft (per browser) so a refresh doesn't lose work.
    try {
      const draft = localStorage.getItem(storeKey);
      if (draft && draft !== starter) ta.value = draft;
    } catch (e) {}

    function lines() {
      const n = ta.value.split("\n").length;
      gutter.textContent = Array.from({ length: n }, (_, i) => i + 1).join("\n");
      ta.rows = Math.max(10, n + 1);
    }
    function changed() {
      lines();
      const edited = ta.value.trim() !== starter.trim();
      if ((card.dataset.edited === "1") !== edited) {
        card.dataset.edited = edited ? "1" : "0";
        card.classList.toggle("answered", edited);
        document.dispatchEvent(new Event("vasuki:code-edited"));
      }
      try { localStorage.setItem(storeKey, ta.value); } catch (e) {}
    }
    ta.addEventListener("input", changed);
    ta.addEventListener("scroll", () => { gutter.scrollTop = ta.scrollTop; });

    // Editing keys: Tab indents (Shift+Tab dedents), Enter keeps indentation
    // and adds one level after a trailing colon.
    ta.addEventListener("keydown", (e) => {
      const { selectionStart: a, selectionEnd: b, value: v } = ta;
      if (e.key === "Tab") {
        e.preventDefault();
        const lineStart = v.lastIndexOf("\n", a - 1) + 1;
        if (e.shiftKey) {
          const cut = v.slice(lineStart, lineStart + 4).match(/^ */)[0].length;
          ta.setRangeText("", lineStart, lineStart + cut, "end");
          ta.selectionStart = ta.selectionEnd = Math.max(lineStart, a - cut);
        } else {
          ta.setRangeText(INDENT, a, b, "end");
        }
        changed();
      } else if (e.key === "Enter" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        const lineStart = v.lastIndexOf("\n", a - 1) + 1;
        const line = v.slice(lineStart, a);
        let indent = line.match(/^ */)[0];
        if (/:\s*$/.test(line)) indent += INDENT;
        ta.setRangeText("\n" + indent, a, b, "end");
        changed();
      } else if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        runBtn.click();
      }
    });
    card.querySelector(".reset-btn").addEventListener("click", () => {
      if (ta.value !== starter && !confirm("Reset this problem to the starter code?")) return;
      ta.value = starter;
      changed();
      out.hidden = true;
      status.textContent = "";
    });

    runBtn.addEventListener("click", async () => {
      runBtn.disabled = true;
      status.textContent = "Running…";
      status.className = "run-status running";
      const data = await post(card.dataset.runUrl, { qid: card.dataset.qid, code: ta.value });
      runBtn.disabled = false;
      render(data);
    });

    // Practice only: judge against every test (hidden ones too).
    const submitBtn = card.querySelector(".judge-btn");
    if (submitBtn) submitBtn.addEventListener("click", async () => {
      submitBtn.disabled = true;
      status.textContent = "Judging all tests…";
      status.className = "run-status running";
      const data = await post(card.dataset.submitUrl, { code: ta.value });
      submitBtn.disabled = false;
      renderJudge(data);
    });

    function renderJudge(data) {
      if (data.error) return render(data);
      out.hidden = false;
      out.innerHTML = "";
      status.textContent = data.passed + " / " + data.total + " tests passed";
      status.className = "run-status " + (data.solved ? "good" : "bad");
      const row = document.createElement("div");
      row.className = "ro-row " + (data.solved ? "ok" : "fail");
      const head = document.createElement("strong");
      head.textContent = data.solved ? "✓ Accepted — all tests passed" : "✗ " + (data.total - data.passed) + " test(s) failing";
      row.appendChild(head);
      if (data.first_fail) {
        const f = data.first_fail, detail = document.createElement("pre");
        detail.textContent = "input:    " + f.args.map((x) => JSON.stringify(x)).join(", ") +
          "\nexpected: " + JSON.stringify(f.expected) +
          "\n" + (f.error ? "error:    " + f.error : "got:      " + JSON.stringify(f.got));
        row.appendChild(detail);
      } else if (!data.solved) {
        const p = document.createElement("pre");
        p.textContent = "A hidden test failed. Think about edge cases: empty input, duplicates, negatives, large values.";
        row.appendChild(p);
      }
      if (data.approach) {
        const a = document.createElement("p");
        a.className = "ri-explain";
        a.textContent = "💡 Approach: " + data.approach;
        row.appendChild(a);
      }
      out.appendChild(row);
      const b = submitBtn.getBoundingClientRect();
      if (data.solved) {
        sound("win");
        if (VFX.confetti) VFX.confetti(90);
        if (VFX.floater) VFX.floater(b.left + b.width / 2, b.top, data.xp ? "SOLVED +" + data.xp + " XP" : "SOLVED", "#ffcf5c");
        if (data.xp && VFX.xpOrbs) VFX.xpOrbs(b.left + b.width / 2, b.top, 10);
        if (window.Core3D) Core3D.pulse("gold");
        card.classList.add("answered");
      } else {
        sound("wrong");
        if (VFX.shake) VFX.shake(6);
      }
    }

    function render(data) {
      out.hidden = false;
      out.innerHTML = "";
      if (data.error) {
        status.textContent = "Error";
        status.className = "run-status bad";
        const pre = document.createElement("pre");
        pre.className = "ro-error";
        pre.textContent = data.error;
        out.appendChild(pre);
        sound("wrong");
        if (window.Core3D) Core3D.pulse("bad");
        return;
      }
      const passed = data.results.filter((r) => r.ok).length;
      status.textContent = passed + " / " + data.results.length + " samples passed";
      status.className = "run-status " + (passed === data.results.length ? "good" : "bad");
      data.results.forEach((r, i) => {
        const row = document.createElement("div");
        row.className = "ro-row " + (r.ok ? "ok" : "fail");
        const head = document.createElement("strong");
        head.textContent = (r.ok ? "✓ " : "✗ ") + "Sample " + (i + 1);
        row.appendChild(head);
        if (!r.ok) {
          const detail = document.createElement("pre");
          detail.textContent = "input:    " + r.args.map((x) => JSON.stringify(x)).join(", ") +
            "\nexpected: " + JSON.stringify(r.expected) +
            "\n" + (r.error ? "error:    " + r.error : "got:      " + JSON.stringify(r.got));
          row.appendChild(detail);
        }
        out.appendChild(row);
      });
      if (passed === data.results.length) {
        sound("correct", 2);
        const b = runBtn.getBoundingClientRect();
        if (VFX.sparks) VFX.sparks(b.left + b.width / 2, b.top, 16, ["#2ee59d", "#fff"]);
        if (VFX.floater) VFX.floater(b.right + 40, b.top, "SAMPLES PASSED", "#2ee59d");
        if (window.Core3D) Core3D.pulse("good");
      } else {
        sound("wrong");
      }
    }

    // Clear the saved draft once a drive paper is actually submitted.
    if (form) form.addEventListener("submit", () => {
      try { localStorage.removeItem(storeKey); } catch (e) {}
    });

    changed();
  });
})();
