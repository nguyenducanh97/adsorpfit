/* ==========================================================================
   AdsorpFit: application controller.

   Responsibilities, in order:
     1. boot Pyodide and load the Python engine from /py
     2. build the model picker from the engine's own catalogue
     3. parse pasted / uploaded data
     4. run fits and render results, figures and interpretation
     5. export figures, tables and workbooks

   Nothing is sent anywhere: Pyodide runs entirely in the browser, so the
   data never leaves the machine.
   ========================================================================== */

(function () {
  "use strict";

  let py = null;                     // the Pyodide instance
  let bridge = null;                 // the Python bridge module
  let XLSX_AVAILABLE = false;        // set once openpyxl is confirmed present
  const CATALOGUE = { isotherm: [], kinetics: [] };
  const STATE = {
    kinetics: { data: null, fit: null, advice: null, style: null,
                traceStyle: null, traces: [], diffusion: null },
    isotherm: { data: null, fit: null, advice: null, style: null,
                traceStyle: null, traces: [] },
    thermo: { datasets: [], result: null, style: null, traces: [] },
    projectId: null,
    projectName: ""
  };

  /* ==================================================================== util */

  const $ = function (sel, root) { return (root || document).querySelector(sel); };
  const $$ = function (sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  };

  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "class") n.className = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else if (k === "text") n.textContent = attrs[k];
      else if (k.slice(0, 2) === "on") n[k] = attrs[k];
      else if (attrs[k] !== null && attrs[k] !== undefined) n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      if (c === null || c === undefined) return;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return n;
  }

  function toast(msg, kind, ms) {
    const t = el("div", { class: "toast " + (kind || ""), text: msg });
    $("#toasts").appendChild(t);
    setTimeout(function () {
      t.style.transition = "opacity .3s"; t.style.opacity = "0";
      setTimeout(function () { t.remove(); }, 300);
    }, ms || 4200);
  }

  function fmt(v, sig) {
    sig = sig || 4;
    if (v === null || v === undefined || (typeof v === "number" && !isFinite(v)))
      return "n.d.";
    const a = Math.abs(v);
    if (a === 0) return "0";
    if (a >= 1e5 || a < 1e-3) return v.toExponential(sig - 1);
    return v.toPrecision(sig).replace(/\.?0+$/, "").replace(/\.$/, "");
  }

  // Minimal, safe markdown: **bold**, *italic*, `code`. Everything else is
  // escaped, because interpretation strings are composed from fitted numbers
  // and we never want them parsed as HTML.
  function md(s) {
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  }

  // The Python side takes either a JSON payload string (fit, render_figure, …)
  // or a plain string (list_models, parse_pasted). Stringifying a string would
  // wrap it in quotes and escape its newlines, so pass those through untouched.
  function call(fn, arg) {
    const raw = arg === undefined ? bridge[fn]()
      : bridge[fn](typeof arg === "string" ? arg : JSON.stringify(arg));
    const out = JSON.parse(raw);
    if (!out.ok) {
      console.error(fn, out.error, out.detail);
      throw new Error(out.error);
    }
    return out;
  }

  function theme() { return document.documentElement.getAttribute("data-theme"); }

  /* ------------------------------------------------------------- equations */

  // Render a LaTeX string with KaTeX. Every model carries a proper `equation`
  // field in LaTeX; `equation_plain` is only the ASCII fallback used when
  // KaTeX has not loaded (offline, blocked CDN) or the expression fails to
  // parse: never as the primary display.
  function tex(latex, opts) {
    opts = opts || {};
    if (typeof katex === "undefined" || !latex) return null;
    try {
      return katex.renderToString(latex, {
        displayMode: opts.display !== false,
        throwOnError: false,
        output: "html",
        strict: false,
        trust: false,
        maxSize: 30
      });
    } catch (e) {
      console.warn("KaTeX could not render:", latex, e);
      return null;
    }
  }

  function equationNode(model, opts) {
    opts = opts || {};
    const html = tex(model.equation, opts);
    if (html) {
      return el("div", { class: "equation" + (opts.cls ? " " + opts.cls : ""),
                         html: html });
    }
    return el("div", { class: "equation fallback" + (opts.cls ? " " + opts.cls : ""),
                       text: model.equation_plain });
  }

  function inlineEquation(model) {
    const html = tex(model.equation, { display: false });
    return el("span", { class: "mi-eq", html: html || "" }) ||
           el("span", { class: "mi-eq", text: model.equation_plain });
  }

  /* ==================================================================== boot */

  const BOOT_STEPS = [
    "Downloading the Python runtime…",
    "Loading NumPy and SciPy…",
    "Loading Matplotlib and Pillow…",
    "Loading the AdsorpFit model library…",
    "Ready."
  ];

  function bootMsg(i, extra) {
    $("#boot-msg").textContent = BOOT_STEPS[i] + (extra ? " " + extra : "");
    $("#boot-bar").style.width = ((i + 1) / BOOT_STEPS.length * 100) + "%";
  }

  async function boot() {
    try {
      bootMsg(0);
      py = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
      });

      bootMsg(1);
      await py.loadPackage(["numpy", "scipy"]);

      bootMsg(2);
      await py.loadPackage(["matplotlib", "pillow"]);

      // openpyxl is not a built-in Pyodide package, so it comes from PyPI via
      // micropip. Only the .xlsx export needs it, so a failure here (offline,
      // blocked CDN) must not stop the app starting.
      try {
        await py.loadPackage("micropip");
        const micropip = py.pyimport("micropip");
        await micropip.install("openpyxl");
        XLSX_AVAILABLE = true;
      } catch (e) {
        console.warn("openpyxl unavailable:.xlsx export disabled", e);
        XLSX_AVAILABLE = false;
      }

      bootMsg(3);
      const files = ["core.py", "isotherms.py", "kinetics.py", "thermo.py",
                     "advisor.py", "bridge.py"];
      const sources = await Promise.all(files.map(function (f) {
        return fetch("py/" + f + "?v=" + Date.now()).then(function (r) {
          if (!r.ok) throw new Error("could not load py/" + f + " (" + r.status + ")");
          return r.text();
        });
      }));
      files.forEach(function (f, i) { py.FS.writeFile("/home/pyodide/" + f, sources[i]); });
      py.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
      bridge = py.pyimport("bridge");

      CATALOGUE.isotherm = call("list_models", "isotherm").models;
      CATALOGUE.kinetics = call("list_models", "kinetics").models;

      buildModelPicker("kinetics");
      buildModelPicker("isotherm");
      buildThermoControls();
      buildGuide();

      // Small handle for debugging from the browser console, and for anyone
      // who wants to drive the engine directly rather than through the UI.
      window.AdsorpFit = {
        state: STATE, catalogue: CATALOGUE, call: call,
        pyodide: function () { return py; },
        exportFigure: function (cat, fmt, dpi) {
          return exportFigure(cat, fmt, dpi || 600);
        }
      };

      bootMsg(4);
      setTimeout(function () { $("#boot").classList.add("done"); }, 400);
    } catch (e) {
      console.error(e);
      $("#boot-msg").innerHTML =
        '<strong style="color:#d94f3d">Could not start.</strong><br>' +
        md(String(e.message || e)) +
        '<br><span class="tiny">If you opened this file directly from disk, ' +
        'the browser blocks loading the Python modules. Serve the folder over ' +
        'HTTP instead: for example <code>python -m http.server</code>, or use ' +
        'the published GitHub Pages URL.</span>';
    }
  }

  /* ========================================================== model picker */

  function buildModelPicker(cat) {
    const host = $(cat === "kinetics" ? "#kin-models" : "#iso-models");
    host.innerHTML = "";
    const models = CATALOGUE[cat];
    const groups = {};
    models.forEach(function (m) {
      (groups[m.family] = groups[m.family] || []).push(m);
    });

    const DEFAULT_ON = {
      kinetics: ["pfo", "pso", "elovich", "weber_morris"],
      isotherm: ["langmuir", "freundlich", "temkin", "dubinin_radushkevich", "sips"]
    };

    Object.keys(groups).forEach(function (fam) {
      const g = el("div", { class: "model-group" }, [
        el("div", { class: "gh" }, [
          el("span", { class: "t", text: fam }),
          el("span", { class: "line" })
        ])
      ]);
      groups[fam].forEach(function (m) {
        const cb = el("input", { type: "checkbox", value: m.key });
        if (DEFAULT_ON[cat].indexOf(m.key) >= 0) cb.checked = true;
        cb.dataset.model = m.key;
        const item = el("label", { class: "model-item" }, [
          cb,
          el("span", { class: "mi-body" }, [
            el("span", { class: "mi-name", text: m.name }),
            inlineEquation(m)
          ]),
          el("button", {
            class: "mi-info", type: "button", title: "About this model",
            onclick: function (ev) { ev.preventDefault(); ev.stopPropagation(); showModelInfo(m); }
          }, ["?"])
        ]);
        g.appendChild(item);
      });
      host.appendChild(g);
    });
  }

  function showModelInfo(m) {
    const back = el("div", { class: "modal-back", onclick: function (e) {
      if (e.target === back) back.remove();
    } });
    const body = el("div", { class: "modal-body" }, [
      equationNode(m),
      el("p", { class: "tiny", style: "margin-top:-6px",
                text: m.citation }),
      el("div", { class: "section-title", text: "Parameters" }),
      el("dl", { class: "kv" }, m.params.reduce(function (acc, p) {
        acc.push(el("dt", { text: p.symbol + (p.unit && p.unit !== "–" ? " (" + p.unit + ")" : "") }));
        acc.push(el("dd", { text: p.meaning }));
        return acc;
      }, [])),
      el("div", { class: "section-title", text: "What the model assumes" }),
      el("ul", { class: "interp" }, m.assumptions.map(function (a) {
        return el("li", { html: md(a) });
      })),
      m.linear_forms.length ? el("div", { class: "section-title", text: "Linearised forms" }) : null,
      m.linear_forms.length ? el("ul", { class: "interp" }, m.linear_forms.map(function (lf) {
        return el("li", { html: "<strong>" + lf.name + "</strong>: " +
          md(lf.y_label + " vs " + lf.x_label) + (lf.note ? ". " + md(lf.note) : "") });
      })) : null
    ]);
    back.appendChild(el("div", { class: "modal" }, [
      el("div", { class: "modal-head" }, [
        el("h3", { text: m.name }),
        el("span", { class: "chip info", text: m.n_params + " parameters" }),
        el("button", { class: "icon-btn", style: "margin-left:auto",
                       onclick: function () { back.remove(); }, html: "&times;" })
      ]),
      body
    ]));
    document.body.appendChild(back);
  }

  /* ============================================================ data input */

  function parseInput(text) {
    const r = call("parse_pasted", text);
    return r;
  }

  function readData(cat) {
    const ta = $(cat === "kinetics" ? "#kin-data" : "#iso-data");
    const txt = ta.value.trim();
    if (!txt) { toast("Paste or upload some data first.", "bad"); return null; }
    let p;
    try { p = parseInput(txt); }
    catch (e) { toast("Could not read the data: " + e.message, "bad"); return null; }

    if (p.n_cols < 2) {
      toast("Two columns are needed: x and y.", "bad"); return null;
    }
    const x = p.columns[0], y = p.columns[1];
    const n = Math.min(x.length, y.length);
    const data = {
      x: x.slice(0, n), y: y.slice(0, n),
      yerr: p.n_cols > 2 ? p.columns[2].slice(0, n) : null,
      C0col: p.n_cols > 3 ? p.columns[3].slice(0, n) : null,
      header: p.header, skipped: p.skipped
    };
    if (data.x.some(function (v) { return v === null; }) ||
        data.y.some(function (v) { return v === null; })) {
      toast("Some cells are empty; those rows were dropped.", "warn");
      const keep = [];
      for (let i = 0; i < n; i++) if (data.x[i] !== null && data.y[i] !== null) keep.push(i);
      ["x", "y", "yerr", "C0col"].forEach(function (k) {
        if (data[k]) data[k] = keep.map(function (i) { return data[k][i]; });
      });
    }
    $(cat === "kinetics" ? "#kin-count" : "#iso-count").textContent =
      data.x.length + " points" + (data.skipped ? " (" + data.skipped + " rows skipped)" : "");
    STATE[cat].data = data;
    return data;
  }

  /* ================================================================ fitting */

  // Experimental context shared by the fitter and the advisor, so both judge
  // a model against exactly the same conditions.
  function buildCtx(cat, data) {
    const pref = cat === "kinetics" ? "kin" : "iso";
    const ctx = { T: Number($("#" + pref + "-T").value) || 298.15 };
    if (cat === "kinetics") {
      ctx.C0 = Number($("#kin-C0").value) || null;
      ctx.dose = Number($("#kin-dose").value) || null;
      ctx.particle_radius = Number($("#kin-radius").value) || null;
    } else {
      const mw = Number($("#iso-MW").value);
      if (mw) ctx.MW = mw;
      const cs = Number($("#iso-Cs").value);
      if (cs) ctx.Cs = cs;
      ctx.dose = Number($("#iso-dose").value) || null;
      if (data && data.C0col) ctx.C0_list = data.C0col;
    }
    return ctx;
  }

  async function runFit(cat) {
    const data = readData(cat);
    if (!data) return;

    const pref = cat === "kinetics" ? "kin" : "iso";
    const models = $$('#' + pref + '-models input[type=checkbox]:checked')
      .map(function (c) { return c.value; });
    if (!models.length) { toast("Select at least one model.", "bad"); return; }

    const ctx = buildCtx(cat, data);

    const btn = $("#" + pref + "-run");
    const old = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-inline"></span> Fitting ' + models.length + ' models…';
    await new Promise(function (r) { setTimeout(r, 30); });

    try {
      const res = call("fit", {
        category: cat, x: data.x, y: data.y, models: models, ctx: ctx,
        weights: $("#" + pref + "-weights").value,
        also_linear: $("#" + pref + "-linear").checked,
        criterion: $("#" + pref + "-criterion").value
      });
      STATE[cat].fit = res;
      STATE[cat].frames = null;      // recompute the pinned plot frame

      if (cat === "kinetics") {
        try {
          STATE.kinetics.diffusion = call("diffusion_analysis", {
            t: data.x, q: data.y, segments: 3,
            particle_radius: Number($("#kin-radius").value) || null
          });
        } catch (e) { STATE.kinetics.diffusion = null; }
      }
      renderResults(cat);
      toast(I18N.t("msg.fitted", { n: models.length }), "good");
      scrollToResults(cat);
    } catch (e) {
      toast("Fitting failed: " + e.message, "bad", 8000);
    } finally {
      btn.disabled = false;
      btn.innerHTML = old;
    }
  }

  /* =============================================================== advisor */

  async function runAdvisor(cat) {
    const data = readData(cat);
    if (!data) return;
    const pref = cat === "kinetics" ? "kin" : "iso";
    const btn = document.querySelector('[data-advise="' + cat + '"]');
    const old = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-inline"></span>';
    await new Promise(function (r) { setTimeout(r, 30); });
    try {
      const ctx = buildCtx(cat, data);
      const res = call("advise", {
        category: cat === "kinetics" ? "kinetics" : "isotherm",
        x: data.x, y: data.y, ctx: ctx
      });
      STATE[cat].advice = res;
      renderAdvice(cat);
    } catch (e) {
      toast("Analysis failed: " + e.message, "bad", 7000);
    } finally {
      btn.disabled = false;
      btn.innerHTML = old;
    }
  }

  function renderAdvice(cat) {
    const host = $(cat === "kinetics" ? "#kin-advice" : "#iso-advice");
    const res = STATE[cat].advice;
    host.innerHTML = "";
    if (!res) {
      host.appendChild(el("p", { class: "tiny", style: "margin:0",
                                 text: I18N.t("adv.none") }));
      return;
    }

    host.appendChild(el("p", { class: "tiny", style: "margin:0 0 12px",
                               text: I18N.t("adv.intro") }));

    res.summary.forEach(function (s) {
      host.appendChild(el("div", { class: "callout info" }, [
        el("span", { class: "ci", text: "▸" }),
        el("span", { html: md(s) })
      ]));
    });

    const groups = { recommend: [], usable: [], avoid: [] };
    res.models.forEach(function (m) { groups[m.verdict].push(m); });

    ["recommend", "usable", "avoid"].forEach(function (v) {
      const list = groups[v];
      if (!list.length) return;
      host.appendChild(el("div", { class: "advice-group" }, [
        el("div", { class: "advice-head " + v }, [
          el("span", { class: "dot" }),
          el("span", { text: I18N.t("adv." + v) + " (" + list.length + ")" }),
          el("span", { class: "line" })
        ])
      ].concat(list.map(function (m) {
        const cb = el("input", { type: "checkbox", "data-advice-pick": m.key });
        cb.checked = v === "recommend";
        cb.onchange = function () {
          const target = $$('#' + (cat === "kinetics" ? "kin" : "iso") +
            '-models input[type=checkbox]').find(function (c) {
            return c.value === m.key;
          });
          if (target) target.checked = cb.checked;
        };
        return el("div", { class: "advice-item " + v }, [
          el("div", { class: "ai-top" }, [
            el("span", { class: "ai-name", text: m.name }),
            el("span", { class: "chip", text: m.n_params + "p" }),
            m.R2 !== null && m.R2 !== undefined
              ? el("span", { class: "chip", text: "R² " + fmt(m.R2, 4) }) : null,
            m.delta !== null && m.delta !== undefined
              ? el("span", { class: "chip", text: "Δ " + fmt(m.delta, 3) }) : null,
            el("label", { class: "pick" }, [cb, "select"])
          ]),
          el("ul", { class: "ai-why" }, m.reasons.slice(0, 3).map(function (r) {
            return el("li", { html: md(r) });
          }))
        ]);
      }))));
    });

    host.appendChild(el("div", { class: "btn-row", style: "margin-top:12px" }, [
      el("button", { class: "btn primary sm", text: I18N.t("btn.applyAdvice"),
        onclick: function () { applyAdvice(cat); } }),
      el("button", { class: "btn sm", text: I18N.t("btn.fit"),
        onclick: function () { applyAdvice(cat); runFit(cat); } })
    ]));
  }

  function applyAdvice(cat) {
    const res = STATE[cat].advice;
    if (!res) return;
    const pref = cat === "kinetics" ? "#kin-models" : "#iso-models";
    const wanted = {};
    res.models.forEach(function (m) {
      if (m.verdict === "recommend") wanted[m.key] = true;
    });
    $$(pref + " input[type=checkbox]").forEach(function (c) {
      c.checked = !!wanted[c.value];
    });
    $$('[data-advice-pick]').forEach(function (c) {
      c.checked = !!wanted[c.getAttribute("data-advice-pick")];
    });
    const n = Object.keys(wanted).length;
    toast(n + " recommended model(s) selected.", "good");
  }

  /* ================================================================ issues */

  const ISSUE_ICON = { block: "⛔", warn: "⚠", info: "ℹ" };
  const ISSUE_CLASS = { block: "bad", warn: "warn", info: "info" };

  function issueNode(i, modelName) {
    return el("div", { class: "callout " + ISSUE_CLASS[i.level] + " issue " + i.level }, [
      el("span", { class: "ci", text: ISSUE_ICON[i.level] }),
      el("span", {}, [
        i.level === "block"
          ? el("span", { class: "badge-block", text: I18N.t("issue.block") })
          : (i.level === "warn"
             ? el("span", { class: "badge-warn", text: I18N.t("issue.warn") })
             : null),
        el("span", { html: " " + (modelName ? "<strong>" + modelName + ":</strong> " : "")
                             + md(i.text) })
      ])
    ]);
  }

  function collectIssues(res) {
    const out = [];
    res.results.forEach(function (m) {
      (m.issues || []).forEach(function (i) {
        out.push({ model: m.model_name, issue: i });
      });
    });
    const rank = { block: 0, warn: 1, info: 2 };
    out.sort(function (a, b) { return rank[a.issue.level] - rank[b.issue.level]; });
    return out;
  }

  /* ============================================================== rendering */

  function renderResults(cat) {
    const host = $(cat === "kinetics" ? "#kin-results" : "#iso-results");
    const res = STATE[cat].fit;
    host.innerHTML = "";

    const sub = el("div", { class: "panel" }, [
      el("div", { class: "panel-head" }, [
        el("h2", { text: "Results" }),
        el("span", { class: "hint" }, [
          el("span", { class: "chip info",
            text: res.results.length + " models · " + STATE[cat].data.x.length + " points" })
        ])
      ]),
      el("div", { class: "panel-body", style: "padding-top:12px" }, [
        el("nav", { class: "tabs", id: cat + "-subtabs", style: "margin-bottom:14px" },
          [["overview", "Overview"], ["figures", "Figures"],
           ["params", "Parameters"], ["interp", "Interpretation"],
           cat === "kinetics" ? ["diffusion", "Diffusion"] : null,
           ["linear", "Linear plots"], ["export", "Export"]]
          .filter(Boolean).map(function (t, i) {
            return el("button", {
              role: "tab", "data-sub": t[0], text: t[1],
              "aria-selected": i === 0 ? "true" : "false",
              onclick: function () { showSub(cat, t[0]); }
            });
          })),
        el("div", { id: cat + "-subpanes" })
      ])
    ]);
    host.appendChild(sub);

    const panes = $("#" + cat + "-subpanes");
    panes.appendChild(el("div", { "data-pane": "overview" }, [renderOverview(cat)]));
    panes.appendChild(el("div", { "data-pane": "figures", class: "hidden" }, [renderFigures(cat)]));
    panes.appendChild(el("div", { "data-pane": "params", class: "hidden" }, [renderParams(cat)]));
    panes.appendChild(el("div", { "data-pane": "interp", class: "hidden" }, [renderInterp(cat)]));
    if (cat === "kinetics")
      panes.appendChild(el("div", { "data-pane": "diffusion", class: "hidden" }, [renderDiffusion()]));
    panes.appendChild(el("div", { "data-pane": "linear", class: "hidden" }, [renderLinear(cat)]));
    panes.appendChild(el("div", { "data-pane": "export", class: "hidden" }, [renderExport(cat)]));

    drawMainFigure(cat);
    // the results panel and its plot were just created, so give them their
    // collapse, drag and resize affordances
    Layout.refresh();
  }

  function showSub(cat, name) {
    $$("#" + cat + "-subtabs button").forEach(function (b) {
      b.setAttribute("aria-selected", b.dataset.sub === name ? "true" : "false");
    });
    $$("#" + cat + "-subpanes > div").forEach(function (d) {
      d.classList.toggle("hidden", d.dataset.pane !== name);
    });
    if (name === "figures") {
      setTimeout(function () {
        const d = $("#" + cat + "-plot");
        if (d && d.data) Plotly.Plots.resize(d);
      }, 30);
    }
  }

  /* ---------------------------------------------------------- overview pane */

  function renderOverview(cat) {
    const res = STATE[cat].fit;
    const wrap = el("div");

    res.summary.forEach(function (s) {
      wrap.appendChild(el("div", { class: "callout info" }, [
        el("span", { class: "ci", text: "▸" }),
        el("span", { html: md(s) })
      ]));
    });

    const crit = res.ranking.length ? res.ranking[0].criterion : "AICc";
    const tbl = el("table", { class: "data" }, [
      el("thead", {}, [el("tr", {}, [
        el("th", { text: "#" }), el("th", { text: "Model" }),
        el("th", { class: "num", text: "p" }),
        el("th", { class: "num", text: crit }),
        el("th", { class: "num", text: "Δ" }),
        el("th", { class: "num", text: "weight" }),
        el("th", { class: "num", text: "R²" }),
        el("th", { class: "num", text: "adj R²" }),
        el("th", { class: "num", text: "RMSE" }),
        el("th", { text: "support" })
      ])]),
      el("tbody", {}, res.ranking.map(function (r) {
        const m = res.results.find(function (q) { return q.model_key === r.model_key; });
        const blocked = m && (m.issues || []).some(function (i) {
          return i.level === "block";
        });
        return el("tr", { class: blocked ? "" : (r.rank === 1 ? "best" : "") }, [
          el("td", { class: "num", text: r.rank }),
          el("td", {}, [
            el("span", { text: r.model_name }),
            blocked ? el("span", { class: "badge-block",
                                   style: "margin-left:7px",
                                   text: I18N.t("issue.block") }) : null
          ]),
          el("td", { class: "num", text: r.n_params }),
          el("td", { class: "num", text: fmt(r.value, 5) }),
          el("td", { class: "num", text: fmt(r.delta, 3) }),
          el("td", { class: "num", text: r.weight === null ? "":
                     (r.weight * 100).toFixed(1) + "%" }),
          el("td", { class: "num", text: fmt(r.R2, 5) }),
          el("td", { class: "num", text: fmt(r.adj_R2, 5) }),
          el("td", { class: "num", text: fmt(r.RMSE, 4) }),
          el("td", { class: "tiny", text: r.evidence })
        ]);
      }))
    ]);
    wrap.appendChild(el("div", { class: "table-wrap" }, [tbl]));

    wrap.appendChild(el("p", { class: "tiny", style: "margin-top:10px" , html:
      "<strong>Δ</strong> is the difference in " + crit + " from the best model. " +
      "<strong>weight</strong> is the Akaike weight, the probability that this model " +
      "is the best approximating one <em>among those you fitted</em>. Models within " +
      "Δ &lt; 2 of the leader are not statistically distinguishable from it." }));

    // Domain and validity findings come first: a model that predicts
    // impossible values is a harder problem than a wide confidence interval,
    // and burying it under the statistics is how it gets published.
    const issues = collectIssues(res);
    const blocking = issues.filter(function (r) { return r.issue.level === "block"; });
    if (blocking.length) {
      wrap.appendChild(el("div", { class: "callout bad", style: "font-weight:600" }, [
        el("span", { class: "ci", text: "⛔" }),
        el("span", { html: blocking.length + " of the models you fitted are being "
          + "applied outside their own domain of validity. Their parameters should "
          + "not be reported, regardless of R²." })
      ]));
    }
    if (issues.length) {
      wrap.appendChild(el("div", { class: "section-title",
                                   text: I18N.t("issue.heading") }));
      issues.forEach(function (r) {
        wrap.appendChild(issueNode(r.issue, r.model));
      });
    }

    const allWarn = [];
    res.results.forEach(function (m) {
      (m.warnings || []).forEach(function (w) {
        allWarn.push({ model: m.model_name, text: w });
      });
    });
    if (allWarn.length) {
      wrap.appendChild(el("div", { class: "section-title",
                                   text: "Parameter diagnostics" }));
      allWarn.forEach(function (w) {
        wrap.appendChild(el("div", { class: "callout warn" }, [
          el("span", { class: "ci", text: "⚠" }),
          el("span", { html: "<strong>" + w.model + ":</strong> " + md(w.text) })
        ]));
      });
    }
    return wrap;
  }

  /* ----------------------------------------------------------- figures pane */

  function renderFigures(cat) {
    const st = STATE[cat];
    if (!st.style) {
      st.style = Fig.newStyle(cat === "kinetics"
        ? { x_label: "$t$ (" + $("#kin-tunit").value + ")",
            y_label: "$q_t$ (" + $("#kin-qunit").value + ")",
            legend_loc: "lower right" }
        : { x_label: "$C_e$ (" + $("#iso-cunit").value + ")",
            y_label: "$q_e$ (" + $("#iso-qunit").value + ")",
            legend_loc: "lower right" });
    }

    const modeSel = el("select", { id: cat + "-figmode", onchange: function () {
      drawMainFigure(cat);
    } }, [
      el("option", { value: "fit", text: "Data + fitted curves" }),
      el("option", { value: "residual", text: "Residuals vs x" }),
      el("option", { value: "predobs", text: "Predicted vs observed" })
    ]);

    const traceHost = el("div", { id: cat + "-tracectl" });
    const styleHost = el("div", { class: "style-stack", id: cat + "-stylectl" });

    const left = el("div", {}, [
      el("div", { class: "btn-row", style: "margin-bottom:10px" }, [
        el("span", { class: "mini-label", style: "margin:0", text: "View" }),
        modeSel
      ]),
      el("div", { id: cat + "-plot" }),
      el("div", { class: "section-title", text: "Series appearance" }),
      traceHost
    ]);

    const right = el("div", {}, [styleHost]);
    const shell = el("div", { class: "figure-shell" }, [left, right]);

    setTimeout(function () {
      Fig.buildControls(styleHost, st.style, function () { drawMainFigure(cat); });
      // buildTraceControls establishes the per-series defaults (which curves
      // start visible), so the figure has to be redrawn once they exist.
      buildTraceControls(cat, traceHost);
      drawMainFigure(cat);
      Layout.refresh();
    }, 10);
    return shell;
  }

  function seriesFor(cat) {
    // Which model curves to draw: all successful fits, in ranking order.
    const res = STATE[cat].fit;
    const order = res.ranking.map(function (r) { return r.model_key; });
    return res.results
      .filter(function (m) { return m.success && m.curve; })
      .sort(function (a, b) {
        return order.indexOf(a.model_key) - order.indexOf(b.model_key);
      });
  }

  function buildTraceControls(cat, host) {
    const st = STATE[cat];
    host.innerHTML = "";
    st.traceStyle = st.traceStyle || {};

    function ctl(key, label, defaults) {
      const ts = st.traceStyle[key] = st.traceStyle[key] || Object.assign({}, defaults);
      const row = el("div", { class: "row c4", style: "align-items:end;margin-bottom:8px" }, [
        el("div", {}, [
          el("label", { class: "mini-label", text: label }),
          el("label", { class: "inline-check", style: "margin:0" }, [
            (function () {
              const c = el("input", { type: "checkbox" });
              c.checked = ts.show !== false;
              c.onchange = function () { ts.show = c.checked; drawMainFigure(cat); };
              return c;
            })(), "show"
          ])
        ]),
        (function () {
          const w = el("div", {}, [el("label", { class: "mini-label", text: "colour" })]);
          const i = el("input", { type: "color", value: ts.color });
          i.oninput = function () { ts.color = i.value; drawMainFigure(cat); };
          w.appendChild(i); return w;
        })(),
        (function () {
          const w = el("div", {}, [el("label", { class: "mini-label",
            text: ts.kind === "line" ? "dash" : "symbol" })]);
          const s = el("select");
          const opts = ts.kind === "line"
            ? ["solid", "dash", "dot", "dashdot", "longdash"]
            : Fig.SYMBOL_CYCLE.concat(["circle-open", "square-open", "diamond-open"]);
          opts.forEach(function (o) {
            const op = el("option", { value: o, text: o });
            if ((ts.kind === "line" ? ts.dash : ts.symbol) === o) op.selected = true;
            s.appendChild(op);
          });
          s.onchange = function () {
            if (ts.kind === "line") ts.dash = s.value; else ts.symbol = s.value;
            drawMainFigure(cat);
          };
          w.appendChild(s); return w;
        })(),
        (function () {
          const w = el("div", {}, [el("label", { class: "mini-label",
            text: ts.kind === "line" ? "width" : "size" })]);
          const i = el("input", { type: "number", step: "0.1", min: "0.2", max: "12",
            value: ts.kind === "line" ? ts.line_width : ts.marker_size });
          i.oninput = function () {
            if (ts.kind === "line") ts.line_width = Number(i.value);
            else ts.marker_size = Number(i.value);
            drawMainFigure(cat);
          };
          w.appendChild(i); return w;
        })()
      ]);
      host.appendChild(row);
    }

    ctl("__data__", "Experimental data",
        { kind: "scatter", color: Fig.PALETTE[0], symbol: "circle",
          marker_size: 5, show: true });
    seriesFor(cat).forEach(function (m, i) {
      ctl(m.model_key, m.model_name,
          { kind: "line", color: Fig.PALETTE[(i + 1) % Fig.PALETTE.length],
            dash: "solid", line_width: 1.6, show: i < 4 });
    });
  }

  function buildTraces(cat) {
    const st = STATE[cat];
    const d = st.data;
    const mode = ($("#" + cat + "-figmode") || {}).value || "fit";
    const ts = st.traceStyle || {};
    const out = [];

    // Every series is always emitted, in a fixed order, with `visible` marking
    // whether it is shown. Filtering the array here instead would shift the
    // remaining traces' positions and make Plotly reassign their colours.
    if (mode === "fit") {
      const dt = ts.__data__ || {};
      out.push({
        kind: "scatter", x: d.x, y: d.y, name: "Experimental",
        color: dt.color, symbol: dt.symbol, marker_size: dt.marker_size,
        visible: dt.show !== false,
        yerr: d.yerr && d.yerr.every(function (v) { return v !== null; }) ? d.yerr : null
      });
      seriesFor(cat).forEach(function (m) {
        const s = ts[m.model_key] || {};
        out.push({
          kind: "line", x: m.curve.x, y: m.curve.y, name: m.model_name,
          color: s.color, dash: s.dash, line_width: s.line_width,
          visible: s.show !== false
        });
      });
    } else if (mode === "residual") {
      seriesFor(cat).forEach(function (m) {
        const s = ts[m.model_key] || {};
        out.push({
          kind: "scatter", x: d.x, y: m.residuals, name: m.model_name,
          color: s.color, symbol: s.symbol || "circle", marker_size: 5,
          visible: s.show !== false
        });
      });
      out.push({ kind: "line", x: [Math.min.apply(null, d.x), Math.max.apply(null, d.x)],
                 y: [0, 0], name: "zero", color: "#888888", dash: "dash",
                 line_width: 1 });
    } else {
      const all = [];
      seriesFor(cat).forEach(function (m) {
        const s = ts[m.model_key] || {};
        out.push({ kind: "scatter", x: d.y, y: m.y_cal, name: m.model_name,
                   color: s.color, symbol: s.symbol || "circle", marker_size: 5,
                   visible: s.show !== false });
        if (s.show !== false) all.push.apply(all, m.y_cal.concat(d.y));
      });
      if (all.length) {
        const lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
        out.push({ kind: "line", x: [lo, hi], y: [lo, hi], name: "1:1",
                   color: "#888888", dash: "dash", line_width: 1 });
      }
    }
    return out;
  }

  // The plot frame is computed once per fit from ALL series, then pinned.
  //
  // Without this, Plotly autoranges over only the visible traces, so hiding a
  // model whose curve runs outside the data envelope (Freundlich, Temkin and
  // Halsey have no plateau; Harkins-Jura and BET diverge) rescales both axes
  // and every remaining curve visibly jumps. Models that sit inside the data
  // envelope did not trigger it, which is why it looked intermittent.
  //
  // Curves are allowed to stretch the frame only so far past the measured
  // data. Beyond that they are clipped, so one diverging model cannot flatten
  // every other curve into a horizontal line.
  function computeFrame(cat, mode) {
    const st = STATE[cat];
    const d = st.data;
    if (!d) return null;
    const series = seriesFor(cat);

    function pad(lo, hi, frac) {
      if (!isFinite(lo) || !isFinite(hi)) return null;
      if (hi === lo) { const e = Math.abs(hi || 1) * 0.1; return [lo - e, hi + e]; }
      const m = (hi - lo) * (frac === undefined ? 0.06 : frac);
      return [lo - m, hi + m];
    }

    if (mode === "residual") {
      let m = 0;
      series.forEach(function (s) {
        (s.residuals || []).forEach(function (r) {
          if (isFinite(r)) m = Math.max(m, Math.abs(r));
        });
      });
      m = m || 1;
      return { x: pad(Math.min.apply(null, d.x), Math.max.apply(null, d.x)),
               y: [-m * 1.15, m * 1.15] };
    }

    if (mode === "predobs") {
      const all = d.y.slice();
      series.forEach(function (s) {
        (s.y_cal || []).forEach(function (v) { if (isFinite(v)) all.push(v); });
      });
      const lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
      return { x: pad(lo, hi), y: pad(lo, hi) };
    }

    const xLo = Math.min(0, Math.min.apply(null, d.x));
    const xHi = Math.max.apply(null, d.x);
    const yLo = Math.min.apply(null, d.y);
    const yHi = Math.max.apply(null, d.y);
    const span = (yHi - yLo) || Math.abs(yHi) || 1;
    // How far outside the measured data a curve may push the frame. Kept
    // tight so the data fill the plot: a model that diverges runs off the
    // top, which is both honest and more readable than squashing every
    // other curve to accommodate it.
    const ceiling = yHi + 0.15 * span;
    const floor = yLo - 0.10 * span;

    let lo = yLo, hi = yHi;
    series.forEach(function (s) {
      if (!s.curve) return;
      s.curve.y.forEach(function (v) {
        if (!isFinite(v)) return;
        if (v < hi && v > ceiling) return;
        if (v > lo && v < floor) return;
        if (v <= ceiling && v > hi) hi = v;
        if (v >= floor && v < lo) lo = v;
      });
    });
    return { x: pad(xLo, xHi * 1.03, 0.02), y: pad(lo, hi, 0.06) };
  }

  // After a fit, bring the results into view. On the wide two-column layout
  // the results sit beside the controls, so the page only needs to return to
  // the top; when the columns are stacked they sit below, so scroll to them.
  function scrollToResults(cat) {
    const host = $(cat === "kinetics" ? "#kin-results" : "#iso-results");
    if (!host) return;
    setTimeout(function () {
      const stacked = document.documentElement.getAttribute("data-layout") === "stack"
        || window.matchMedia("(max-width: 1150px)").matches;
      const behavior = Prefs.get("motion") === "off" ? "auto" : "smooth";
      if (stacked) {
        const y = host.getBoundingClientRect().top + window.scrollY - 70;
        window.scrollTo({ top: Math.max(0, y), behavior: behavior });
      } else {
        window.scrollTo({ top: 0, behavior: behavior });
      }
    }, 60);
  }

  function drawMainFigure(cat) {
    const div = $("#" + cat + "-plot");
    if (!div) return;
    const st = STATE[cat];
    const mode = ($("#" + cat + "-figmode") || {}).value || "fit";
    const traces = buildTraces(cat);
    st.traces = traces;

    // Residual and parity views need their own axis labels; keep the user's
    // labels for the main fit view.
    const style = Object.assign({}, st.style);
    if (mode === "residual") {
      style.y_label = "Residual, $q_{obs} - q_{cal}$";
    } else if (mode === "predobs") {
      style.x_label = "Observed $q$"; style.y_label = "Predicted $q$";
    }

    st.frames = st.frames || {};
    if (!st.frames[mode]) st.frames[mode] = computeFrame(cat, mode);
    const frame = st.frames[mode];
    // An explicit range the user typed always wins over the pinned frame.
    if (frame) {
      if (style.x_min === null || style.x_min === undefined || style.x_min === "") {
        style.x_min = frame.x[0]; style.x_max = frame.x[1];
      }
      if (style.y_min === null || style.y_min === undefined || style.y_min === "") {
        style.y_min = frame.y[0]; style.y_max = frame.y[1];
      }
    }

    st.effectiveStyle = style;
    Fig.draw(div.id, traces, style, theme());
  }

  /* ---------------------------------------------------------- params pane */

  function renderParams(cat) {
    const res = STATE[cat].fit;
    const wrap = el("div");
    const order = res.ranking.map(function (r) { return r.model_key; });
    const sorted = res.results.slice().sort(function (a, b) {
      return order.indexOf(a.model_key) - order.indexOf(b.model_key);
    });

    sorted.forEach(function (m, idx) {
      const card = el("div", { class: "result-card" + (idx > 2 ? " collapsed" : "") });
      const head = el("div", { class: "rh", onclick: function () {
        card.classList.toggle("collapsed");
      } }, [
        el("span", { class: "rank", text: String(idx + 1) }),
        el("span", { class: "rname", text: m.model_name }),
        el("span", { class: "rstats" }, [
          el("span", { class: "chip " + (m.stats.R2 > 0.98 ? "good" :
                       m.stats.R2 > 0.9 ? "warn" : "bad"),
                       text: "R² " + fmt(m.stats.R2, 5) }),
          el("span", { class: "chip", text: "RMSE " + fmt(m.stats.RMSE, 4) }),
          el("span", { class: "chip", text: "AICc " + fmt(m.stats.AICc, 5) })
        ])
      ]);
      card.appendChild(head);

      const body = el("div", { class: "rb" });
      if (!m.success) {
        body.appendChild(el("div", { class: "callout bad" }, [
          el("span", { class: "ci", text: "✕" }),
          el("span", { text: "This model did not converge. " + m.message })
        ]));
        card.appendChild(body);
        wrap.appendChild(card);
        return;
      }

      body.appendChild(equationNode(m));

      (m.issues || []).forEach(function (i) {
        body.appendChild(issueNode(i, null));
      });

      body.appendChild(el("div", { class: "table-wrap" }, [
        el("table", { class: "data" }, [
          el("thead", {}, [el("tr", {}, [
            el("th", { text: "Parameter" }), el("th", { text: "Unit" }),
            el("th", { class: "num", text: "Value" }),
            el("th", { class: "num", text: "Std. error" }),
            el("th", { class: "num", text: "95% CI" }),
            el("th", { class: "num", text: "t" }),
            el("th", { class: "num", text: "p" })
          ])]),
          el("tbody", {}, m.param_meta.map(function (p) {
            const v = m.params[p.key], se = m.stderr[p.key], ci = m.ci95[p.key];
            const pv = m.pvalue[p.key];
            return el("tr", {}, [
              el("td", { text: p.symbol }),
              el("td", { class: "tiny", text: p.unit }),
              el("td", { class: "num", text: fmt(v, 5) }),
              el("td", { class: "num", text: fmt(se, 3) }),
              el("td", { class: "num", text: ci && ci[0] !== null
                ? fmt(ci[0], 4) + " … " + fmt(ci[1], 4) : "n.d." }),
              el("td", { class: "num", text: fmt(m.tvalue[p.key], 3) }),
              el("td", { class: "num", text: pv === null ? "n.d." :
                         (pv < 0.0001 ? "<0.0001" : pv.toFixed(4)) })
            ]);
          }))
        ])
      ]));

      if (Object.keys(m.derived || {}).length) {
        body.appendChild(el("div", { class: "section-title", text: "Derived quantities" }));
        const dl = el("dl", { class: "kv" });
        Object.keys(m.derived).forEach(function (k) {
          const v = m.derived[k];
          dl.appendChild(el("dt", { text: k.replace(/_/g, " ") }));
          dl.appendChild(el("dd", { text: Array.isArray(v)
            ? v.map(function (q) { return fmt(q, 4); }).join(", ")
            : fmt(v, 5) }));
        });
        body.appendChild(dl);
      }

      body.appendChild(el("div", { class: "section-title", text: "Goodness of fit" }));
      const S = m.stats;
      const statRows = [
        ["R²", S.R2], ["adjusted R²", S.adj_R2], ["RMSE", S.RMSE],
        ["SSE", S.SSE], ["χ²", S.chi2], ["reduced χ²", S.chi2_red],
        ["ARE (%)", S.ARE], ["HYBRID", S.HYBRID], ["MPSD (%)", S.MPSD],
        ["EABS", S.EABS], ["MAE", S.MAE], ["Δq (%)", S.delta_q],
        ["AIC", S.AIC], ["AICc", S.AICc], ["BIC", S.BIC]
      ];
      body.appendChild(el("div", { class: "table-wrap" }, [
        el("table", { class: "data" }, [
          el("tbody", {}, chunk(statRows, 3).map(function (row) {
            const cells = [];
            row.forEach(function (r) {
              cells.push(el("td", { class: "tiny", text: r[0] }));
              cells.push(el("td", { class: "num", text: fmt(r[1], 5) }));
            });
            return el("tr", {}, cells);
          }))
        ])
      ]));

      body.appendChild(el("p", { class: "tiny", style: "margin-top:10px",
                                text: "Reference: " + m.citation }));
      card.appendChild(body);
      wrap.appendChild(card);
    });
    return wrap;
  }

  function chunk(arr, n) {
    const out = [];
    for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n));
    return out;
  }

  /* ------------------------------------------------------ interpretation */

  function renderInterp(cat) {
    const res = STATE[cat].fit;
    const wrap = el("div");
    const order = res.ranking.map(function (r) { return r.model_key; });
    res.results.slice().sort(function (a, b) {
      return order.indexOf(a.model_key) - order.indexOf(b.model_key);
    }).forEach(function (m, i) {
      if (!m.success || !m.interpretation) return;
      const card = el("div", { class: "result-card" + (i > 1 ? " collapsed" : "") });
      card.appendChild(el("div", { class: "rh", onclick: function () {
        card.classList.toggle("collapsed");
      } }, [
        el("span", { class: "rank", text: String(i + 1) }),
        el("span", { class: "rname", text: m.model_name }),
        el("span", { class: "rstats" }, [
          el("span", { class: "chip", text: "R² " + fmt(m.stats.R2, 4) })
        ])
      ]));
      const blockers = (m.issues || []).filter(function (i) {
        return i.level === "block";
      });
      card.appendChild(el("div", { class: "rb" },
        blockers.map(function (i) { return issueNode(i, null); }).concat([
        blockers.length ? el("p", { class: "tiny", style: "margin:0 0 12px",
          text: "The interpretation below is generated from parameters that fall "
              + "outside this model's valid range. It is shown for completeness "
              + "only; do not quote it." }): null,
        el("ul", { class: "interp" }, m.interpretation.map(function (s) {
          return el("li", { html: md(s) });
        })),
        el("div", { class: "section-title", text: "Model assumptions you are accepting" }),
        el("ul", { class: "interp" }, m.assumptions.map(function (a) {
          return el("li", { html: md(a) });
        }))
      ])));
      wrap.appendChild(card);
    });
    return wrap;
  }

  /* ---------------------------------------------------------- diffusion */

  function renderDiffusion() {
    const d = STATE.kinetics.diffusion;
    const wrap = el("div");
    if (!d) {
      wrap.appendChild(el("div", { class: "empty", html:
        '<div class="big">◌</div>Diffusion analysis is unavailable for these data.' }));
      return wrap;
    }

    wrap.appendChild(el("div", { class: "section-title",
      text: "Weber–Morris multi-region analysis" }));
    wrap.appendChild(el("div", { class: "callout info" }, [
      el("span", { class: "ci", text: "▸" }),
      el("span", { html: md(d.weber_morris.note) })
    ]));

    wrap.appendChild(el("div", { class: "table-wrap" }, [
      el("table", { class: "data" }, [
        el("thead", {}, [el("tr", {}, [
          el("th", { text: "Stage" }), el("th", { text: "Interpretation" }),
          el("th", { class: "num", text: "k_id" }), el("th", { class: "num", text: "C" }),
          el("th", { class: "num", text: "R²" }), el("th", { class: "num", text: "n" })
        ])]),
        el("tbody", {}, d.weber_morris.segments.map(function (s) {
          return el("tr", {}, [
            el("td", { class: "num", text: s.stage }),
            el("td", { class: "tiny", text: s.label }),
            el("td", { class: "num", text: fmt(s.kid, 4) + " ± " + fmt(s.kid_se, 2) }),
            el("td", { class: "num", text: fmt(s.C, 4) + " ± " + fmt(s.C_se, 2) }),
            el("td", { class: "num", text: fmt(s.R2, 5) }),
            el("td", { class: "num", text: s.n_points })
          ]);
        }))
      ])
    ]));

    wrap.appendChild(el("div", { id: "wm-plot", style: "margin-top:14px" }));

    if (d.boyd && d.boyd.t) {
      wrap.appendChild(el("div", { class: "section-title", text: "Boyd plot" }));
      wrap.appendChild(el("div", { class: "callout " +
        (d.boyd.through_origin ? "good" : "warn") }, [
        el("span", { class: "ci", text: d.boyd.through_origin ? "✓" : "⚠" }),
        el("span", { html: md(d.boyd.interpretation) })
      ]));
      wrap.appendChild(el("div", { id: "boyd-plot" }));
    }

    setTimeout(function () {
      const segTraces = [];
      d.weber_morris.segments.forEach(function (s, i) {
        segTraces.push({ kind: "scatter", x: s.x, y: s.y,
          name: "stage " + s.stage, color: Fig.PALETTE[i % Fig.PALETTE.length],
          symbol: Fig.SYMBOL_CYCLE[i % Fig.SYMBOL_CYCLE.length], marker_size: 5.5 });
        const x0 = Math.min.apply(null, s.x), x1 = Math.max.apply(null, s.x);
        segTraces.push({ kind: "line", x: [x0, x1],
          y: [s.kid * x0 + s.C, s.kid * x1 + s.C],
          name: "fit " + s.stage, color: Fig.PALETTE[i % Fig.PALETTE.length],
          dash: "dash", line_width: 1.4 });
      });
      Fig.draw("wm-plot", segTraces, Fig.newStyle({
        x_label: "$t^{1/2}$ (min$^{1/2}$)",
        y_label: "$q_t$ (mg g$^{-1}$)", legend_loc: "lower right"
      }), theme());

      if (d.boyd && d.boyd.t) {
        const b = d.boyd;
        const x0 = Math.min.apply(null, b.t), x1 = Math.max.apply(null, b.t);
        Fig.draw("boyd-plot", [
          { kind: "scatter", x: b.t, y: b.Bt, name: "B·t", color: Fig.PALETTE[0],
            symbol: "circle", marker_size: 5.5 },
          { kind: "line", x: [x0, x1],
            y: [b.slope * x0 + b.intercept, b.slope * x1 + b.intercept],
            name: "linear fit (R² = " + fmt(b.R2, 4) + ")",
            color: Fig.PALETTE[1], dash: "dash", line_width: 1.4 }
        ], Fig.newStyle({ x_label: "$t$ (min)", y_label: "$B_t$",
                          legend_loc: "upper left" }), theme());
      }
    }, 40);

    return wrap;
  }

  /* ------------------------------------------------------- linear plots */

  function renderLinear(cat) {
    const res = STATE[cat].fit;
    const wrap = el("div");
    const any = res.results.some(function (m) { return m.linear && m.linear.length; });
    if (!any) {
      wrap.appendChild(el("div", { class: "empty", html:
        '<div class="big">◌</div>Linearised fits were not requested, or none of the ' +
        'selected models has a classical linear form.' }));
      return wrap;
    }

    wrap.appendChild(el("div", { class: "callout warn" }, [
      el("span", { class: "ci", text: "⚠" }),
      el("span", { html: md(
        "Linearised fits are shown for comparison with the older literature, not " +
        "because they are better. Transforming the data changes which points " +
        "dominate the regression, so the parameters below generally differ from " +
        "the non-linear ones: and the R² of a linear plot is not comparable with " +
        "the R² of a non-linear fit. Where the two disagree, report the non-linear " +
        "result.") })
    ]));

    res.results.forEach(function (m) {
      if (!m.linear || !m.linear.length) return;
      const card = el("div", { class: "result-card collapsed" });
      card.appendChild(el("div", { class: "rh", onclick: function () {
        card.classList.toggle("collapsed");
        setTimeout(function () {
          m.linear.forEach(function (lf, j) {
            const id = "lin-" + m.model_key + "-" + j;
            const node = document.getElementById(id);
            if (node && lf.plot) {
              const x0 = Math.min.apply(null, lf.plot.x);
              const x1 = Math.max.apply(null, lf.plot.x);
              Fig.draw(id, [
                { kind: "scatter", x: lf.plot.x, y: lf.plot.y, name: "transformed data",
                  color: Fig.PALETTE[0], symbol: "circle", marker_size: 5.5 },
                { kind: "line", x: [x0, x1],
                  y: [lf.plot.slope * x0 + lf.plot.intercept,
                      lf.plot.slope * x1 + lf.plot.intercept],
                  name: "R² = " + fmt(lf.plot.R2, 5),
                  color: Fig.PALETTE[1], dash: "dash", line_width: 1.5 }
              ], Fig.newStyle({ x_label: lf.x_label, y_label: lf.y_label,
                                legend_loc: "best", height_cm: 6 }), theme());
            }
          });
        }, 30);
      } }, [
        el("span", { class: "rank", text: "≡" }),
        el("span", { class: "rname", text: m.model_name }),
        el("span", { class: "rstats" }, [
          el("span", { class: "chip info", text: m.linear.length + " linear form(s)" })
        ])
      ]));

      const body = el("div", { class: "rb" });
      m.linear.forEach(function (lf, j) {
        body.appendChild(el("div", { class: "section-title",
          text: lf.form_name + "" + lf.y_label + " vs " + lf.x_label }));
        if (lf.note) {
          body.appendChild(el("p", { class: "tiny", html: md(lf.note) }));
        }
        if (lf.success) {
          const nonlin = m.params;
          body.appendChild(el("div", { class: "table-wrap" }, [
            el("table", { class: "data" }, [
              el("thead", {}, [el("tr", {}, [
                el("th", { text: "Parameter" }),
                el("th", { class: "num", text: "Linear" }),
                el("th", { class: "num", text: "Non-linear" }),
                el("th", { class: "num", text: "difference" })
              ])]),
              el("tbody", {}, m.param_meta.map(function (p) {
                const a = lf.params[p.key], b = nonlin[p.key];
                const diff = (a !== null && b) ? (100 * (a - b) / b) : null;
                return el("tr", {}, [
                  el("td", { text: p.symbol }),
                  el("td", { class: "num", text: fmt(a, 5) }),
                  el("td", { class: "num", text: fmt(b, 5) }),
                  el("td", { class: "num", text: diff === null ? "":
                             (diff > 0 ? "+" : "") + diff.toFixed(1) + "%" })
                ]);
              }))
            ])
          ]));
          body.appendChild(el("p", { class: "tiny", text:
            "R² of the linear plot = " + fmt(lf.stats.R2_linear, 5) +
            "; the same parameters reproduce the raw data with R² = " +
            fmt(lf.stats.R2, 5) + "." }));
          (lf.warnings || []).forEach(function (w) {
            body.appendChild(el("div", { class: "callout warn" }, [
              el("span", { class: "ci", text: "⚠" }), el("span", { html: md(w) })
            ]));
          });
          body.appendChild(el("div", { id: "lin-" + m.model_key + "-" + j,
                                       style: "margin-bottom:16px" }));
        } else {
          body.appendChild(el("div", { class: "callout bad" }, [
            el("span", { class: "ci", text: "✕" }), el("span", { text: lf.message })
          ]));
        }
      });
      card.appendChild(body);
      wrap.appendChild(card);
    });
    return wrap;
  }

  /* ------------------------------------------------------------- export */

  const IMAGE_FORMATS = [
    ["png", "PNG: raster, lossless, universal"],
    ["tiff", "TIFF: LZW compressed, the Elsevier/Wiley standard for line art"],
    ["pdf", "PDF: vector, editable, best for LaTeX"],
    ["svg", "SVG: vector, editable in Illustrator or Inkscape"],
    ["eps", "EPS: vector PostScript, required by some older journals"],
    ["ps", "PS: PostScript"],
    ["jpg", "JPEG: lossy; only for photographs, not line art"],
    ["webp", "WebP: modern raster, good for web supplements"],
    ["bmp", "BMP: uncompressed raster"]
  ];

  const TABLE_FORMATS = [
    ["csv", "CSV: comma separated"],
    ["tsv", "TSV: tab separated, pastes straight into Excel"],
    ["xlsx", "XLSX: formatted Excel workbook, one sheet per table"],
    ["markdown", "Markdown: for GitHub or notebooks"],
    ["latex", "LaTeX: a complete table environment"],
    ["html", "HTML: for Word via paste"],
    ["json", "JSON: the full result object"]
  ];

  function renderExport(cat) {
    const wrap = el("div");

    wrap.appendChild(el("div", { class: "section-title", text: "Figure" }));
    const fmtSel = el("select", { id: cat + "-imgfmt" },
      IMAGE_FORMATS.map(function (f) {
        return el("option", { value: f[0], text: f[1] });
      }));
    const dpiSel = el("select", { id: cat + "-imgdpi" },
      [150, 300, 600, 900, 1200].map(function (d) {
        const o = el("option", { value: d, text: d + " dpi" });
        if (d === 600) o.selected = true;
        return o;
      }));
    wrap.appendChild(el("div", { class: "row c2" }, [
      el("label", { class: "field" }, [
        el("span", { class: "lbl", text: "Format" }), fmtSel]),
      el("label", { class: "field" }, [
        el("span", { class: "lbl", text: "Resolution" }), dpiSel])
    ]));
    wrap.appendChild(el("p", { class: "tiny", html:
      "The export is rendered by Matplotlib using exactly the style settings on " +
      "the Figures tab: it is not a screenshot of the preview. Vector formats " +
      "(PDF, SVG, EPS, PS) ignore the resolution setting because they have no " +
      "pixels; set it for the raster formats." }));
    wrap.appendChild(el("div", { class: "btn-row", style: "margin:10px 0 22px" }, [
      el("button", { class: "btn primary", onclick: function () {
        exportFigure(cat, fmtSel.value, Number(dpiSel.value));
      } }, ["Download figure"]),
      el("button", { class: "btn", onclick: function () {
        exportAllFormats(cat, Number(dpiSel.value));
      } }, ["Download every format"])
    ]));

    wrap.appendChild(el("div", { class: "section-title", text: "Results tables" }));
    const tfmt = el("select", { id: cat + "-tabfmt" },
      TABLE_FORMATS
        .filter(function (f) { return f[0] !== "xlsx" || XLSX_AVAILABLE; })
        .map(function (f) {
          return el("option", { value: f[0], text: f[1] });
        }));
    wrap.appendChild(el("label", { class: "field" }, [
      el("span", { class: "lbl", text: "Format" }), tfmt]));
    wrap.appendChild(el("div", { class: "btn-row", style: "margin:10px 0 22px" }, [
      el("button", { class: "btn primary", onclick: function () {
        exportTable(cat, tfmt.value);
      } }, ["Download table"]),
      el("button", { class: "btn", onclick: function () {
        exportTable(cat, tfmt.value, true);
      } }, ["Copy to clipboard"])
    ]));

    wrap.appendChild(el("div", { class: "section-title", text: "Plot data" }));
    wrap.appendChild(el("p", { class: "tiny", html:
      "Exports the experimental points and every fitted curve as x,y columns, so " +
      "you can rebuild the figure in Origin, GraphPad or Excel if a coauthor " +
      "insists on it." }));
    wrap.appendChild(el("div", { class: "btn-row", style: "margin-top:10px" }, [
      el("button", { class: "btn", onclick: function () { exportCurves(cat); } },
        ["Download curve data (CSV)"]),
      el("button", { class: "btn", onclick: function () { exportReport(cat); } },
        ["Download full report (HTML)"])
    ]));
    return wrap;
  }

  function download(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = el("a", { href: url, download: name });
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 200);
  }

  function b64ToBlob(b64, mime) {
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return new Blob([arr], { type: mime });
  }

  async function exportFigure(cat, format, dpi) {
    try {
      const st = STATE[cat];
      const style = Object.assign({}, st.effectiveStyle || st.style, { dpi: dpi });
      const payload = Fig.toMatplotlib(st.traces, style, format);
      payload.dpi = dpi;
      toast("Rendering " + format.toUpperCase() + " at " + dpi + " dpi…");
      const r = call("render_figure", payload);
      download(b64ToBlob(r.data, r.mime), "adsorpfit-" + cat + "." + r.format);
      toast("Downloaded.", "good");
    } catch (e) {
      toast("Export failed: " + e.message, "bad", 7000);
    }
  }

  async function exportAllFormats(cat, dpi) {
    for (const f of IMAGE_FORMATS) {
      // BMP is enormous and rarely wanted; skip it in the bulk export.
      if (f[0] === "bmp") continue;
      await exportFigure(cat, f[0], dpi);
      await new Promise(function (r) { setTimeout(r, 350); });
    }
  }

  function paramRows(cat) {
    const res = STATE[cat].fit;
    const order = res.ranking.map(function (r) { return r.model_key; });
    const rows = [];
    res.results.slice().sort(function (a, b) {
      return order.indexOf(a.model_key) - order.indexOf(b.model_key);
    }).forEach(function (m) {
      if (!m.success) return;
      m.param_meta.forEach(function (p) {
        rows.push({
          model: m.model_name, parameter: p.symbol, unit: p.unit,
          value: m.params[p.key], stderr: m.stderr[p.key],
          ci_low: m.ci95[p.key] ? m.ci95[p.key][0] : null,
          ci_high: m.ci95[p.key] ? m.ci95[p.key][1] : null,
          R2: m.stats.R2, adj_R2: m.stats.adj_R2, RMSE: m.stats.RMSE,
          chi2: m.stats.chi2, AICc: m.stats.AICc, BIC: m.stats.BIC
        });
      });
    });
    return rows;
  }

  const PARAM_COLS = [
    { key: "model", label: "Model" }, { key: "parameter", label: "Parameter" },
    { key: "unit", label: "Unit" }, { key: "value", label: "Value" },
    { key: "stderr", label: "Std. error" },
    { key: "ci_low", label: "95% CI low" }, { key: "ci_high", label: "95% CI high" },
    { key: "R2", label: "R²" }, { key: "adj_R2", label: "adj. R²" },
    { key: "RMSE", label: "RMSE" }, { key: "chi2", label: "χ²" },
    { key: "AICc", label: "AICc" }, { key: "BIC", label: "BIC" }
  ];

  function exportTable(cat, format, toClipboard) {
    try {
      const rows = paramRows(cat);
      if (format === "json") {
        const txt = JSON.stringify(STATE[cat].fit, null, 2);
        if (toClipboard) { navigator.clipboard.writeText(txt); toast("Copied.", "good"); }
        else download(new Blob([txt], { type: "application/json" }),
                      "adsorpfit-" + cat + ".json");
        return;
      }
      if (format === "xlsx") {
        const r = call("export_xlsx", {
          sheets: [
            { name: "Parameters",
              columns: PARAM_COLS.map(function (c) { return c.label; }),
              rows: rows.map(function (row) {
                return PARAM_COLS.map(function (c) { return row[c.key]; });
              }) },
            { name: "Ranking",
              columns: ["Rank", "Model", "p", "Criterion", "Value", "Delta",
                        "Weight", "R2", "adj R2", "RMSE"],
              rows: STATE[cat].fit.ranking.map(function (r2) {
                return [r2.rank, r2.model_name, r2.n_params, r2.criterion,
                        r2.value, r2.delta, r2.weight, r2.R2, r2.adj_R2, r2.RMSE];
              }) },
            { name: "Raw data",
              columns: ["x", "y"],
              rows: STATE[cat].data.x.map(function (v, i) {
                return [v, STATE[cat].data.y[i]];
              }) }
          ]
        });
        download(b64ToBlob(r.data, r.mime), "adsorpfit-" + cat + ".xlsx");
        toast("Workbook downloaded.", "good");
        return;
      }
      const r = call("export_table", {
        rows: rows, columns: PARAM_COLS, format: format,
        caption: "Fitted " + cat + " model parameters (AdsorpFit)"
      });
      if (toClipboard) { navigator.clipboard.writeText(r.text); toast("Copied.", "good"); }
      else {
        const ext = { markdown: "md", latex: "tex", html: "html" }[format] || format;
        download(new Blob([r.text], { type: "text/plain" }),
                 "adsorpfit-" + cat + "." + ext);
      }
    } catch (e) {
      toast("Export failed: " + e.message, "bad", 7000);
    }
  }

  function exportCurves(cat) {
    const st = STATE[cat];
    const lines = [];
    lines.push("# AdsorpFit curve export");
    lines.push("# experimental data");
    lines.push("x,y");
    st.data.x.forEach(function (v, i) { lines.push(v + "," + st.data.y[i]); });
    seriesFor(cat).forEach(function (m) {
      lines.push("");
      lines.push("# " + m.model_name);
      lines.push("x," + m.model_key);
      m.curve.x.forEach(function (v, i) { lines.push(v + "," + m.curve.y[i]); });
    });
    download(new Blob([lines.join("\n")], { type: "text/csv" }),
             "adsorpfit-" + cat + "-curves.csv");
  }

  function exportReport(cat) {
    const res = STATE[cat].fit;
    const esc = function (s) {
      return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    };
    const parts = [
      "<!DOCTYPE html><html><head><meta charset='utf-8'>",
      "<title>AdsorpFit report" + cat + "</title><style>",
      "body{font:14px/1.65 system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;color:#12303c}",
      "h1{font-size:24px}h2{font-size:18px;margin-top:32px;border-bottom:2px solid #cfe0e8;padding-bottom:6px}",
      "h3{font-size:15px;margin-top:22px}table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0}",
      "th,td{border:1px solid #cfe0e8;padding:6px 9px;text-align:left}th{background:#eef6f9}",
      "li{margin-bottom:8px}code{background:#eef6f9;padding:1px 5px;border-radius:3px}",
      ".eq{background:#f4fafc;border:1px solid #cfe0e8;padding:10px;text-align:center;font-family:Georgia,serif}",
      "</style></head><body>",
      "<h1>AdsorpFit report" + cat + "</h1>",
      "<p>Generated " + new Date().toLocaleString() + ". " +
      res.results.length + " models fitted to " + STATE[cat].data.x.length +
      " data points by non-linear least squares.</p>",
      "<h2>Model comparison</h2><table><tr><th>#</th><th>Model</th><th>p</th>" +
      "<th>" + (res.ranking[0] || {}).criterion + "</th><th>Δ</th><th>weight</th>" +
      "<th>R²</th><th>RMSE</th></tr>"
    ];
    res.ranking.forEach(function (r) {
      parts.push("<tr><td>" + r.rank + "</td><td>" + esc(r.model_name) + "</td><td>" +
        r.n_params + "</td><td>" + fmt(r.value, 5) + "</td><td>" + fmt(r.delta, 3) +
        "</td><td>" + (r.weight * 100).toFixed(1) + "%</td><td>" + fmt(r.R2, 5) +
        "</td><td>" + fmt(r.RMSE, 4) + "</td></tr>");
    });
    parts.push("</table>");
    res.summary.forEach(function (s) {
      parts.push("<p>" + md(s) + "</p>");
    });

    const order = res.ranking.map(function (r) { return r.model_key; });
    res.results.slice().sort(function (a, b) {
      return order.indexOf(a.model_key) - order.indexOf(b.model_key);
    }).forEach(function (m) {
      if (!m.success) return;
      parts.push("<h2>" + esc(m.model_name) + "</h2>");
      parts.push("<div class='eq'>" + esc(m.equation_plain) + "</div>");
      parts.push("<p><em>" + esc(m.citation) + "</em></p>");
      parts.push("<table><tr><th>Parameter</th><th>Unit</th><th>Value</th>" +
                 "<th>Std. error</th><th>95% CI</th></tr>");
      m.param_meta.forEach(function (p) {
        const ci = m.ci95[p.key];
        parts.push("<tr><td>" + esc(p.symbol) + "</td><td>" + esc(p.unit) +
          "</td><td>" + fmt(m.params[p.key], 5) + "</td><td>" +
          fmt(m.stderr[p.key], 3) + "</td><td>" +
          (ci && ci[0] !== null ? fmt(ci[0], 4) + " … " + fmt(ci[1], 4) : "n.d.") +
          "</td></tr>");
      });
      parts.push("</table>");
      parts.push("<p><strong>R²</strong> " + fmt(m.stats.R2, 5) +
        " · <strong>adj. R²</strong> " + fmt(m.stats.adj_R2, 5) +
        " · <strong>RMSE</strong> " + fmt(m.stats.RMSE, 4) +
        " · <strong>χ²</strong> " + fmt(m.stats.chi2, 4) +
        " · <strong>AICc</strong> " + fmt(m.stats.AICc, 5) + "</p>");
      if (m.interpretation) {
        parts.push("<h3>Interpretation</h3><ul>");
        m.interpretation.forEach(function (s) { parts.push("<li>" + md(s) + "</li>"); });
        parts.push("</ul>");
      }
      parts.push("<h3>Assumptions</h3><ul>");
      m.assumptions.forEach(function (s) { parts.push("<li>" + esc(s) + "</li>"); });
      parts.push("</ul>");
    });
    parts.push("</body></html>");
    download(new Blob([parts.join("\n")], { type: "text/html" }),
             "adsorpfit-" + cat + "-report.html");
    toast("Report downloaded.", "good");
  }

  /* ======================================================== thermodynamics */

  // Which isotherm constant each K° route consumes, and which model supplies
  // it. Checked before fitting so a mismatched pair produces a clear message
  // rather than a KeyError from the Python side.
  const ROUTE_NEEDS = {
    langmuir_molar: { field: "K_L", param: "KL", models: ["langmuir"],
                      label: "the Langmuir constant K_L" },
    redlich_peterson: { field: "K_RP", param: "KRP", models: ["redlich_peterson"],
                        label: "the Redlich–Peterson constant K_RP" },
    freundlich: { field: "K_F", param: "KF", models: ["freundlich"],
                  label: "the Freundlich constant K_F" },
    kd_density: { field: "K_D", param: null, models: null, label: "" },
    kc_dimensionless: { field: "K_C", param: null, models: null, label: "" },
    direct: { field: "K0", param: null, models: null, label: "" }
  };

  function buildThermoControls() {
    const sel = $("#th-model");
    // Ordered so Langmuir is the default, since it pairs with the default
    // K° route; the catalogue's own order is alphabetical and would put
    // Dubinin-Radushkevich first, which supplies no equilibrium constant.
    ["langmuir", "redlich_peterson", "freundlich", "sips", "toth",
     "temkin", "dubinin_radushkevich"].forEach(function (key) {
      const m = CATALOGUE.isotherm.find(function (x) { return x.key === key; });
      if (m) sel.appendChild(el("option", { value: m.key, text: m.name }));
    });

    const routes = call("k_routes").routes;
    const rsel = $("#th-route");
    routes.forEach(function (r) {
      rsel.appendChild(el("option", { value: r.key,
        text: r.label + (r.defensible ? "" : "  ⚠") }));
    });
    function updateNote() {
      const r = routes.find(function (x) { return x.key === rsel.value; });
      const box = $("#th-route-note");
      box.className = "callout " + (r.defensible ? "info" : "bad");
      $("span:last-child", box).innerHTML = md(r.note);
    }
    rsel.onchange = updateNote;
    updateNote();

    $("#th-add").onclick = function () { addThermoDataset(); };
    $("#th-arrhenius").onchange = function () {
      $("#th-arr-box").classList.toggle("hidden", !this.checked);
    };
    $("#th-run").onclick = runThermo;
    addThermoDataset(298.15);
    addThermoDataset(308.15);
    addThermoDataset(318.15);
  }

  function addThermoDataset(T, text) {
    const host = $("#th-datasets");
    const idx = host.children.length;
    const box = el("div", { class: "panel", style: "margin-bottom:10px" }, [
      el("div", { class: "panel-head" }, [
        el("h3", { text: "Temperature " + (idx + 1) }),
        el("span", { class: "hint" }, [
          el("button", { class: "btn ghost sm", text: "remove",
            onclick: function () { box.remove(); renumberThermo(); } })
        ])
      ]),
      el("div", { class: "panel-body" }, [
        el("label", { class: "field" }, [
          el("span", { class: "lbl", text: "Temperature (K)" }),
          el("input", { type: "number", step: "0.01", class: "th-T",
                        value: T || (298.15 + idx * 10) })
        ]),
        el("label", { class: "field", style: "margin-bottom:0" }, [
          el("span", { class: "lbl", text: "Ce and qe, two columns" }),
          el("textarea", { rows: "5", class: "th-data", spellcheck: "false",
                           placeholder: "0.5\t8.1\n1.2\t17.9\n…" })
        ])
      ])
    ]);
    if (text) $(".th-data", box).value = text;
    host.appendChild(box);
  }

  function renumberThermo() {
    $$("#th-datasets .panel-head h3").forEach(function (h, i) {
      h.textContent = "Temperature " + (i + 1);
    });
  }

  async function runThermo() {
    const boxes = $$("#th-datasets > .panel");
    if (boxes.length < 2) {
      toast("At least two temperatures are needed.", "bad"); return;
    }
    const datasets = [];
    for (const b of boxes) {
      const T = Number($(".th-T", b).value);
      const txt = $(".th-data", b).value.trim();
      if (!txt) continue;
      let p;
      try { p = parseInput(txt); }
      catch (e) { toast("Could not read data at " + T + " K.", "bad"); return; }
      if (p.n_cols < 2) { toast("Two columns needed at " + T + " K.", "bad"); return; }
      datasets.push({ T: T, x: p.columns[0], y: p.columns[1] });
    }
    if (datasets.length < 2) {
      toast("At least two temperatures with data are needed.", "bad"); return;
    }

    const btn = $("#th-run");
    const old = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-inline"></span> Analysing…';
    await new Promise(function (r) { setTimeout(r, 30); });

    try {
      const modelKey = $("#th-model").value;
      const route = $("#th-route").value;
      const MW = Number($("#th-MW").value) || null;
      const need = ROUTE_NEEDS[route];

      if (need.models && need.models.indexOf(modelKey) < 0) {
        const wanted = CATALOGUE.isotherm.find(function (m) {
          return m.key === need.models[0];
        });
        toast('This K° route needs ' + need.label + ', which only the ' +
              wanted.name + ' model provides. Either switch the isotherm model ' +
              'to ' + wanted.name + ', or choose a K° route that does not depend ' +
              'on a specific model (K_D or K_C).', "bad", 11000);
        return;
      }
      if (route === "langmuir_molar" && !MW) {
        toast("Enter the adsorbate molar mass, the Langmuir K° route converts " +
              "K_L from L/mg to L/mol and cannot do that without it.", "bad", 8000);
        return;
      }

      const kfit = call("isotherm_K_for_thermo", {
        model: modelKey, datasets: datasets, ctx: {}
      });

      const bad = kfit.rows.filter(function (r) { return !r.success; });
      if (bad.length) {
        toast("The isotherm fit failed at " + bad.length + " temperature(s); " +
              "check those datasets before running the thermodynamics.", "bad", 8000);
        return;
      }

      const values = kfit.rows.map(function (r, i) {
        const out = {};
        if (route === "kd_density" || route === "kc_dimensionless") {
          // Evaluate in the dilute limit, K_D = qe/Ce is only a constant as
          // Ce -> 0 unless the isotherm happens to be linear.
          const ds = datasets[i];
          let jmin = 0;
          ds.x.forEach(function (v, j) { if (v < ds.x[jmin]) jmin = j; });
          out[need.field] = ds.y[jmin] / ds.x[jmin];
        } else if (need.param) {
          const v = r.params[need.param];
          if (v === undefined || v === null) {
            throw new Error("the fitted " + need.label + " is not available at " +
                            datasets[i].T + " K");
          }
          out[need.field] = v;
        }
        if (route === "langmuir_molar") out.MW = MW;
        return out;
      });

      const payload = {
        T: datasets.map(function (d) { return d.T; }),
        route: route, values: values, MW: MW,
        nonlinear: $("#th-nonlinear").checked
      };

      if ($("#th-isosteric").checked) {
        payload.isosteric = buildIsosteric(kfit, datasets, modelKey);
      }
      if ($("#th-arrhenius").checked) {
        const at = $("#th-arr-data").value.trim();
        if (at) {
          const p = parseInput(at);
          if (p.n_cols >= 2) {
            payload.arrhenius = { T: p.columns[0], k: p.columns[1] };
          }
        }
      }

      const res = call("fit_thermo", payload);
      res._kfit = kfit;
      res._datasets = datasets;
      STATE.thermo.result = res;
      renderThermo();
      toast("Thermodynamic analysis complete.", "good");
    } catch (e) {
      toast("Analysis failed: " + e.message, "bad", 8000);
    } finally {
      btn.disabled = false;
      btn.innerHTML = old;
    }
  }

  function buildIsosteric(kfit, datasets, modelKey) {
    // For a set of target loadings, find the Ce each temperature needs to
    // reach that loading, by inverting the fitted isotherm numerically.
    const allQ = [];
    datasets.forEach(function (d) { allQ.push.apply(allQ, d.y); });
    const qmin = Math.min.apply(null, allQ), qmax = Math.max.apply(null, allQ);
    const targets = [];
    for (let i = 1; i <= 5; i++) {
      targets.push(qmin + (qmax - qmin) * (i / 6));
    }
    const Ce = targets.map(function (q) {
      return kfit.rows.map(function (r, i) {
        return invertIsotherm(modelKey, r.params, q, datasets[i]);
      });
    });
    return { T: datasets.map(function (d) { return d.T; }), q: targets, Ce: Ce };
  }

  function invertIsotherm(key, p, qTarget, ds) {
    // Closed form where one exists, bisection otherwise.
    if (key === "langmuir") {
      const denom = p.qm - qTarget;
      return denom > 0 ? qTarget / (p.KL * denom) : null;
    }
    if (key === "freundlich") {
      return Math.pow(qTarget / p.KF, p.n);
    }
    // generic bisection on the observed Ce range, widened 100x each way
    const lo0 = Math.min.apply(null, ds.x) / 100;
    const hi0 = Math.max.apply(null, ds.x) * 100;
    let lo = lo0, hi = hi0;
    const f = function (c) { return evalIsotherm(key, p, c) - qTarget; };
    if (f(lo) * f(hi) > 0) return null;
    for (let i = 0; i < 80; i++) {
      const mid = 0.5 * (lo + hi);
      if (f(lo) * f(mid) <= 0) hi = mid; else lo = mid;
    }
    return 0.5 * (lo + hi);
  }

  function evalIsotherm(key, p, ce) {
    switch (key) {
      case "langmuir": return p.qm * p.KL * ce / (1 + p.KL * ce);
      case "freundlich": return p.KF * Math.pow(ce, 1 / p.n);
      case "sips": {
        const t = Math.pow(p.Ks * ce, p.ms);
        return p.qm * t / (1 + t);
      }
      case "toth":
        return p.qm * p.KT * ce / Math.pow(1 + Math.pow(p.KT * ce, p.nt), 1 / p.nt);
      case "redlich_peterson":
        return p.KRP * ce / (1 + p.aRP * Math.pow(ce, p.g));
      case "temkin":
        return (8.314462618 * 298.15 / p.bT) * Math.log(p.AT * ce);
      default: return NaN;
    }
  }

  function renderThermo() {
    const res = STATE.thermo.result;
    const host = $("#th-results");
    host.innerHTML = "";
    const vh = res.vant_hoff;

    // Figures are constructed synchronously so the styling panel can be
    // built from them in the same pass; only the Plotly calls are deferred,
    // because those need the target divs to exist in the DOM first.
  // Build every thermodynamic figure up front and keep each one's traces
  // and style together, so the styling panel and the exporter can address
  // them by key. Styles survive a re-run, so a figure you have already
  // tuned is not reset when you change a fitting option.
  const prev = STATE.thermo.figures || {};
  const figs = {};

  const x0 = Math.min.apply(null, vh.invT), x1 = Math.max.apply(null, vh.invT);
  figs.vanthoff = {
    label: "van't Hoff: ln K° vs 1/T",
    traces: [
      { kind: "scatter", x: vh.invT, y: vh.lnK, name: "experimental",
        color: Fig.PALETTE[0], symbol: "circle", marker_size: 6 },
      { kind: "line", x: [x0, x1],
        y: [vh.slope * x0 + vh.intercept, vh.slope * x1 + vh.intercept],
        name: "van't Hoff fit (R² = " + fmt(vh.R2, 4) + ")",
        color: Fig.PALETTE[1], dash: "dash", line_width: 1.6 }
    ],
    style: (prev.vanthoff && prev.vanthoff.style) || Fig.newStyle({
      x_label: "1/$T$ (K$^{-1}$)",
      y_label: "ln $K^{\\circ}$",
      legend_loc: "upper right"
    })
  };

  figs.gibbs = {
    label: "Gibbs energy: ΔG° vs T",
    traces: [
      { kind: "scatter", x: vh.T, y: vh.dG_direct_kJ_mol,
        name: "ΔG° from K°", color: Fig.PALETTE[0],
        symbol: "circle", marker_size: 6 },
      { kind: "line", x: vh.T, y: vh.dG_from_fit_kJ_mol,
        name: "ΔH° − TΔS°",
        color: Fig.PALETTE[1], dash: "dash", line_width: 1.6 }
    ],
    style: (prev.gibbs && prev.gibbs.style) || Fig.newStyle({
      x_label: "$T$ (K)",
      y_label: "$\\Delta G^{\\circ}$ (kJ mol$^{-1}$)",
      legend_loc: "upper right"
    })
  };

  if (res.isosteric) {
    const rows = res.isosteric.rows.filter(function (r) {
      return r.dH_iso_kJ_mol !== null;
    });
    if (rows.length) {
      figs.isosteric = {
        label: "Isosteric heat: ΔH_iso vs loading",
        traces: [{
          kind: "scatter", x: rows.map(function (r) { return r.q; }),
          y: rows.map(function (r) { return r.dH_iso_kJ_mol; }),
          yerr: rows.map(function (r) { return r.se_kJ_mol; }),
          name: "ΔH_iso", color: Fig.PALETTE[2],
          symbol: "square", marker_size: 6
        }],
        style: (prev.isosteric && prev.isosteric.style) || Fig.newStyle({
          x_label: "$q_e$ (mg g$^{-1}$)",
          y_label: "$\\Delta H_{iso}$ (kJ mol$^{-1}$)",
          legend: false
        })
      };
    }
  }

  if (res.arrhenius && !res.arrhenius.error) {
    const a = res.arrhenius;
    const ax0 = Math.min.apply(null, a.invT), ax1 = Math.max.apply(null, a.invT);
    const slope = -a.Ea_kJ_mol * 1000 / 8.314462618;
    const icept = Math.log(a.A);
    figs.arrhenius = {
      label: "Arrhenius: ln k vs 1/T",
      traces: [
        { kind: "scatter", x: a.invT, y: a.lnk, name: "experimental",
          color: Fig.PALETTE[0], symbol: "circle", marker_size: 6 },
        { kind: "line", x: [ax0, ax1],
          y: [slope * ax0 + icept, slope * ax1 + icept],
          name: "Arrhenius fit", color: Fig.PALETTE[1], dash: "dash",
          line_width: 1.6 }
      ],
      style: (prev.arrhenius && prev.arrhenius.style) || Fig.newStyle({
        x_label: "1/$T$ (K$^{-1}$)", y_label: "ln $k$",
        legend_loc: "upper right"
      })
    };
  }

  STATE.thermo.figures = figs;
  STATE.thermo.traces = figs.vanthoff.traces;
  STATE.thermo.style = figs.vanthoff.style;


    if (vh.error) {
      host.appendChild(el("div", { class: "callout bad" }, [
        el("span", { class: "ci", text: "✕" }), el("span", { text: vh.error })
      ]));
      return;
    }

    const panel = el("div", { class: "panel" }, [
      el("div", { class: "panel-head" }, [
        el("h2", { text: "Thermodynamic parameters" }),
        el("span", { class: "hint" }, [
          el("span", { class: "chip " + (res.route_defensible ? "info" : "bad"),
                       text: res.route_label })
        ])
      ])
    ]);
    const body = el("div", { class: "panel-body" });

    // headline numbers
    body.appendChild(el("div", { class: "row c3", style: "margin-bottom:16px" }, [
      bigStat("ΔH°", fmt(vh.dH_kJ_mol, 4) + " kJ mol⁻¹",
              "± " + fmt(vh.dH_se_kJ_mol, 2)),
      bigStat("ΔS°", fmt(vh.dS_J_mol_K, 4) + " J mol⁻¹ K⁻¹",
              "± " + fmt(vh.dS_se_J_mol_K, 2)),
      bigStat("van't Hoff R²", fmt(vh.R2, 5),
              vh.R2 > 0.98 ? "good linearity" : "check for curvature")
    ]));

    // per-temperature table
    body.appendChild(el("div", { class: "table-wrap" }, [
      el("table", { class: "data" }, [
        el("thead", {}, [el("tr", {}, [
          el("th", { class: "num", text: "T (K)" }),
          el("th", { class: "num", text: "K°" }),
          el("th", { class: "num", text: "ln K°" }),
          el("th", { class: "num", text: "ΔG° from K° (kJ/mol)" }),
          el("th", { class: "num", text: "ΔG° from ΔH°−TΔS° (kJ/mol)" })
        ])]),
        el("tbody", {}, vh.T.map(function (T, i) {
          return el("tr", {}, [
            el("td", { class: "num", text: T.toFixed(2) }),
            el("td", { class: "num", text: fmt(vh.K0[i], 5) }),
            el("td", { class: "num", text: fmt(vh.lnK[i], 5) }),
            el("td", { class: "num", text: fmt(vh.dG_direct_kJ_mol[i], 4) }),
            el("td", { class: "num", text: fmt(vh.dG_from_fit_kJ_mol[i], 4) })
          ]);
        }))
      ])
    ]));

    body.appendChild(el("div", { class: "section-title", text: "van't Hoff plot" }));
    body.appendChild(el("div", { id: "vh-plot" }));

    body.appendChild(el("div", { class: "section-title", text: "Interpretation" }));
    body.appendChild(el("ul", { class: "interp" }, res.interpretation.map(function (s) {
      return el("li", { html: md(s) });
    })));

    (res.warnings || []).concat(vh.warnings || []).forEach(function (w) {
      body.appendChild(el("div", { class: "callout warn" }, [
        el("span", { class: "ci", text: "⚠" }), el("span", { html: md(w) })
      ]));
    });

    // per-temperature isotherm constants
    body.appendChild(el("div", { class: "section-title",
      text: "Isotherm constants used (" + res._kfit.model_name + ")" }));
    const pkeys = Object.keys(res._kfit.rows[0].params);
    body.appendChild(el("div", { class: "table-wrap" }, [
      el("table", { class: "data" }, [
        el("thead", {}, [el("tr", {}, [el("th", { class: "num", text: "T (K)" })]
          .concat(pkeys.map(function (k) { return el("th", { class: "num", text: k }); }))
          .concat([el("th", { class: "num", text: "R²" })]))]),
        el("tbody", {}, res._kfit.rows.map(function (r) {
          return el("tr", {}, [el("td", { class: "num", text: r.T.toFixed(2) })]
            .concat(pkeys.map(function (k) {
              return el("td", { class: "num", text: fmt(r.params[k], 5) });
            }))
            .concat([el("td", { class: "num", text: fmt(r.R2, 5) })]));
        }))
      ])
    ]));

    if (res.isosteric) {
      body.appendChild(el("div", { class: "section-title",
        text: "Isosteric heat of adsorption" }));
      body.appendChild(el("p", { class: "tiny", html: md(res.isosteric.note) }));
      body.appendChild(el("div", { class: "table-wrap" }, [
        el("table", { class: "data" }, [
          el("thead", {}, [el("tr", {}, [
            el("th", { class: "num", text: "q (mg/g)" }),
            el("th", { class: "num", text: "ΔH_iso (kJ/mol)" }),
            el("th", { class: "num", text: "± " }),
            el("th", { class: "num", text: "R²" })
          ])]),
          el("tbody", {}, res.isosteric.rows.map(function (r) {
            return el("tr", {}, [
              el("td", { class: "num", text: fmt(r.q, 4) }),
              el("td", { class: "num", text: fmt(r.dH_iso_kJ_mol, 4) }),
              el("td", { class: "num", text: fmt(r.se_kJ_mol, 2) }),
              el("td", { class: "num", text: fmt(r.R2, 4) })
            ]);
          }))
        ])
      ]));
      if (res.isosteric.trend) {
        body.appendChild(el("div", { class: "callout info" }, [
          el("span", { class: "ci", text: "▸" }),
          el("span", { html: md(res.isosteric.trend) })
        ]));
      }
      body.appendChild(el("div", { id: "iso-heat-plot" }));
    }

    if (res.arrhenius && !res.arrhenius.error) {
      body.appendChild(el("div", { class: "section-title",
        text: "Arrhenius activation energy" }));
      body.appendChild(el("div", { class: "row c3", style: "margin-bottom:12px" }, [
        bigStat("Eₐ", fmt(res.arrhenius.Ea_kJ_mol, 4) + " kJ mol⁻¹",
                "± " + fmt(res.arrhenius.se_kJ_mol, 2)),
        bigStat("A", fmt(res.arrhenius.A, 4), "pre-exponential factor"),
        bigStat("R²", fmt(res.arrhenius.R2, 5), "")
      ]));
      body.appendChild(el("div", { class: "callout info" }, [
        el("span", { class: "ci", text: "▸" }),
        el("span", { html: md(res.arrhenius.interpretation) })
      ]));
      body.appendChild(el("div", { id: "arr-plot" }));
    }

    body.appendChild(el("div", { class: "section-title",
                                 text: "Figure styling and export" }));
    body.appendChild(buildThermoFigurePanel());

    body.appendChild(el("div", { class: "section-title", text: "Data export" }));
    body.appendChild(el("div", { class: "btn-row" }, [
      el("button", { class: "btn", onclick: function () {
        const rows = vh.T.map(function (T, i) {
          return { T: T, K0: vh.K0[i], lnK: vh.lnK[i],
                   invT: vh.invT[i], dG: vh.dG_direct_kJ_mol[i],
                   dGfit: vh.dG_from_fit_kJ_mol[i] };
        });
        const r = call("export_table", {
          rows: rows, format: "csv",
          columns: [{ key: "T", label: "T (K)" }, { key: "invT", label: "1/T (1/K)" },
                    { key: "K0", label: "K0" }, { key: "lnK", label: "ln K0" },
                    { key: "dG", label: "dG from K (kJ/mol)" },
                    { key: "dGfit", label: "dG from dH-TdS (kJ/mol)" }],
          caption: "van't Hoff data"
        });
        download(new Blob([r.text], { type: "text/csv" }), "adsorpfit-vanthoff.csv");
      } }, ["Download data (CSV)"]),
      el("button", { class: "btn", onclick: function () {
        download(new Blob([JSON.stringify(STATE.thermo.result, null, 2)],
                          { type: "application/json" }),
                 "adsorpfit-thermo.json");
      } }, ["Download full result (JSON)"])
    ]));

    panel.appendChild(body);
    host.appendChild(panel);
    Layout.refresh();

    setTimeout(function () {

      Fig.draw("vh-plot", figs.vanthoff.traces, figs.vanthoff.style, theme());
      if (figs.isosteric) {
        Fig.draw("iso-heat-plot", figs.isosteric.traces,
                 Object.assign({}, figs.isosteric.style, { height_cm: 6 }), theme());
      }
      if (figs.arrhenius) {
        Fig.draw("arr-plot", figs.arrhenius.traces,
                 Object.assign({}, figs.arrhenius.style, { height_cm: 6 }), theme());
      }

      if ($("#th-fig-preview")) {
        const pick = $("#th-figpick");
        const k = (pick && pick.value) || "vanthoff";
        if (figs[k]) Fig.draw("th-fig-preview", figs[k].traces, figs[k].style, theme());
      }
    }, 40);
  }

  function bigStat(label, value, sub) {
    return el("div", { style: "background:var(--foam-50);border:1px solid var(--border);" +
      "border-radius:10px;padding:12px 14px" }, [
      el("div", { class: "tiny", style: "font-weight:700;text-transform:uppercase;" +
        "letter-spacing:.6px", text: label }),
      el("div", { style: "font-size:19px;font-weight:700;margin:3px 0 1px;" +
        "letter-spacing:-.3px", text: value }),
      el("div", { class: "tiny", text: sub || "" })
    ]);
  }

  // The thermodynamic figures get the same treatment as the kinetics and
  // isotherm ones: a full style panel, a live preview, and every export
  // format. A figure selector switches which of the three is being edited.
  function buildThermoFigurePanel() {
    const figs = STATE.thermo.figures || {};
    const keys = Object.keys(figs);
    if (!keys.length) return el("p", { class: "tiny", text: "No figure available." });

    const sel = el("select", { id: "th-figpick" }, keys.map(function (k) {
      return el("option", { value: k, text: figs[k].label });
    }));
    const styleHost = el("div", { class: "style-stack", id: "th-stylectl" });
    const preview = el("div", { id: "th-fig-preview" });

    function refresh() {
      const k = sel.value;
      const f = STATE.thermo.figures[k];
      Fig.draw("th-fig-preview", f.traces, f.style, theme());
    }
    sel.onchange = function () {
      const f = STATE.thermo.figures[sel.value];
      Fig.buildControls(styleHost, f.style, refresh);
      refresh();
    };

    const fmtSel = el("select", { id: "th-imgfmt" },
      IMAGE_FORMATS.map(function (f) {
        return el("option", { value: f[0], text: f[1] });
      }));
    const dpiSel = el("select", { id: "th-imgdpi" },
      [150, 300, 600, 900, 1200].map(function (d) {
        const o = el("option", { value: d, text: d + " dpi" });
        if (d === 600) o.selected = true;
        return o;
      }));

    const shell = el("div", { class: "figure-shell" }, [
      el("div", {}, [
        el("div", { class: "btn-row", style: "margin-bottom:10px" }, [
          el("span", { class: "mini-label", style: "margin:0", text: "Figure" }),
          sel
        ]),
        preview,
        el("div", { class: "row c2", style: "margin-top:12px" }, [
          el("label", { class: "field" }, [
            el("span", { class: "lbl", text: I18N.t("lbl.format") }), fmtSel]),
          el("label", { class: "field" }, [
            el("span", { class: "lbl", text: I18N.t("lbl.resolution") }), dpiSel])
        ]),
        el("div", { class: "btn-row" }, [
          el("button", { class: "btn primary", text: I18N.t("btn.download"),
            onclick: function () {
              exportThermoFigure(sel.value, fmtSel.value, Number(dpiSel.value));
            } }),
          el("button", { class: "btn", text: I18N.t("btn.downloadAll"),
            onclick: async function () {
              for (const f of IMAGE_FORMATS) {
                if (f[0] === "bmp") continue;
                await exportThermoFigure(sel.value, f[0], Number(dpiSel.value));
                await new Promise(function (r) { setTimeout(r, 350); });
              }
            } })
        ])
      ]),
      el("div", {}, [styleHost])
    ]);

    setTimeout(function () {
      const f = STATE.thermo.figures[sel.value];
      Fig.buildControls(styleHost, f.style, refresh);
      refresh();
    }, 20);
    return shell;
  }

  async function exportThermoFigure(key, format, dpi) {
    try {
      const f = STATE.thermo.figures[key];
      if (!f) return;
      const style = Object.assign({}, f.style, { dpi: dpi || 600 });
      const payload = Fig.toMatplotlib(f.traces, style, format || "png");
      payload.dpi = dpi || 600;
      toast(I18N.t("msg.rendering", { fmt: (format || "png").toUpperCase(),
                                      dpi: dpi || 600 }));
      const r = call("render_figure", payload);
      download(b64ToBlob(r.data, r.mime), "adsorpfit-" + key + "." + r.format);
      toast(I18N.t("msg.downloaded"), "good");
    } catch (e) { toast("Export failed: " + e.message, "bad", 7000); }
  }

  /* ======================================================== settings drawer */

  function openDrawer(title, buildBody) {
    closeDrawer();
    const back = el("div", { class: "drawer-back", onclick: closeDrawer });
    const body = el("div", { class: "drawer-body" });
    const panel = el("div", { class: "drawer", role: "dialog", "aria-modal": "true" }, [
      el("div", { class: "drawer-head" }, [
        el("h3", { text: title }),
        el("button", { class: "icon-btn", style: "margin-left:auto",
                       onclick: closeDrawer, html: "&times;",
                       "aria-label": I18N.t("btn.close") })
      ]),
      body
    ]);
    document.body.appendChild(back);
    document.body.appendChild(panel);
    buildBody(body);
    document.addEventListener("keydown", escClose);
  }

  function escClose(e) { if (e.key === "Escape") closeDrawer(); }

  function closeDrawer() {
    $$(".drawer-back, .drawer").forEach(function (n) { n.remove(); });
    document.removeEventListener("keydown", escClose);
  }

  function segmented(labelKey, prefKey, options) {
    const wrap = el("div", {}, [
      el("label", { class: "mini-label", text: I18N.t(labelKey) })
    ]);
    const seg = el("div", { class: "seg" });
    options.forEach(function (o) {
      const b = el("button", { type: "button", text: I18N.t(o[1]) });
      b.setAttribute("aria-pressed", Prefs.get(prefKey) === o[0] ? "true" : "false");
      b.onclick = function () {
        Prefs.set(prefKey, o[0]);
        $$("button", seg).forEach(function (x) {
          x.setAttribute("aria-pressed", x === b ? "true" : "false");
        });
        redrawAllFigures();
      };
      seg.appendChild(b);
    });
    wrap.appendChild(seg);
    return wrap;
  }

  function openSettings() {
    openDrawer(I18N.t("set.title"), function (body) {
      body.appendChild(segmented("set.theme", "theme", [
        ["light", "set.themeLight"], ["dark", "set.themeDark"],
        ["auto", "set.themeAuto"]
      ]));
      body.appendChild(segmented("set.motion", "motion", [
        ["full", "set.motionFull"], ["calm", "set.motionCalm"],
        ["off", "set.motionOff"]
      ]));
      body.appendChild(segmented("set.layout", "layout", [
        ["side", "set.layoutSide"], ["right", "set.layoutRight"],
        ["stack", "set.layoutStack"]
      ]));
      body.appendChild(segmented("set.density", "density", [
        ["comfy", "set.densityComfy"], ["compact", "set.densityCompact"]
      ]));

      body.appendChild(el("div", { class: "section-title",
                                   text: I18N.t("set.language") }));
      const seg = el("div", { class: "seg" });
      I18N.languages.forEach(function (l) {
        const b = el("button", { type: "button", text: l[1] });
        b.setAttribute("aria-pressed", I18N.get() === l[0] ? "true" : "false");
        b.onclick = function () {
          I18N.set(l[0]);
          closeDrawer();
          openSettings();
        };
        seg.appendChild(b);
      });
      body.appendChild(seg);
      body.appendChild(el("p", { class: "tiny", html:
        "The interface, the guide and the model descriptions are translated. "
        + "The automatically written interpretation paragraphs are still "
        + "generated in English." }));

      body.appendChild(el("div", { class: "section-title",
                                   text: I18N.t("set.panels") }));
      body.appendChild(el("p", { class: "tiny", text: I18N.t("set.panelsHelp") }));
      body.appendChild(el("div", { class: "btn-row", style: "margin-bottom:6px" }, [
        el("button", { class: "btn sm", text: I18N.t("set.resetLayout"),
          onclick: function () { Layout.reset(); toast(I18N.t("set.layoutReset"), "good"); } })
      ]));

      const u = Projects.usage();
      body.appendChild(el("div", { class: "section-title", text: "Storage" }));
      body.appendChild(el("p", { class: "tiny", html:
        u.count + " project(s) saved, using " + (u.bytes / 1024).toFixed(1)
        + " KB of this browser's local storage. Preferences and projects live "
        + "on this device only: nothing is sent to a server, so they will not "
        + "follow you to another computer unless you export them to a file." }));
    });
  }

  /* ======================================================== projects drawer */

  function snapshot() {
    // Everything needed to restore a working session. Raw text is stored
    // rather than parsed arrays so the user sees exactly what they typed.
    return {
      version: Projects.VERSION,
      savedAt: new Date().toISOString(),
      kinetics: {
        data: $("#kin-data").value,
        tunit: $("#kin-tunit").value, qunit: $("#kin-qunit").value,
        T: $("#kin-T").value, C0: $("#kin-C0").value,
        dose: $("#kin-dose").value, radius: $("#kin-radius").value,
        weights: $("#kin-weights").value, criterion: $("#kin-criterion").value,
        linear: $("#kin-linear").checked,
        models: $$("#kin-models input:checked").map(function (c) { return c.value; }),
        style: STATE.kinetics.style, traceStyle: STATE.kinetics.traceStyle
      },
      isotherm: {
        data: $("#iso-data").value,
        cunit: $("#iso-cunit").value, qunit: $("#iso-qunit").value,
        T: $("#iso-T").value, MW: $("#iso-MW").value,
        Cs: $("#iso-Cs").value, dose: $("#iso-dose").value,
        weights: $("#iso-weights").value, criterion: $("#iso-criterion").value,
        linear: $("#iso-linear").checked,
        models: $$("#iso-models input:checked").map(function (c) { return c.value; }),
        style: STATE.isotherm.style, traceStyle: STATE.isotherm.traceStyle
      },
      thermo: {
        model: $("#th-model").value, route: $("#th-route").value,
        MW: $("#th-MW").value,
        nonlinear: $("#th-nonlinear").checked,
        isosteric: $("#th-isosteric").checked,
        arrhenius: $("#th-arrhenius").checked,
        arrData: $("#th-arr-data").value,
        datasets: $$("#th-datasets > .panel").map(function (b) {
          return { T: $(".th-T", b).value, data: $(".th-data", b).value };
        })
      }
    };
  }

  function restore(p) {
    if (!p) return;
    function setv(sel, v) { const n = $(sel); if (n && v !== undefined && v !== null) n.value = v; }
    function setc(sel, v) { const n = $(sel); if (n && v !== undefined) n.checked = !!v; }

    const k = p.kinetics || {};
    setv("#kin-data", k.data); setv("#kin-tunit", k.tunit); setv("#kin-qunit", k.qunit);
    setv("#kin-T", k.T); setv("#kin-C0", k.C0); setv("#kin-dose", k.dose);
    setv("#kin-radius", k.radius); setv("#kin-weights", k.weights);
    setv("#kin-criterion", k.criterion); setc("#kin-linear", k.linear);
    if (k.models) $$("#kin-models input").forEach(function (c) {
      c.checked = k.models.indexOf(c.value) >= 0;
    });
    STATE.kinetics.style = k.style || null;
    STATE.kinetics.traceStyle = k.traceStyle || null;

    const i = p.isotherm || {};
    setv("#iso-data", i.data); setv("#iso-cunit", i.cunit); setv("#iso-qunit", i.qunit);
    setv("#iso-T", i.T); setv("#iso-MW", i.MW); setv("#iso-Cs", i.Cs);
    setv("#iso-dose", i.dose); setv("#iso-weights", i.weights);
    setv("#iso-criterion", i.criterion); setc("#iso-linear", i.linear);
    if (i.models) $$("#iso-models input").forEach(function (c) {
      c.checked = i.models.indexOf(c.value) >= 0;
    });
    STATE.isotherm.style = i.style || null;
    STATE.isotherm.traceStyle = i.traceStyle || null;

    const th = p.thermo || {};
    setv("#th-model", th.model); setv("#th-route", th.route); setv("#th-MW", th.MW);
    setc("#th-nonlinear", th.nonlinear); setc("#th-isosteric", th.isosteric);
    setc("#th-arrhenius", th.arrhenius); setv("#th-arr-data", th.arrData);
    $("#th-arr-box").classList.toggle("hidden", !th.arrhenius);
    if (th.datasets && th.datasets.length) {
      $("#th-datasets").innerHTML = "";
      th.datasets.forEach(function (d) { addThermoDataset(Number(d.T), d.data); });
    }
    const rs = $("#th-route");
    if (rs && rs.onchange) rs.onchange();

    ["kinetics", "isotherm"].forEach(function (c) {
      STATE[c].fit = null; STATE[c].advice = null;
      $(c === "kinetics" ? "#kin-results" : "#iso-results").innerHTML = "";
      renderAdvice(c);
      if ($(c === "kinetics" ? "#kin-data" : "#iso-data").value.trim()) readData(c);
    });
    STATE.thermo.result = null;
    $("#th-results").innerHTML = "";
  }

  // Show which project is open, so saving over the right one is obvious.
  function refreshProjectBadge() {
    const b = $("#proj-current");
    if (!b) return;
    if (STATE.projectName) {
      b.textContent = STATE.projectName;
      b.classList.remove("hidden");
    } else {
      b.textContent = "";
      b.classList.add("hidden");
    }
  }

  function openProjects() {
    openDrawer(I18N.t("proj.title"), function (body) {
      const nameInput = el("input", { type: "text",
        placeholder: I18N.t("proj.name"),
        value: STATE.projectName || "" });
      body.appendChild(el("label", { class: "field" }, [
        el("span", { class: "lbl", text: I18N.t("proj.name") }), nameInput
      ]));
      body.appendChild(el("div", { class: "btn-row", style: "margin-bottom:16px" }, [
        el("button", { class: "btn primary sm", text: I18N.t("proj.save"),
          onclick: function () {
            const nm = nameInput.value.trim();
            if (!nm) { toast(I18N.t("proj.name"), "bad"); return; }
            const rec = Projects.save(nm, snapshot(), STATE.projectId);
            if (!rec) {
              toast("Could not save: this browser's local storage is full. "
                    + "Delete an old project or export it to a file first.",
                    "bad", 9000);
              return;
            }
            STATE.projectId = rec.id;
            STATE.projectName = rec.name;
            toast(I18N.t("proj.saved"), "good");
            refreshProjectBadge();
            closeDrawer(); openProjects();
          } }),
        el("button", { class: "btn sm", text: I18N.t("proj.saveAs"),
          onclick: function () {
            const nm = nameInput.value.trim();
            if (!nm) { toast(I18N.t("proj.name"), "bad"); return; }
            const rec = Projects.save(nm, snapshot(), null);
            if (rec) {
              STATE.projectId = rec.id; STATE.projectName = rec.name;
              toast(I18N.t("proj.saved"), "good");
            refreshProjectBadge();
              closeDrawer(); openProjects();
            }
          } })
      ]));

      const list = Projects.all();
      body.appendChild(el("div", { class: "section-title",
        text: I18N.t("proj.title") + " (" + list.length + ")" }));
      if (!list.length) {
        body.appendChild(el("p", { class: "tiny", text: I18N.t("proj.none") }));
      }
      // Rename and delete happen inside the drawer rather than through
      // window.prompt and window.confirm. Native dialogs are suppressed in a
      // number of contexts (sandboxed frames, background tabs, and once a
      // user has ticked "prevent this page from creating additional
      // dialogs"). When they are suppressed prompt returns null and confirm
      // returns false, so both actions silently did nothing.
      list.forEach(function (p) {
        const row = el("div", { class: "proj-item" });

        function renderRow(mode) {
          row.innerHTML = "";
          row.classList.toggle("confirming", mode === "delete");

          if (mode === "rename") {
            const input = el("input", { type: "text", value: p.name });
            function commit() {
              const nm = input.value.trim();
              if (!nm) { renderRow(); return; }
              Projects.rename(p.id, nm);
              p.name = nm;
              if (STATE.projectId === p.id) {
                STATE.projectName = nm;
                refreshProjectBadge();
              }
              toast(I18N.t("proj.renamed"), "good");
              renderRow();
            }
            input.onkeydown = function (e) {
              if (e.key === "Enter") { e.preventDefault(); commit(); }
              if (e.key === "Escape") { e.preventDefault(); renderRow(); }
            };
            row.appendChild(el("div", { class: "pb" }, [input]));
            row.appendChild(el("div", { class: "pa" }, [
              el("button", { class: "btn sm primary", text: I18N.t("btn.save"),
                             onclick: commit }),
              el("button", { class: "btn sm", text: I18N.t("btn.cancel"),
                             onclick: function () { renderRow(); } })
            ]));
            setTimeout(function () { input.focus(); input.select(); }, 20);
            return;
          }

          if (mode === "delete") {
            row.appendChild(el("div", { class: "pb" }, [
              el("div", { class: "pn", text: I18N.t("proj.confirmDelete") }),
              el("div", { class: "pd", text: p.name })
            ]));
            row.appendChild(el("div", { class: "pa" }, [
              el("button", { class: "btn sm danger", text: I18N.t("btn.delete"),
                onclick: function () {
                  Projects.remove(p.id);
                  if (STATE.projectId === p.id) {
                    STATE.projectId = null; STATE.projectName = "";
                    refreshProjectBadge();
                  }
                  toast(I18N.t("proj.deleted"), "good");
                  closeDrawer(); openProjects();
                } }),
              el("button", { class: "btn sm", text: I18N.t("btn.cancel"),
                             onclick: function () { renderRow(); } })
            ]));
            return;
          }

          const when = new Date(p.modified);
          const nameEl = el("div", { class: "pn editable",
                                     title: I18N.t("proj.clickToRename") }, [
            el("span", { text: p.name }),
            p.id === STATE.projectId
              ? el("span", { class: "chip info", style: "margin-left:6px",
                             text: I18N.t("proj.current") }) : null
          ]);
          nameEl.onclick = function () { renderRow("rename"); };

          row.appendChild(el("div", { class: "pb" }, [
            nameEl,
            el("div", { class: "pd", text: I18N.t("proj.modified") + " "
              + when.toLocaleString() })
          ]));
          row.appendChild(el("div", { class: "pa" }, [
            el("button", { class: "btn sm", text: I18N.t("btn.load"),
              onclick: function () {
                restore(p.payload);
                STATE.projectId = p.id; STATE.projectName = p.name;
                refreshProjectBadge();
                toast(I18N.t("proj.loaded"), "good");
                closeDrawer();
              } }),
            el("button", { class: "btn sm", text: I18N.t("btn.rename"),
                           onclick: function () { renderRow("rename"); } }),
            el("button", { class: "btn sm danger", text: I18N.t("btn.delete"),
                           onclick: function () { renderRow("delete"); } })
          ]));
        }

        renderRow();
        body.appendChild(row);
      });

      body.appendChild(el("div", { class: "section-title", text: "Transfer" }));
      body.appendChild(el("p", { class: "tiny", html:
        "Projects are stored in this browser only. Export to a file to move one "
        + "to another computer, or to keep a backup." }));
      body.appendChild(el("div", { class: "btn-row" }, [
        el("button", { class: "btn sm", text: I18N.t("proj.export"),
          onclick: function () {
            const blob = new Blob([JSON.stringify({
              app: "AdsorpFit", version: Projects.VERSION,
              exported: new Date().toISOString(), projects: Projects.all()
            }, null, 2)], { type: "application/json" });
            download(blob, "adsorpfit-projects.json");
          } }),
        (function () {
          const lab = el("label", { class: "btn sm", style: "margin:0" },
                         [I18N.t("proj.import")]);
          const inp = el("input", { type: "file", accept: ".json", hidden: "" });
          inp.onchange = function () {
            const f = inp.files[0];
            if (!f) return;
            const r = new FileReader();
            r.onload = function () {
              try {
                const parsed = JSON.parse(r.result);
                const incoming = parsed.projects || [];
                if (!incoming.length) throw new Error("no projects in that file");
                let n = 0;
                incoming.forEach(function (p) {
                  if (Projects.save(p.name, p.payload, null)) n++;
                });
                toast("Imported " + n + " project(s).", "good");
                closeDrawer(); openProjects();
              } catch (e) {
                toast("Could not read that file: " + e.message, "bad", 7000);
              }
            };
            r.readAsText(f);
          };
          lab.appendChild(inp);
          return lab;
        })()
      ]));
    });
  }

  function redrawAllFigures() {
    ["kinetics", "isotherm"].forEach(function (c) {
      if (STATE[c].fit) drawMainFigure(c);
    });
    if (STATE.thermo.result) renderThermo();
  }

  /* ================================================================= guide */

  function buildGuide() {
    $("#guide-body").innerHTML = GUIDE_HTML;
  }

  /* ============================================================ demo data */

  const DEMO = {
    kinetics:
      "t (min)\tqt (mg/g)\n" +
      "5\t22.8\n10\t36.4\n15\t46.1\n20\t53.2\n30\t62.5\n45\t70.1\n" +
      "60\t74.2\n90\t77.6\n120\t78.9\n150\t79.4\n180\t79.6\n240\t79.8\n300\t79.9",
    isotherm:
      "Ce (mg/L)\tqe (mg/g)\tsd\tC0\n" +
      "0.52\t8.1\t0.4\t10\n1.24\t17.9\t0.7\t25\n2.55\t32.5\t1.1\t50\n" +
      "5.10\t52.4\t1.6\t80\n9.05\t71.2\t2.0\t120\n15.1\t88.6\t2.4\t160\n" +
      "25.3\t103.1\t2.8\t220\n40.2\t112.9\t3.0\t300\n65.4\t119.4\t3.2\t400\n" +
      "100.1\t122.8\t3.3\t500\n150.3\t124.3\t3.4\t600\n220.5\t125.0\t3.4\t700",
    thermo: [
      [298.15, "0.52\t8.1\n1.24\t17.9\n2.55\t32.5\n5.10\t52.4\n9.05\t71.2\n" +
               "15.1\t88.6\n25.3\t103.1\n40.2\t112.9\n65.4\t119.4\n100.1\t122.8"],
      [308.15, "0.52\t9.6\n1.24\t20.9\n2.55\t37.4\n5.10\t59.2\n9.05\t78.9\n" +
               "15.1\t96.4\n25.3\t110.4\n40.2\t119.4\n65.4\t125.2\n100.1\t128.2"],
      [318.15, "0.52\t11.3\n1.24\t24.3\n2.55\t42.7\n5.10\t66.2\n9.05\t86.5\n" +
               "15.1\t103.9\n25.3\t117.2\n40.2\t125.5\n65.4\t130.6\n100.1\t133.2"]
    ]
  };

  /* ================================================================== wire */

  function wire() {
    $$("#tabs button").forEach(function (b) {
      b.onclick = function () {
        $$("#tabs button").forEach(function (x) {
          x.setAttribute("aria-selected", x === b ? "true" : "false");
        });
        $$(".tabpane").forEach(function (p) {
          p.classList.toggle("hidden", p.id !== "panel-" + b.dataset.tab);
        });
        window.scrollTo({ top: 0, behavior: "smooth" });
      };
    });

    $("#settings-btn").onclick = openSettings;
    $("#projects-btn").onclick = openProjects;
    $("#resetlayout-btn").onclick = function () {
      Layout.reset();
      toast(I18N.t("set.layoutReset"), "good");
    };

    const ls = $("#lang-switch");
    I18N.languages.forEach(function (l) {
      const b = el("button", { type: "button", text: l[0].toUpperCase(),
                               title: l[1] });
      b.setAttribute("aria-pressed", I18N.get() === l[0] ? "true" : "false");
      b.onclick = function () { I18N.set(l[0]); };
      ls.appendChild(b);
    });
    I18N.onChange(function (lang) {
      $$("#lang-switch button").forEach(function (b) {
        b.setAttribute("aria-pressed",
          b.textContent.toLowerCase() === lang ? "true" : "false");
      });
      // re-render anything whose text was generated rather than marked up
      ["kinetics", "isotherm"].forEach(function (c) {
        if (STATE[c].fit) renderResults(c);
        renderAdvice(c);
      });
      if (STATE.thermo.result) renderThermo();
      buildGuide();
    });

    Prefs.onChange(function () { redrawAllFigures(); });

    $$("[data-advise]").forEach(function (b) {
      b.onclick = function () { runAdvisor(b.dataset.advise); };
    });

    $("#kin-run").onclick = function () { runFit("kinetics"); };
    $("#iso-run").onclick = function () { runFit("isotherm"); };

    $$("[data-demo]").forEach(function (b) {
      b.onclick = function () {
        const k = b.dataset.demo;
        if (k === "thermo") {
          $("#th-datasets").innerHTML = "";
          DEMO.thermo.forEach(function (d) { addThermoDataset(d[0], d[1]); });
          $("#th-MW").value = "194.19";
          toast("Example loaded: three temperatures.", "good");
        } else {
          $(k === "kinetics" ? "#kin-data" : "#iso-data").value = DEMO[k];
          readData(k);
          toast("Example data loaded. Press “Fit models”.", "good");
        }
      };
    });

    $$("[data-clear]").forEach(function (b) {
      b.onclick = function () {
        const k = b.dataset.clear;
        if (k === "thermo") { $("#th-datasets").innerHTML = ""; addThermoDataset(); }
        else {
          $(k === "kinetics" ? "#kin-data" : "#iso-data").value = "";
          $(k === "kinetics" ? "#kin-count" : "#iso-count").textContent = "no data";
          $(k === "kinetics" ? "#kin-results" : "#iso-results").innerHTML = "";
          STATE[k].data = STATE[k].fit = null;
        }
      };
    });

    $$("[data-file]").forEach(function (inp) {
      inp.onchange = function () {
        const f = inp.files[0];
        if (!f) return;
        const r = new FileReader();
        r.onload = function () {
          $(inp.dataset.file === "kinetics" ? "#kin-data" : "#iso-data").value = r.result;
          readData(inp.dataset.file);
          toast("Loaded " + f.name, "good");
        };
        r.readAsText(f);
      };
    });

    $$("[data-selectall]").forEach(function (a) {
      a.onclick = function (e) {
        e.preventDefault();
        const pref = a.dataset.selectall === "kinetics" ? "#kin-models" : "#iso-models";
        $$(pref + " input[type=checkbox]").forEach(function (c) { c.checked = true; });
      };
    });
    $$("[data-selectnone]").forEach(function (a) {
      a.onclick = function (e) {
        e.preventDefault();
        const pref = a.dataset.selectnone === "kinetics" ? "#kin-models" : "#iso-models";
        $$(pref + " input[type=checkbox]").forEach(function (c) { c.checked = false; });
      };
    });

    ["kin-data", "iso-data"].forEach(function (id) {
      $("#" + id).addEventListener("blur", function () {
        if (this.value.trim()) readData(id === "kin-data" ? "kinetics" : "isotherm");
      });
    });
  }

  const GUIDE_HTML = [
    "<p>AdsorpFit fits adsorption data in your browser. Nothing is uploaded",
    "the Python scientific stack runs locally through WebAssembly, so your ",
    "unpublished data stays on your machine.</p>",
    "<h3>Getting a result</h3><ol>",
    "<li>Paste two columns of data, or upload a CSV. Column 1 is time (kinetics) ",
    "or equilibrium concentration (isotherms); column 2 is the loading q.</li>",
    "<li>Fill in the experiment panel. Temperature is needed by Temkin and ",
    "Dubinin–Radushkevich; molar mass is needed for the D–R mean free energy and ",
    "for the thermodynamic K° conversion; initial concentrations enable the ",
    "Langmuir separation factor R<sub>L</sub>.</li>",
    "<li>Select models and press <strong>Fit models</strong>.</li></ol>",
    "<h3>Three things worth knowing before you report anything</h3>",
    "<p><strong>Do not rank models by R².</strong> R² can only increase when you ",
    "add a parameter, so comparing a two-parameter Langmuir against a ",
    "four-parameter Fritz–Schlünder on R² is guaranteed to favour the latter ",
    "regardless of whether the extra parameters mean anything. AdsorpFit ranks on ",
    "AICc, which penalises complexity, and reports Akaike weights so you can see ",
    "when two models are genuinely indistinguishable (Δ &lt; 2).</p>",
    "<p><strong>Non-linear regression is the correct method.</strong> Linearising ",
    "an adsorption model changes the error structure: plotting t/q<sub>t</sub> ",
    "against t, for instance, puts t on both axes and manufactures a correlation, ",
    "which is the main reason pseudo-second-order appears to fit almost every ",
    "published dataset. AdsorpFit fits the untransformed equation and shows the ",
    "linear plots only for comparison.</p>",
    "<p><strong>ΔG° depends on how you make K° dimensionless.</strong> ",
    "−RT ln K requires a dimensionless K. A Langmuir K<sub>L</sub> in L/mg is not ",
    "dimensionless, and different unit choices for the same experiment give ΔG° ",
    "values differing by tens of kJ/mol. The Thermodynamics tab makes you choose ",
    "a conversion route explicitly and states it in the output, because it must ",
    "be stated in your paper too.</p>",
    "<h3>Checks AdsorpFit runs for you</h3><ul>",
    "<li>Whether a fitted parameter's standard error exceeds the parameter ",
    "itself, i.e. whether the data actually determine it.</li>",
    "<li>Whether q<sub>e,cal</sub> agrees with q<sub>e,exp</sub>, which catches ",
    "bad kinetic fits that R² misses.</li>",
    "<li>Whether the fitted q<sub>max</sub> lies far outside the measured range, ",
    "making it an extrapolation rather than a measurement.</li>",
    "<li>Whether a three- or four-parameter model has collapsed onto a simpler ",
    "one (Sips with m = 1 is Langmuir; Redlich–Peterson with g = 1 is Langmuir).</li>",
    "<li>Whether a parameter has hit a physical bound.</li>",
    "<li>Whether a linearised fit is flattering itself relative to the same ",
    "parameters tested against the raw data.</li></ul>",
    "<h3>Citing the models</h3>",
    "<p>Every model card carries the original citation. Cite the primary ",
    "source (Lagergren 1898, Ho &amp; McKay 1999, Langmuir 1918), not a recent paper ",
    "that happens to use the model. The <em>?</em> button beside each model shows ",
    "its equation, parameter meanings, assumptions and reference.</p>"
  ].join("");

  /* =================================================================== go */

  function start() {
    I18N.init();
    Prefs.init();
    I18N.apply(document);
    wire();
    Layout.init();
    boot();
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
