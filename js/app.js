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

  const SUB_DIGITS = { "₀": "0", "₁": "1", "₂": "2", "₃": "3",
                       "₄": "4", "₅": "5", "₆": "6", "₇": "7",
                       "₈": "8", "₉": "9" };
  const SUP_CHARS = { "⁰": "0", "¹": "1", "²": "2", "³": "3",
                      "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7",
                      "⁸": "8", "⁹": "9", "⁻": "−",
                      "⁺": "+", "ᵅ": "α", "·": "." };

  // Normalise scientific notation to one rendered form.
  //
  // The model library was written over time in two notations: ASCII
  // underscores (q_max, C_e, k_2) and Unicode subscripts. Both were shown
  // literally, so a parameter appeared in a table as "q_max". Rather than
  // rewrite six hundred strings, and risk breaking the very lookup tables
  // that map those characters, both forms are converted here to <sub> and
  // <sup>. Greek letters and the degree sign are left alone: they are real
  // characters, not notation workarounds.
  function sci(s) {
    return s
      // Unicode runs first, so a following ASCII rule cannot split them
      .replace(/[₀-₉]+/g, function (run) {
        return "<sub>" + run.replace(/./g, function (c) {
          return SUB_DIGITS[c] || c; }) + "</sub>";
      })
      .replace(/[⁰¹²³⁴-⁹⁺⁻ᵅ·]+/g,
        function (run) {
          // a lone middle dot is punctuation, not an exponent
          if (!/[⁰¹²³⁴-⁹⁻ᵅ]/.test(run)) return run;
          return "<sup>" + run.replace(/./g, function (c) {
            return SUP_CHARS[c] || c; }) + "</sup>";
        })
      // braced forms, e.g. q_{e,cal} and 10^{B}
      .replace(/([A-Za-z])_\{([^}]{1,10})\}/g, "$1<sub>$2</sub>")
      .replace(/\^\{([^}]{1,10})\}/g, "<sup>$1</sup>")
      // bare forms, e.g. q_max and R^2
      .replace(/([A-Za-z])_([A-Za-z0-9]{1,6})(?![A-Za-z0-9_])/g, "$1<sub>$2</sub>")
      .replace(/\^(−?-?[0-9A-Za-z.]{1,4})/g, "<sup>$1</sup>");
  }

  // Minimal, safe markdown: **bold**, *italic*, `code`, plus the scientific
  // notation above. Everything else is escaped, because these strings are
  // composed from fitted numbers and must never be parsed as HTML.
  function md(s) {
    return sci(String(s)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"))
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

  // Render a parameter symbol as maths. Model metadata carries a `tex` field
  // derived from the symbol; the plain `symbol` remains the fallback and is
  // what the CSV and LaTeX exports use, since those want text.
  function symbolNode(meta, opts) {
    opts = opts || {};
    const html = tex(meta.tex, { display: false });
    if (html) {
      return el("span", { class: "sym" + (opts.cls ? " " + opts.cls : ""),
                          html: html, title: meta.symbol });
    }
    return el("span", { class: "sym-fallback", text: meta.symbol });
  }

  function unitNode(meta) {
    if (!meta.unit || meta.unit === "–" || meta.unit === "-") {
      return el("span", { class: "tiny", text: "–" });
    }
    const html = meta.unit_tex ? tex(meta.unit_tex, { display: false }) : null;
    if (html) return el("span", { class: "sym unit", html: html });
    return el("span", { class: "tiny", text: meta.unit });
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

  const N_BOOT_STEPS = 5;          // boot.step.0 through boot.step.4

  function bootMsg(i, extra) {
    $("#boot-msg").textContent = I18N.t("boot.step." + i) + (extra ? " " + extra : "");
    $("#boot-bar").style.width = ((i + 1) / N_BOOT_STEPS * 100) + "%";
  }

  // Ten to twenty seconds is a long time to look at a progress bar. These
  // lines use it to say something true about how the fitting works, each
  // one a decision the site actually acts on rather than a slogan.
  const N_FACTS = 7;

  function startBootFacts() {
    const host = $("#boot-fact");
    if (!host) return;
    let i = Math.floor(Math.random() * N_FACTS);   // not always the same first line
    // one wrapper element, so the flex centring treats the line as a whole
    const show = function () {
      host.innerHTML = "<span>" + I18N.t("boot.fact." + i) + "</span>";
    };
    show();
    I18N.onChange(show);

    const timer = setInterval(function () {
      if (!document.getElementById("boot") ||
          $("#boot").classList.contains("done")) {
        clearInterval(timer);
        return;
      }
      i = (i + 1) % N_FACTS;
      if (document.documentElement.getAttribute("data-motion") === "off") {
        show();
        return;
      }
      host.classList.add("swap");
      setTimeout(function () { show(); host.classList.remove("swap"); }, 450);
    }, 4600);
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
      // lang.py and the ko_* tables have to be on the filesystem before
      // bridge is imported, because core imports lang at module load.
      const files = ["lang.py", "ko_core.py", "ko_advisor.py",
                     "ko_kinetics.py", "ko_isotherms.py", "ko_thermo.py",
                     "ko_extra.py", "ko_names.py", "ko_assumptions.py", "ko.py",
                     "core.py", "isotherms.py", "kinetics.py", "thermo.py",
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
      // The interpretation paragraphs are written in Python with the fitted
      // numbers inside them, so the Python side needs the language too.
      call("set_language", I18N.get());

      CATALOGUE.isotherm = call("list_models", "isotherm").models;
      CATALOGUE.kinetics = call("list_models", "kinetics").models;

      buildModelPicker("kinetics");
      buildModelPicker("isotherm");
      buildPresetPickers();
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
      el("div", { class: "section-title", text: I18N.t("sub.params") }),
      el("dl", { class: "kv" }, m.params.reduce(function (acc, p) {
        const dt = el("dt", {}, [symbolNode(p)]);
        if (p.unit && p.unit !== "–" && p.unit !== "-") {
          dt.appendChild(document.createTextNode(" "));
          dt.appendChild(unitNode(p));
        }
        acc.push(dt);
        acc.push(el("dd", { text: p.meaning }));
        return acc;
      }, [])),
      el("div", { class: "section-title", text: I18N.t("sec.assumes") }),
      el("ul", { class: "interp" }, m.assumptions.map(function (a) {
        return el("li", { html: md(a) });
      })),
      m.linear_forms.length ? el("div", { class: "section-title", text: I18N.t("sec.linear") }) : null,
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

  /* ============================================================== presets */

  // Built-in example datasets. Each carries its citation, which is shown
  // beneath the picker once one is loaded: these are other people's
  // measurements and should travel with their attribution.
  function buildPresetPickers() {
    $$("[data-preset]").forEach(function (sel) {
      const cat = sel.dataset.preset;
      sel.innerHTML = "";
      sel.appendChild(el("option", { value: "",
                                     text: I18N.t("preset.choose") }));
      PRESETS.filter(function (p) {
        return p.cat === (cat === "kinetics" ? "kinetics" : "isotherm");
      }).forEach(function (p) {
        const t = p[I18N.get()] || p.en;
        sel.appendChild(el("option", { value: p.id, text: t.name }));
      });
      sel.onchange = function () {
        if (sel.value) loadPreset(cat, sel.value);
      };
    });
  }

  function loadPreset(cat, id) {
    const p = PRESETS.find(function (x) { return x.id === id; });
    if (!p) return;
    const t = p[I18N.get()] || p.en;
    const pref = cat === "kinetics" ? "kin" : "iso";

    $("#" + pref + "-data").value = p.data;
    Object.keys(p.ctx || {}).forEach(function (k) {
      const n = $("#" + pref + "-" + k);
      if (n) n.value = p.ctx[k];
    });
    if (p.models) {
      $$("#" + pref + "-models input[type=checkbox]").forEach(function (c) {
        c.checked = p.models.indexOf(c.value) >= 0;
      });
    }
    readData(cat);

    STATE[cat].fit = null;
    STATE[cat].advice = null;
    STATE[cat].frames = null;
    STATE[cat].traceStyle = null;
    $("#" + pref + "-results").innerHTML = "";
    renderAdvice(cat);

    // attribution sits under the picker, not in a toast that disappears
    const host = $("#" + pref + "-data").closest(".panel-body");
    let cite = $(".preset-cite", host);
    if (!cite) {
      cite = el("div", { class: "preset-cite" });
      host.appendChild(cite);
    }
    cite.innerHTML = "<b>" + md(t.name) + ".</b> " + md(t.note) +
                     "<span class='src'>" + md(p.cite) + "</span>";
    toast(I18N.t("preset.loaded"), "good");
  }

  /* ============================================================ field help */

  // Longer explanations live behind the "?" beside a field rather than under
  // it, so the panel stays scannable but the answer is one click away.
  // Written for someone who has the number in front of them and does not know
  // what it is for.
  const FIELD_HELP = {
    mw: {
      en: {
        title: "Molar mass",
        html:
          "<p>The molecular weight of <b>the substance you are adsorbing</b>, " +
          "not the adsorbent. If you are removing caffeine with biochar, this " +
          "is caffeine's molar mass, not the biochar's.</p>" +
          "<div class='egs'>" +
          "<b>Caffeine</b><span>194.19</span>" +
          "<b>Methylene blue</b><span>319.85</span>" +
          "<b>Phenol</b><span>94.11</span>" +
          "<b>Pb(II)</b><span>207.2</span>" +
          "<b>Cd(II)</b><span>112.41</span>" +
          "</div>" +
          "<p>Exactly two calculations need it:</p><ul>" +
          "<li><b>Dubinin–Radushkevich.</b> Its mean free energy E comes from " +
          "the Polanyi potential, &epsilon; = RT ln(1 + 1/C<sub>e</sub>), which " +
          "is only dimensionally correct with C<sub>e</sub> in mol/L. Without " +
          "the molar mass your C<sub>e</sub> stays in mg/L, so E carries the " +
          "wrong units and cannot be compared either with published values or " +
          "with the 8 and 16 kJ/mol thresholds used to argue physisorption " +
          "against chemisorption.</li>" +
          "<li><b>Thermodynamics.</b> The recommended route to a dimensionless " +
          "K° converts the Langmuir constant from L/mg to L/mol before " +
          "multiplying by the molarity of water, and that conversion is where " +
          "the molar mass enters.</li></ul>" +
          "<p>Every other model ignores it, so leave it blank if you are " +
          "fitting neither.</p>"
      },
      ko: {
        title: "분자량",
        html:
          "<p><b>흡착되는 물질</b>의 분자량입니다. 흡착제의 분자량이 아닙니다. " +
          "바이오차로 카페인을 제거한다면 카페인의 분자량을 입력합니다.</p>" +
          "<div class='egs'>" +
          "<b>카페인</b><span>194.19</span>" +
          "<b>메틸렌 블루</b><span>319.85</span>" +
          "<b>페놀</b><span>94.11</span>" +
          "<b>Pb(II)</b><span>207.2</span>" +
          "<b>Cd(II)</b><span>112.41</span>" +
          "</div>" +
          "<p>다음 두 계산에서만 사용됩니다.</p><ul>" +
          "<li><b>Dubinin–Radushkevich.</b> 평균 자유에너지 E는 Polanyi 퍼텐셜 " +
          "&epsilon; = RT ln(1 + 1/C<sub>e</sub>)에서 구하는데, 이 식은 " +
          "C<sub>e</sub>가 mol/L일 때만 차원이 맞습니다. 분자량이 없으면 " +
          "C<sub>e</sub>가 mg/L로 남아 E의 단위가 틀리게 되고, 문헌값이나 " +
          "물리흡착·화학흡착 기준인 8, 16 kJ/mol과 비교할 수 없습니다.</li>" +
          "<li><b>열역학.</b> 무차원 K°를 구하는 권장 경로에서 Langmuir 상수를 " +
          "L/mg에서 L/mol로 변환할 때 분자량이 필요합니다.</li></ul>" +
          "<p>다른 모델은 이 값을 사용하지 않으므로, 두 계산을 하지 않는다면 " +
          "비워 두어도 됩니다.</p>"
      }
    },

    cs: {
      en: {
        title: "Solubility Cₛ",
        html:
          "<p>The <b>saturation concentration</b> of your adsorbate in water at " +
          "your working temperature: the highest C<sub>e</sub> that can " +
          "physically exist before the compound starts coming out of solution. " +
          "Look it up for your compound; PubChem and solubility tables list it, " +
          "and it changes with temperature.</p>" +
          "<div class='egs'>" +
          "<b>Methylene blue, 25 °C</b><span>43 600 mg/L</span>" +
          "<b>Phenol, 25 °C</b><span>83 000 mg/L</span>" +
          "<b>Caffeine, 25 °C</b><span>21 600 mg/L</span>" +
          "</div>" +
          "<p><b>Only the BET model uses it.</b> BET describes adsorbate " +
          "stacking in layers on top of already-adsorbed molecules, and that " +
          "only becomes significant as the solution approaches saturation. Its " +
          "equation divides by (C<sub>s</sub> − C<sub>e</sub>), so it diverges " +
          "at C<sub>e</sub> = C<sub>s</sub>.</p>" +
          "<p>Two things AdsorpFit will tell you if C<sub>s</sub> is wrong: it " +
          "blocks the BET fit outright when your highest C<sub>e</sub> reaches " +
          "or exceeds C<sub>s</sub>, since the solution would be " +
          "supersaturated; and it warns when your data sit far below " +
          "C<sub>s</sub>, because then there is little multilayer behaviour for " +
          "the model to detect and q<sub>s</sub> will be poorly determined.</p>" +
          "<p>Leave it blank unless you are fitting BET.</p>"
      },
      ko: {
        title: "용해도 Cₛ",
        html:
          "<p>사용 온도에서 흡착질이 물에 녹을 수 있는 <b>포화 농도</b>입니다. " +
          "즉 화합물이 석출되기 전까지 실제로 존재할 수 있는 최대 " +
          "C<sub>e</sub>입니다. PubChem이나 용해도 표에서 찾을 수 있으며 " +
          "온도에 따라 달라집니다.</p>" +
          "<div class='egs'>" +
          "<b>메틸렌 블루, 25 °C</b><span>43 600 mg/L</span>" +
          "<b>페놀, 25 °C</b><span>83 000 mg/L</span>" +
          "<b>카페인, 25 °C</b><span>21 600 mg/L</span>" +
          "</div>" +
          "<p><b>BET 모델에서만 사용됩니다.</b> BET는 이미 흡착된 분자 위에 " +
          "다시 흡착되어 층이 쌓이는 현상을 다루는데, 이는 용액이 포화에 " +
          "가까워질 때만 뚜렷해집니다. 식의 분모에 (C<sub>s</sub> − " +
          "C<sub>e</sub>)가 있어 C<sub>e</sub> = C<sub>s</sub>에서 발산합니다.</p>" +
          "<p>C<sub>s</sub>가 맞지 않으면 두 가지를 알려 줍니다. 최대 " +
          "C<sub>e</sub>가 C<sub>s</sub> 이상이면 과포화 상태가 되므로 BET " +
          "피팅을 차단하고, 데이터가 C<sub>s</sub>보다 훨씬 낮으면 다층 흡착 " +
          "거동이 거의 없어 q<sub>s</sub>가 잘 결정되지 않는다고 경고합니다.</p>" +
          "<p>BET를 사용하지 않는다면 비워 두어도 됩니다.</p>"
      }
    },

    radius: {
      en: {
        title: "Particle radius",
        html:
          "<p>The mean radius of your adsorbent grains, in centimetres. Measure " +
          "it by sieve fraction or laser diffraction, and use half the mean " +
          "diameter.</p>" +
          "<p>Two diffusion calculations consume it. The <b>Boyd</b> plot turns " +
          "its slope B into an effective diffusion coefficient through " +
          "D<sub>i</sub> = B·r²/π². The <b>Crank</b> homogeneous surface " +
          "diffusion model contains D and r only as the ratio D/r², which is " +
          "why they cannot be fitted separately.</p>" +
          "<p>That last point matters: if you let the fit choose r, neither D " +
          "nor r means anything on its own, only their ratio. Enter your " +
          "measured radius and treat D as the single fitted quantity.</p>"
      },
      ko: {
        title: "입자 반경",
        html:
          "<p>흡착제 입자의 평균 반경(cm)입니다. 체 분석이나 레이저 회절로 " +
          "측정한 평균 직경의 절반을 사용하세요.</p>" +
          "<p>두 가지 확산 계산에 사용됩니다. <b>Boyd</b> 그래프는 기울기 B를 " +
          "D<sub>i</sub> = B·r²/π² 식으로 유효 확산계수로 변환합니다. " +
          "<b>Crank</b> 균일 표면확산 모델에서는 D와 r이 D/r² 형태로만 " +
          "나타나므로 둘을 따로 구할 수 없습니다.</p>" +
          "<p>따라서 r을 피팅에 맡기면 D와 r은 각각으로는 의미가 없고 비율만 " +
          "의미를 갖습니다. 측정한 반경을 입력하고 D만 피팅 결과로 보세요.</p>"
      }
    }
  };

  function showFieldHelp(key) {
    const entry = FIELD_HELP[key];
    if (!entry) return;
    const t = entry[I18N.get()] || entry.en;
    const back = el("div", { class: "modal-back", onclick: function (e) {
      if (e.target === back) back.remove();
    } });
    back.appendChild(el("div", { class: "modal", style: "max-width:560px" }, [
      el("div", { class: "modal-head" }, [
        el("h3", { text: t.title }),
        el("button", { class: "icon-btn", style: "margin-left:auto",
                       onclick: function () { back.remove(); }, html: "&times;",
                       "aria-label": I18N.t("btn.close") })
      ]),
      el("div", { class: "modal-body help-body", html: t.html })
    ]));
    document.body.appendChild(back);
    function esc(e) {
      if (e.key === "Escape") { back.remove(); document.removeEventListener("keydown", esc); }
    }
    document.addEventListener("keydown", esc);
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

  async function runFit(cat, opts) {
    opts = opts || {};
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
      if (!opts.silent) {
        toast(I18N.t("msg.fitted", { n: models.length }), "good");
        scrollToResults(cat);
      }
    } catch (e) {
      toast("Fitting failed: " + e.message, "bad", 8000);
    } finally {
      btn.disabled = false;
      btn.innerHTML = old;
    }
  }

  /* =============================================================== advisor */

  async function runAdvisor(cat, opts) {
    opts = opts || {};
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
        el("th", { text: I18N.t("th.rank") }),
        el("th", { text: I18N.t("th.model") }),
        el("th", { class: "num", text: "p" }),
        el("th", { class: "num", text: crit }),
        el("th", { class: "num", text: "Δ" }),
        el("th", { class: "num", text: I18N.t("th.weight") }),
        el("th", { class: "num", text: "R²" }),
        el("th", { class: "num", text: I18N.t("th.adjR2") }),
        el("th", { class: "num", text: "RMSE" }),
        el("th", { text: I18N.t("th.support") })
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

    wrap.appendChild(el("p", { class: "tiny", style: "margin-top:10px",
      html: I18N.t("th.footnote", { crit: crit }) }));

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
      el("div", { class: "section-title", text: I18N.t("fig.series") }),
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

  /* ====================================================== series appearance */

  // One implementation of the per-series controls, shared by the kinetics,
  // isotherm and thermodynamic figures so all three offer the same handles.
  //
  // `items` describes the rows: {key, label, defaults}. `store` holds the
  // user's choices, keyed so they survive a redraw or a refit. `redraw` is
  // called on every change.
  function seriesControls(host, items, store, redraw) {
    host.innerHTML = "";
    if (!items.length) {
      host.appendChild(el("p", { class: "tiny", style: "margin:0",
                                 text: I18N.t("fig.noSeries") }));
      return;
    }

    items.forEach(function (item) {
      const ts = store[item.key] =
        Object.assign({}, item.defaults, store[item.key] || {});
      // the kind comes from the figure, never from stale stored state
      ts.kind = item.defaults.kind;
      const isLine = ts.kind === "line";

      function field(labelKey, node) {
        return el("div", {}, [
          el("label", { class: "mini-label", text: I18N.t(labelKey) }), node
        ]);
      }

      const showBox = el("input", { type: "checkbox" });
      showBox.checked = ts.show !== false;
      showBox.onchange = function () { ts.show = showBox.checked; redraw(); };

      const colour = el("input", { type: "color", value: ts.color || "#0072B2" });
      colour.oninput = function () { ts.color = colour.value; redraw(); };

      const shape = el("select");
      (isLine ? ["solid", "dash", "dot", "dashdot", "longdash"]
              : Fig.SYMBOL_CYCLE.concat(["circle-open", "square-open",
                                         "diamond-open", "triangle-up-open"]))
        .forEach(function (o) {
          const op = el("option", { value: o, text: o });
          if ((isLine ? ts.dash : ts.symbol) === o) op.selected = true;
          shape.appendChild(op);
        });
      shape.onchange = function () {
        if (isLine) ts.dash = shape.value; else ts.symbol = shape.value;
        redraw();
      };

      const size = el("input", {
        type: "number", step: "0.1", min: "0.2", max: "16",
        value: isLine ? (ts.line_width != null ? ts.line_width : 1.6)
                      : (ts.marker_size != null ? ts.marker_size : 5)
      });
      size.oninput = function () {
        const v = Number(size.value);
        if (isLine) ts.line_width = v; else ts.marker_size = v;
        redraw();
      };

      const row = el("div", { class: "row c4",
                              style: "align-items:end;margin-bottom:8px" }, [
        el("div", {}, [
          el("label", { class: "mini-label", text: item.label, title: item.label }),
          el("label", { class: "inline-check", style: "margin:0" },
             [showBox, I18N.t("fig.show")])
        ]),
        field("fig.colour", colour),
        field(isLine ? "fig.dash" : "fig.symbol", shape),
        field(isLine ? "fig.width" : "fig.size", size)
      ]);
      host.appendChild(row);

      // markers get an outline colour and error-bar width as well, which
      // matter for publication figures and have nowhere else to live
      if (!isLine) {
        const edge = el("input", { type: "color",
                                   value: ts.marker_edge || ts.color || "#0072B2" });
        edge.oninput = function () { ts.marker_edge = edge.value; redraw(); };
        const edgeW = el("input", { type: "number", step: "0.1", min: "0", max: "6",
          value: ts.marker_edge_width != null ? ts.marker_edge_width : 1.2 });
        edgeW.oninput = function () {
          ts.marker_edge_width = Number(edgeW.value); redraw();
        };
        const cap = el("input", { type: "number", step: "0.5", min: "0", max: "12",
          value: ts.capsize != null ? ts.capsize : 3 });
        cap.oninput = function () { ts.capsize = Number(cap.value); redraw(); };
        host.appendChild(el("div", { class: "row c4",
                                     style: "align-items:end;margin-bottom:14px" }, [
          el("div", {}),
          field("fig.edge", edge),
          field("fig.edgeWidth", edgeW),
          field("fig.capsize", cap)
        ]));
      }
    });
  }

  // Fold the stored appearance choices into a figure's traces. Traces are
  // matched by name, which is stable across redraws; index is the fallback
  // for an unnamed trace.
  function styledTraces(traces, store) {
    store = store || {};
    return traces.map(function (t, i) {
      const s = store[t.name || ("series" + i)];
      if (!s) return t;
      const out = Object.assign({}, t);
      if (s.color) out.color = s.color;
      if (s.symbol) out.symbol = s.symbol;
      if (s.dash) out.dash = s.dash;
      if (s.marker_size != null) out.marker_size = s.marker_size;
      if (s.line_width != null) out.line_width = s.line_width;
      if (s.marker_edge) out.marker_edge = s.marker_edge;
      if (s.marker_edge_width != null) out.marker_edge_width = s.marker_edge_width;
      if (s.capsize != null) out.capsize = s.capsize;
      out.visible = s.show !== false;
      return out;
    });
  }

  // Describe a figure's traces as rows for seriesControls.
  function traceItems(traces) {
    return traces.map(function (t, i) {
      return {
        key: t.name || ("series" + i),
        label: t.name || ("series " + (i + 1)),
        defaults: {
          kind: t.kind === "line" ? "line" : "scatter",
          color: t.color || Fig.PALETTE[i % Fig.PALETTE.length],
          symbol: t.symbol || "circle",
          dash: t.dash || "solid",
          marker_size: t.marker_size != null ? t.marker_size : 6,
          line_width: t.line_width != null ? t.line_width : 1.6,
          show: true
        }
      };
    });
  }
  function buildTraceControls(cat, host) {
    const st = STATE[cat];
    st.traceStyle = st.traceStyle || {};
    const items = [{
      key: "__data__", label: I18N.t("fig.experimental"),
      defaults: { kind: "scatter", color: Fig.PALETTE[0], symbol: "circle",
                  marker_size: 5, show: true }
    }];
    seriesFor(cat).forEach(function (m, i) {
      items.push({
        key: m.model_key, label: m.model_name,
        defaults: { kind: "line",
                    color: Fig.PALETTE[(i + 1) % Fig.PALETTE.length],
                    dash: "solid", line_width: 1.6, show: i < 4 }
      });
    });
    seriesControls(host, items, st.traceStyle, function () { drawMainFigure(cat); });
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

  // Friendly names for the quantities models compute on the side. Without
  // these the raw key leaks into the table.
  const DERIVED_LABELS = {
    "t_half": "t_1/2, half-time",
    "t_95": "t_95, time to 95% of equilibrium",
    "h_initial_rate": "h, initial adsorption rate",
    "E_kJ_mol": "E, mean free energy of adsorption",
    "R_L": "R_L, separation factor",
    "B": "B, Temkin heat constant",
    "qmax_equiv": "q_max equivalent (K_RP/a_RP)"
  };

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
            el("th", { text: I18N.t("th.parameter") }),
            el("th", { text: I18N.t("th.unit") }),
            el("th", { class: "num", text: I18N.t("th.value") }),
            el("th", { class: "num", text: I18N.t("th.stderr") }),
            el("th", { class: "num", text: I18N.t("th.ci") }),
            el("th", { class: "num", text: "t" }),
            el("th", { class: "num", text: "p" })
          ])]),
          el("tbody", {}, m.param_meta.map(function (p) {
            const v = m.params[p.key], se = m.stderr[p.key], ci = m.ci95[p.key];
            const pv = m.pvalue[p.key];
            return el("tr", {}, [
              el("td", {}, [symbolNode(p)]),
              el("td", {}, [unitNode(p)]),
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
        body.appendChild(el("div", { class: "section-title", text: I18N.t("sec.derived") }));
        const dl = el("dl", { class: "kv" });
        Object.keys(m.derived).forEach(function (k) {
          const v = m.derived[k];
          // these keys are symbols (t_half, h_initial_rate, E_kJ_mol), so they
          // get the same subscript treatment as everything else
          dl.appendChild(el("dt", { html: md(DERIVED_LABELS[k] || k) }));
          dl.appendChild(el("dd", { text: Array.isArray(v)
            ? v.map(function (q) { return fmt(q, 4); }).join(", ")
            : fmt(v, 5) }));
        });
        body.appendChild(dl);
      }

      body.appendChild(el("div", { class: "section-title", text: I18N.t("sec.gof") }));
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
          text: I18N.t("interp.outOfRange") }) : null,
        el("ul", { class: "interp" }, m.interpretation.map(function (s) {
          return el("li", { html: md(s) });
        })),
        el("div", { class: "section-title", text: I18N.t("sec.assuming") }),
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
      text: I18N.t("sec.weberMorris") }));
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
      wrap.appendChild(el("div", { class: "section-title", text: I18N.t("sec.boyd") }));
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
      el("span", { html: md(I18N.t("lin.caveat")) })
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
                  el("td", {}, [symbolNode(p)]),
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
    ["png", "fmt.png"],
    ["tiff", "fmt.tiff"],
    ["pdf", "fmt.pdf"],
    ["svg", "fmt.svg"],
    ["eps", "fmt.eps"],
    ["ps", "fmt.ps"],
    ["jpg", "fmt.jpg"],
    ["webp", "fmt.webp"],
    ["bmp", "fmt.bmp"]
  ];

  const TABLE_FORMATS = [
    ["csv", "fmt.csv"],
    ["tsv", "fmt.tsv"],
    ["xlsx", "fmt.xlsx"],
    ["markdown", "fmt.markdown"],
    ["latex", "fmt.latex"],
    ["html", "fmt.html"],
    ["json", "fmt.json"]
  ];

  function renderExport(cat) {
    const wrap = el("div");

    wrap.appendChild(el("div", { class: "section-title", text: I18N.t("sec.figure") }));
    const fmtSel = el("select", { id: cat + "-imgfmt" },
      IMAGE_FORMATS.map(function (f) {
        return el("option", { value: f[0], text: I18N.t(f[1]) });
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
      I18N.t("exp.figureNote") }));
    wrap.appendChild(el("div", { class: "btn-row", style: "margin:10px 0 22px" }, [
      el("button", { class: "btn primary", onclick: function () {
        exportFigure(cat, fmtSel.value, Number(dpiSel.value));
      } }, ["Download figure"]),
      el("button", { class: "btn", onclick: function () {
        exportAllFormats(cat, Number(dpiSel.value));
      } }, ["Download every format"])
    ]));

    wrap.appendChild(el("div", { class: "section-title", text: I18N.t("sec.tables") }));
    const tfmt = el("select", { id: cat + "-tabfmt" },
      TABLE_FORMATS
        .filter(function (f) { return f[0] !== "xlsx" || XLSX_AVAILABLE; })
        .map(function (f) {
          return el("option", { value: f[0], text: I18N.t(f[1]) });
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

    wrap.appendChild(el("div", { class: "section-title", text: I18N.t("sec.plotData") }));
    wrap.appendChild(el("p", { class: "tiny", html:
      I18N.t("exp.curveNote") }));
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
          model: m.model_name,
          // LaTeX export wants "$q_{\mathrm{max}}$"; every other format wants
          // the plain symbol, which is what spreadsheets and CSV readers expect
          parameter: p.symbol,
          parameter_tex: p.tex ? "$" + p.tex + "$" : p.symbol,
          unit: p.unit,
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
      const cols = PARAM_COLS.map(function (c) {
        return (format === "latex" && c.key === "parameter")
          ? { key: "parameter_tex", label: c.label } : c;
      });
      const r = call("export_table", {
        rows: rows, columns: cols, format: format,
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
      "sub{font-size:.72em;vertical-align:-0.28em;line-height:0}",
      "sup{font-size:.72em;vertical-align:0.45em;line-height:0}",
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
        parts.push("<tr><td>" + md(p.symbol) + "</td><td>" + md(p.unit) +
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
                      label: "the Langmuir constant K_L", labelHtml: true },
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

  async function runThermo(opts) {
    opts = opts || {};
    const boxes = $$("#th-datasets > .panel");
    if (boxes.length < 2) {
      if (!opts.silent) toast("At least two temperatures are needed.", "bad"); return;
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
      if (!opts.silent) toast("At least two temperatures with data are needed.", "bad"); return;
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
        toast('This K° route needs ' + need.label.replace(/_/g, "") + ', which only the ' +
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
      if (!opts.silent) toast(I18N.t("msg.thermoDone"), "good");
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
        name: I18N.t("th.vhFit", { r2: fmt(vh.R2, 4) }),
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
        label: I18N.t("th.isoLabel"),
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

  // carry the per-series appearance across a re-run, so a figure you have
  // already styled is not reset when a fitting option changes
  Object.keys(figs).forEach(function (k) {
    figs[k].traceStyle = (prev[k] && prev[k].traceStyle) || {};
  });

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
        el("h2", { text: I18N.t("th.params") }),
        el("span", { class: "hint" }, [
          el("span", { class: "chip " + (res.route_defensible ? "info" : "bad"),
                       html: md(res.route_label) })
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
              vh.R2 > 0.98 ? I18N.t("th.goodLin") : I18N.t("th.checkCurve"))
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

    body.appendChild(el("div", { class: "section-title", text: I18N.t("sec.vantHoff") }));
    body.appendChild(el("div", { id: "vh-plot" }));

    body.appendChild(el("div", { class: "section-title", text: I18N.t("sub.interp") }));
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
      text: I18N.t("th.constUsed", { model: res._kfit.model_name }) }));
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
        text: I18N.t("th.isosteric") }));
      body.appendChild(el("p", { class: "tiny", html: md(res.isosteric.note) }));
      body.appendChild(el("div", { class: "table-wrap" }, [
        el("table", { class: "data" }, [
          el("thead", {}, [el("tr", {}, [
            el("th", { class: "num", text: "q (mg/g)" }),
            el("th", { class: "num", html: md("ΔH_iso") + " (kJ/mol)" }),
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
                                 text: I18N.t("th.figStyle") }));
    body.appendChild(buildThermoFigurePanel());

    body.appendChild(el("div", { class: "section-title", text: I18N.t("sec.dataExport") }));
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

      Fig.draw("vh-plot", styledTraces(figs.vanthoff.traces, figs.vanthoff.traceStyle),
               figs.vanthoff.style, theme());
      if (figs.isosteric) {
        Fig.draw("iso-heat-plot",
                 styledTraces(figs.isosteric.traces, figs.isosteric.traceStyle),
                 Object.assign({}, figs.isosteric.style, { height_cm: 6 }), theme());
      }
      if (figs.arrhenius) {
        Fig.draw("arr-plot",
                 styledTraces(figs.arrhenius.traces, figs.arrhenius.traceStyle),
                 Object.assign({}, figs.arrhenius.style, { height_cm: 6 }), theme());
      }

      if ($("#th-fig-preview")) {
        const pick = $("#th-figpick");
        const k = (pick && pick.value) || "vanthoff";
        if (figs[k]) Fig.draw("th-fig-preview",
                              styledTraces(figs[k].traces, figs[k].traceStyle),
                              figs[k].style, theme());
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
    const traceHost = el("div", { id: "th-tracectl" });
    const preview = el("div", { id: "th-fig-preview" });

    function refresh() {
      const f = STATE.thermo.figures[sel.value];
      if (!f) return;
      Fig.draw("th-fig-preview", styledTraces(f.traces, f.traceStyle),
               f.style, theme());
    }
    function rebuildPanels() {
      const f = STATE.thermo.figures[sel.value];
      if (!f) return;
      f.traceStyle = f.traceStyle || {};
      Fig.buildControls(styleHost, f.style, refresh);
      seriesControls(traceHost, traceItems(f.traces), f.traceStyle, refresh);
      refresh();
    }
    sel.onchange = rebuildPanels;

    const fmtSel = el("select", { id: "th-imgfmt" },
      IMAGE_FORMATS.map(function (f) {
        return el("option", { value: f[0], text: I18N.t(f[1]) });
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
        el("div", { class: "section-title", text: I18N.t("fig.series") }),
        traceHost,
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

    setTimeout(rebuildPanels, 20);
    return shell;
  }

  async function exportThermoFigure(key, format, dpi) {
    try {
      const f = STATE.thermo.figures[key];
      if (!f) return;
      const style = Object.assign({}, f.style, { dpi: dpi || 600 });
      const payload = Fig.toMatplotlib(styledTraces(f.traces, f.traceStyle),
                                       style, format || "png");
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
      body.appendChild(el("div", { class: "section-title", text: I18N.t("sec.storage") }));
      body.appendChild(el("p", { class: "tiny", html:
        u.count + " project(s) saved, using " + (u.bytes / 1024).toFixed(1)
        + " KB of this browser's local storage. Preferences and projects live "
        + "on this device only: nothing is sent to a server, so they will not "
        + "follow you to another computer unless you export them to a file." }));
    });
  }

  /* ======================================================== projects drawer */

  function activeTab() {
    const b = $("#tabs button[aria-selected=true]");
    return b ? b.dataset.tab : "kinetics";
  }

  function activeSub(cat) {
    const b = $("#" + cat + "-subtabs button[aria-selected=true]");
    return b ? b.dataset.sub : null;
  }

  function snapshot() {
    // Everything needed to restore a working session. Raw text is stored
    // rather than parsed arrays so the user sees exactly what they typed.
    return {
      version: Projects.VERSION,
      savedAt: new Date().toISOString(),
      // What was on screen, so reopening a project restores the view and not
      // just the inputs. Fits are re-run rather than stored: the results run
      // to megabytes and would exhaust the browser's storage after a few
      // projects, whereas re-fitting takes a few seconds and cannot go stale.
      view: {
        tab: activeTab(),
        kineticsSub: activeSub("kinetics"),
        isothermSub: activeSub("isotherm"),
        kineticsFitted: !!STATE.kinetics.fit,
        isothermFitted: !!STATE.isotherm.fit,
        kineticsAdvised: !!STATE.kinetics.advice,
        isothermAdvised: !!STATE.isotherm.advice,
        thermoRun: !!STATE.thermo.result
      },
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
      thermoFigs: (function () {
        // only the styling travels; traces are rebuilt from the data on load
        const out = {};
        Object.keys(STATE.thermo.figures || {}).forEach(function (k) {
          const f = STATE.thermo.figures[k];
          out[k] = { style: f.style, traceStyle: f.traceStyle };
        });
        return out;
      })(),
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
      STATE[c].fit = null; STATE[c].advice = null; STATE[c].frames = null;
      $(c === "kinetics" ? "#kin-results" : "#iso-results").innerHTML = "";
      renderAdvice(c);
      if ($(c === "kinetics" ? "#kin-data" : "#iso-data").value.trim()) readData(c);
    });
    STATE.thermo.result = null;
    // seed the saved styling so the rebuilt figures pick it up through `prev`
    STATE.thermo.figures = p.thermoFigs || null;
    $("#th-results").innerHTML = "";

    return replayView(p.view);
  }

  // Re-run whatever had been computed when the project was saved, so the
  // results, figures and open tab come back rather than an empty right-hand
  // column. Each step is guarded: a project saved from a half-finished
  // session should still open.
  async function replayView(view) {
    if (!view) return;
    const jobs = [];
    if (view.kineticsFitted) jobs.push(["kinetics", "fit"]);
    if (view.isothermFitted) jobs.push(["isotherm", "fit"]);
    if (view.kineticsAdvised) jobs.push(["kinetics", "advise"]);
    if (view.isothermAdvised) jobs.push(["isotherm", "advise"]);

    if (jobs.length) toast(I18N.t("proj.rebuilding"), null, 6000);
    for (const [cat, what] of jobs) {
      try {
        if (what === "fit") await runFit(cat, { silent: true });
        else await runAdvisor(cat, { silent: true });
      } catch (e) {
        console.warn("could not replay", cat, what, e);
      }
    }
    if (view.thermoRun) {
      try { await runThermo({ silent: true }); }
      catch (e) { console.warn("could not replay thermodynamics", e); }
    }

    if (view.tab) {
      const b = $('#tabs button[data-tab="' + view.tab + '"]');
      if (b) b.click();
    }
    ["kinetics", "isotherm"].forEach(function (c) {
      const want = view[c + "Sub"];
      if (want && STATE[c].fit && $("#" + c + "-subtabs")) showSub(c, want);
    });
    window.scrollTo({ top: 0, behavior: "auto" });
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
              onclick: async function () {
                STATE.projectId = p.id; STATE.projectName = p.name;
                refreshProjectBadge();
                closeDrawer();
                await restore(p.payload);
                toast(I18N.t("proj.loaded"), "good");
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

      body.appendChild(el("div", { class: "section-title", text: I18N.t("sec.transfer") }));
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

      // The interpretation paragraphs, the domain warnings and the advisor's
      // reasons are composed in Python with the fitted numbers already inside
      // them, so re-rendering cannot translate them: they have to be written
      // again. The analyses are re-run silently, which costs well under a
      // second and leaves every setting and every result in place.
      if (bridge) {
        try { call("set_language", lang); } catch (e) { /* not booted yet */ }

        // The catalogue carries the model names, which are translated too,
        // so it is fetched again and the pickers rebuilt. Rebuilding clears
        // the checkboxes, so the current selection is carried across.
        try {
          const chosen = {};
          ["kinetics", "isotherm"].forEach(function (c) {
            const pref = c === "kinetics" ? "kin" : "iso";
            chosen[c] = $$("#" + pref + "-models input:checked")
              .map(function (b) { return b.value; });
          });
          CATALOGUE.isotherm = call("list_models", "isotherm").models;
          CATALOGUE.kinetics = call("list_models", "kinetics").models;
          ["kinetics", "isotherm"].forEach(function (c) {
            buildModelPicker(c);
            const pref = c === "kinetics" ? "kin" : "iso";
            $$("#" + pref + "-models input").forEach(function (b) {
              b.checked = chosen[c].indexOf(b.value) >= 0;
            });
          });
        } catch (e) { console.warn("catalogue refresh failed", e); }

        ["kinetics", "isotherm"].forEach(function (c) {
          if (STATE[c].fit) runFit(c, { silent: true });
          if (STATE[c].advice) runAdvisor(c, { silent: true });
        });
        if (STATE.thermo.result) runThermo({ silent: true });
      }

      // everything else is marked up, so a re-render is enough
      ["kinetics", "isotherm"].forEach(function (c) {
        if (STATE[c].fit) renderResults(c);
        renderAdvice(c);
      });
      if (STATE.thermo.result) renderThermo();
      buildPresetPickers();
      buildGuide();
    });

    Prefs.onChange(function () { redrawAllFigures(); });

    $$("[data-advise]").forEach(function (b) {
      b.onclick = function () { runAdvisor(b.dataset.advise); };
    });

    $$("[data-help]").forEach(function (b) {
      b.onclick = function (e) {
        // the button lives inside a <label>, so without this the click would
        // fall through and focus the field behind the dialog
        e.preventDefault();
        e.stopPropagation();
        showFieldHelp(b.dataset.help);
      };
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
    "<p>AdsorpFit fits adsorption data in your browser. Nothing is uploaded: ",
    "the Python scientific stack runs locally through WebAssembly, so your ",
    "unpublished data stays on your machine.</p>",

    "<h3>Getting a result</h3><ol>",
    "<li>Pick one of the built-in examples from the dropdown, or paste two ",
    "columns of your own. Column 1 is time (kinetics) or equilibrium ",
    "concentration (isotherms); column 2 is the loading q. A third column is ",
    "read as error bars, and on the isotherm tab a fourth is read as the ",
    "initial concentration C<sub>0</sub>, which enables R<sub>L</sub>.</li>",
    "<li>Fill in the experiment panel. The <em>?</em> beside a field explains ",
    "what it is for and whether you need it at all.</li>",
    "<li>Press <strong>Analyse my data</strong> to see which models your data ",
    "can support, then <strong>Fit models</strong>.</li></ol>",

    "<h3>The model advisor</h3>",
    "<p>Selecting twenty models and reporting whichever has the highest R² is ",
    "the commonest way to arrive at a mechanism the data never contained. The ",
    "advisor reads the shape of your raw data first: does the isotherm ",
    "plateau, is it linear or sigmoidal, did the kinetics reach equilibrium, ",
    "are there enough early points to fix a rate constant. It then runs a ",
    "quick trial fit and sorts every model into recommended, usable or not ",
    "advised, with the reason attached.</p>",
    "<p>Physics overrides statistics there. A model that predicts impossible ",
    "values is rejected however well it fits, and among models that are ",
    "statistically tied the simplest one is recommended.</p>",

    "<h3>Three things worth knowing before you report anything</h3>",

    "<p><strong>Do not rank models by R².</strong> R² can only increase when ",
    "you add a parameter, so comparing a two-parameter Langmuir against a ",
    "four-parameter Fritz–Schlünder on R² is guaranteed to favour the latter ",
    "whether or not the extra parameters mean anything. AdsorpFit ranks on ",
    "AICc and reports Akaike weights, so when two models are genuinely ",
    "indistinguishable (Δ &lt; 2) it says so instead of declaring a winner.</p>",

    "<p><strong>Non-linear regression is the correct method.</strong> ",
    "Linearising an adsorption model changes the error structure: plotting ",
    "t/q<sub>t</sub> against t puts t on both axes and manufactures a ",
    "correlation, which is the main reason pseudo-second-order appears to fit ",
    "almost every published dataset. AdsorpFit fits the untransformed ",
    "equation and shows the linear plots only for comparison, flagging cases ",
    "where the linearisation is flattering itself.</p>",

    "<p><strong>ΔG° depends on how you make K° dimensionless.</strong> ",
    "−RT ln K requires a dimensionless K. A Langmuir K<sub>L</sub> in L/mg is ",
    "not dimensionless, and different unit choices for the same experiment ",
    "give ΔG° values differing by tens of kJ/mol. The Thermodynamics tab ",
    "makes you choose a conversion route explicitly and states it in the ",
    "output, because it must be stated in your paper too.</p>",

    "<h3>Where models stop being valid</h3>",
    "<p>Several of these equations are unbounded. Temkin contains ",
    "ln(A<sub>T</sub>C<sub>e</sub>) and runs to minus infinity as ",
    "C<sub>e</sub> approaches zero; Harkins–Jura is singular at ",
    "C<sub>e</sub> = 10<sup>B</sup>; liquid-phase BET divides by ",
    "(C<sub>s</sub> − C<sub>e</sub>). Least squares has no objection to a ",
    "negative loading, so a fit can reach R² = 0.96 while predicting q = −14 ",
    "mg/g at your lowest point. AdsorpFit checks each model's domain against ",
    "your data before fitting and its fitted parameters afterwards, and ",
    "blocks the result rather than quietly reporting it.</p>",

    "<h3>Other checks it runs for you</h3><ul>",
    "<li>Whether a parameter's standard error exceeds the parameter itself, ",
    "meaning the data do not determine it.</li>",
    "<li>Whether q<sub>e,cal</sub> agrees with q<sub>e,exp</sub>. This ",
    "catches more bad kinetic fits than R² does.</li>",
    "<li>Whether a fitted q<sub>max</sub> lies far above the measured range, ",
    "making it an extrapolation rather than a measurement.</li>",
    "<li>Whether a three- or four-parameter model has collapsed onto a ",
    "simpler one: Sips with m = 1 is Langmuir, Redlich–Peterson with g = 1 is ",
    "Langmuir, Tóth with n = 1 is Langmuir.</li>",
    "<li>Whether a parameter has hit a physical bound.</li>",
    "<li>Whether the van't Hoff plot is curved, meaning ΔH° is not constant ",
    "over your temperature range.</li></ul>",

    "<h3>The workspace</h3><ul>",
    "<li><strong>Resize the columns</strong> by dragging the divider between ",
    "them, and any panel by the dotted handle along its bottom edge.</li>",
    "<li><strong>Move a panel</strong> by the grip in its header, within a ",
    "column or across to the other one.</li>",
    "<li><strong>Focus one panel</strong> over the whole window with the ",
    "expand button; Escape returns.</li>",
    "<li><strong>Projects</strong> save your data, settings, selected models ",
    "and figure styling under a name, and reopening one rebuilds the results ",
    "as well. They live in this browser, so export one to a file to move it ",
    "to another machine.</li>",
    "<li><strong>Settings</strong> holds the theme, background motion, layout ",
    "and density, and the language switch.</li></ul>",

    "<h3>Citing the models</h3>",
    "<p>Every model card carries its primary citation, reachable from the ",
    "<em>?</em> beside the model name, along with its equation, parameter ",
    "meanings and assumptions. Cite the original source (Lagergren 1898, ",
    "Ho &amp; McKay 1999, Langmuir 1918) rather than a recent paper that ",
    "happens to use the model.</p>",
    "<p>The built-in example data are real measurements from Wang et al. ",
    "(2021) <em>R. Soc. Open Sci.</em> <strong>8</strong>, 201789, with the ",
    "raw data released on Zenodo under CC0. If you publish anything derived ",
    "from them, cite that paper.</p>"
  ].join("");

  /* =================================================================== go */

  function start() {
    I18N.init();
    Prefs.init();
    I18N.apply(document);
    startBootFacts();
    wire();
    Layout.init();
    boot();
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
