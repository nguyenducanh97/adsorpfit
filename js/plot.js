/* ==========================================================================
   AdsorpFit — figure engine.

   Two renderers share one style object:

     * Plotly draws the interactive preview in the page (fast, zoomable,
       hover readout).
     * Matplotlib, running in Pyodide, renders the publication export.

   Keeping a single style object means what you see in the preview is what
   comes out of the export. `toMatplotlib()` translates the style and traces
   into the payload `bridge.render_figure` expects, including the marker and
   dash-pattern vocabulary, which differs between the two libraries.
   ========================================================================== */

const Fig = (function () {
  "use strict";

  /* ------------------------------------------------------------- defaults */

  const DEFAULT_STYLE = {
    // canvas
    width_cm: 8.5, height_cm: 6.5, dpi: 600, transparent: false, tight: true,
    // type
    font_family: "DejaVu Sans", font_size: 9, label_weight: "normal",
    title_weight: "normal", tick_scale: 0.92,
    // labels
    title: "", x_label: "", y_label: "", annotation: "",
    ann_x: 0.05, ann_y: 0.94,
    // axes
    x_log: false, y_log: false,
    x_min: null, x_max: null, y_min: null, y_max: null,
    axis_width: 0.9, box: true, mirror_ticks: true, minor_ticks: true,
    tick_direction: "in", tick_length: 4,
    // grid
    grid: false, grid_which: "major", grid_style: ":", grid_width: 0.6,
    grid_color: "#b8c4cc", grid_alpha: 0.8,
    // legend
    legend: true, legend_loc: "lower right", legend_scale: 0.88,
    legend_frame: false, legend_cols: 1, legend_edge: "#333333",
    legend_handle: 1.6, legend_spacing: 0.35,
    pad: 0.3, quality: 95, tiff_compression: "tiff_lzw"
  };

  // Plotly symbol  ->  matplotlib marker
  const MARKERS = {
    "circle": "o", "square": "s", "diamond": "D", "triangle-up": "^",
    "triangle-down": "v", "triangle-left": "<", "triangle-right": ">",
    "cross": "P", "x": "X", "star": "*", "pentagon": "p", "hexagon": "h",
    "circle-open": "o", "square-open": "s", "diamond-open": "D",
    "triangle-up-open": "^"
  };
  const OPEN_MARKERS = new Set(["circle-open", "square-open", "diamond-open",
                                "triangle-up-open"]);

  // Plotly dash  ->  matplotlib linestyle
  const DASHES = {
    "solid": "-", "dash": "--", "dot": ":", "dashdot": "-.",
    "longdash": (0, [8, 3]), "longdashdot": "-."
  };
  const DASH_MPL = {
    "solid": "-", "dash": "--", "dot": ":", "dashdot": "-.",
    "longdash": "--", "longdashdot": "-."
  };

  const LEGEND_POS = {
    "upper left": { x: 0.02, y: 0.98, xanchor: "left", yanchor: "top" },
    "upper right": { x: 0.98, y: 0.98, xanchor: "right", yanchor: "top" },
    "lower left": { x: 0.02, y: 0.02, xanchor: "left", yanchor: "bottom" },
    "lower right": { x: 0.98, y: 0.02, xanchor: "right", yanchor: "bottom" },
    "upper center": { x: 0.5, y: 0.98, xanchor: "center", yanchor: "top" },
    "lower center": { x: 0.5, y: 0.02, xanchor: "center", yanchor: "bottom" },
    "center left": { x: 0.02, y: 0.5, xanchor: "left", yanchor: "middle" },
    "center right": { x: 0.98, y: 0.5, xanchor: "right", yanchor: "middle" },
    "best": { x: 0.98, y: 0.02, xanchor: "right", yanchor: "bottom" }
  };

  /* Colour-blind-safe qualitative sequence (Okabe & Ito), reordered so the
     first two - blue for data, vermillion for the fit - are the pair most
     often needed and are distinguishable in greyscale as well. */
  const PALETTE = [
    "#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00",
    "#56B4E9", "#7B5EA7", "#8C564B", "#333333", "#17A2B8"
  ];

  const SYMBOL_CYCLE = ["circle", "square", "triangle-up", "diamond",
                        "triangle-down", "pentagon", "hexagon", "star"];

  function newStyle(over) { return Object.assign({}, DEFAULT_STYLE, over || {}); }

  /* --------------------------------------------------------- Plotly render */

  function mathify(s) {
    // Accept LaTeX-ish input in the label boxes and show it properly in
    // Plotly, which understands a subset via MathJax-free <sub>/<sup>.
    if (!s) return "";
    return String(s)
      .replace(/\$/g, "")
      .replace(/\^\{([^}]*)\}/g, "<sup>$1</sup>")
      .replace(/\^(-?\w)/g, "<sup>$1</sup>")
      .replace(/_\{([^}]*)\}/g, "<sub>$1</sub>")
      .replace(/_(\w)/g, "<sub>$1</sub>")
      .replace(/\\mathrm\{([^}]*)\}/g, "$1")
      .replace(/\\,/g, " ");
  }

  function draw(divId, traces, style, theme) {
    const s = Object.assign({}, DEFAULT_STYLE, style || {});
    const dark = theme === "dark";
    const fg = dark ? "#dbeef5" : "#0d2b38";
    const grid = dark ? "#1b435a" : s.grid_color;
    const paper = dark ? "#0a2130" : "#ffffff";

    // Hidden series stay in the array with visible:false rather than being
    // removed. Plotly.react diffs traces by array position, so dropping one
    // shifts every trace below it: colours jump to the next series and traces
    // can vanish outright. Keeping the array length and order fixed makes
    // toggling stable.
    const pdata = traces.map(function (t, i) {
      const colour = t.color || PALETTE[i % PALETTE.length];
      const vis = t.visible === false ? false : true;
      if (t.kind === "line") {
        return {
          x: t.x, y: t.y, name: t.name, type: "scatter", mode: "lines",
          visible: vis, showlegend: vis,
          line: { color: colour, width: t.line_width || 2,
                  dash: t.dash || "solid", shape: "spline", smoothing: 0.4 },
          hovertemplate: "%{x:.4g}, %{y:.4g}<extra>" + (t.name || "") + "</extra>"
        };
      }
      const sym = t.symbol || SYMBOL_CYCLE[i % SYMBOL_CYCLE.length];
      const open = OPEN_MARKERS.has(sym);
      const tr = {
        x: t.x, y: t.y, name: t.name, type: "scatter", mode: "markers",
        visible: vis, showlegend: vis,
        marker: {
          symbol: sym, size: (t.marker_size || 5) * 1.7,
          color: open ? "rgba(0,0,0,0)" : (t.marker_fill || colour),
          line: { color: t.marker_edge || colour,
                  width: t.marker_edge_width || 1.2 }
        },
        hovertemplate: "%{x:.4g}, %{y:.4g}<extra>" + (t.name || "") + "</extra>"
      };
      if (t.yerr && t.yerr.length) {
        tr.error_y = { type: "data", array: t.yerr, visible: true,
                       color: t.error_color || colour,
                       thickness: t.error_width || 1, width: (t.capsize || 3) };
      }
      if (t.xerr && t.xerr.length) {
        tr.error_x = { type: "data", array: t.xerr, visible: true,
                       color: t.error_color || colour,
                       thickness: t.error_width || 1, width: (t.capsize || 3) };
      }
      return tr;
    });

    const ax = {
      showline: true, linecolor: fg, linewidth: s.axis_width * 1.3,
      mirror: s.mirror_ticks ? "ticks" : false,
      ticks: s.tick_direction === "in" ? "inside" : "outside",
      ticklen: s.tick_length, tickwidth: s.axis_width * 1.2, tickcolor: fg,
      tickfont: { size: s.font_size * s.tick_scale * 1.45, color: fg,
                  family: cssFont(s.font_family) },
      showgrid: !!s.grid, gridcolor: grid,
      gridwidth: s.grid_width * 1.2,
      zeroline: false, automargin: true,
      minor: s.minor_ticks
        ? { ticks: s.tick_direction === "in" ? "inside" : "outside",
            ticklen: s.tick_length * 0.55, tickcolor: fg,
            showgrid: s.grid && s.grid_which === "both", gridcolor: grid }
        : {}
    };

    const layout = {
      paper_bgcolor: s.transparent ? "rgba(0,0,0,0)" : paper,
      plot_bgcolor: s.transparent ? "rgba(0,0,0,0)" : paper,
      font: { family: cssFont(s.font_family), size: s.font_size * 1.45, color: fg },
      margin: { l: 64, r: 18, t: s.title ? 42 : 16, b: 56 },
      title: s.title ? { text: mathify(s.title), font: { size: s.font_size * 1.65 } } : undefined,
      xaxis: Object.assign({}, ax, {
        title: { text: mathify(s.x_label), font: { size: s.font_size * 1.55 },
                 standoff: 12 },
        type: s.x_log ? "log" : "linear",
        range: rangeFor(s.x_min, s.x_max, s.x_log)
      }),
      yaxis: Object.assign({}, ax, {
        title: { text: mathify(s.y_label), font: { size: s.font_size * 1.55 },
                 standoff: 12 },
        type: s.y_log ? "log" : "linear",
        range: rangeFor(s.y_min, s.y_max, s.y_log)
      }),
      showlegend: !!s.legend,
      legend: Object.assign({}, LEGEND_POS[s.legend_loc] || LEGEND_POS["lower right"], {
        font: { size: s.font_size * s.legend_scale * 1.45, color: fg },
        bgcolor: s.legend_frame ? (dark ? "rgba(10,33,48,.9)" : "rgba(255,255,255,.9)")
                                : "rgba(0,0,0,0)",
        bordercolor: s.legend_frame ? s.legend_edge : "rgba(0,0,0,0)",
        borderwidth: s.legend_frame ? 1 : 0,
        orientation: s.legend_cols > 1 ? "h" : "v"
      }),
      hovermode: "closest",
      annotations: s.annotation ? [{
        text: mathify(s.annotation), xref: "paper", yref: "paper",
        x: s.ann_x, y: s.ann_y, showarrow: false,
        font: { size: s.font_size * 1.32, color: fg },
        xanchor: "left", yanchor: "top"
      }] : []
    };

    Plotly.react(divId, pdata, layout, {
      responsive: true, displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d", "toggleSpikelines"],
      toImageButtonOptions: { format: "png", scale: 3 }
    });
  }

  function rangeFor(lo, hi, isLog) {
    if (lo === null || hi === null || lo === "" || hi === "") return undefined;
    const a = Number(lo), b = Number(hi);
    if (!isFinite(a) || !isFinite(b)) return undefined;
    return isLog ? [Math.log10(Math.max(a, 1e-12)), Math.log10(Math.max(b, 1e-12))]
                 : [a, b];
  }

  function cssFont(name) {
    // Matplotlib's built-in families mapped to web-safe stacks so the
    // preview approximates the export.
    const map = {
      "DejaVu Sans": "Inter, 'DejaVu Sans', Arial, sans-serif",
      "DejaVu Serif": "'DejaVu Serif', Georgia, serif",
      "Arial": "Arial, Helvetica, sans-serif",
      "Helvetica": "Helvetica, Arial, sans-serif",
      "Times New Roman": "'Times New Roman', Times, serif",
      "Calibri": "Calibri, 'Segoe UI', sans-serif",
      "Cambria": "Cambria, Georgia, serif",
      "Georgia": "Georgia, serif",
      "Courier New": "'Courier New', monospace",
      "STIXGeneral": "'STIX Two Text', 'Times New Roman', serif"
    };
    return map[name] || name;
  }

  /* --------------------------------------------------- matplotlib payload */

  function toMatplotlib(traces, style, format) {
    const s = Object.assign({}, DEFAULT_STYLE, style || {});
    // Colours are resolved against the FULL trace list so a series keeps its
    // colour whether or not its neighbours are visible; only then are the
    // hidden ones dropped, since the export has no concept of visibility.
    const out = traces.map(function (t, i) {
      const colour = t.color || PALETTE[i % PALETTE.length];
      if (t.visible === false) return null;
      if (t.kind === "line") {
        return {
          kind: "line", x: t.x, y: t.y, name: t.name, color: colour,
          line_width: t.line_width || 1.4,
          line_style: DASH_MPL[t.dash || "solid"] || "-",
          zorder: 2 + i * 0.01
        };
      }
      const sym = t.symbol || SYMBOL_CYCLE[i % SYMBOL_CYCLE.length];
      return {
        kind: "scatter", x: t.x, y: t.y, name: t.name,
        marker: MARKERS[sym] || "o",
        marker_size: t.marker_size || 5,
        marker_fill: OPEN_MARKERS.has(sym) ? "none" : (t.marker_fill || colour),
        marker_edge: t.marker_edge || colour,
        marker_edge_width: t.marker_edge_width || 1.0,
        color: colour,
        yerr: t.yerr && t.yerr.length ? t.yerr : null,
        xerr: t.xerr && t.xerr.length ? t.xerr : null,
        error_color: t.error_color || colour,
        error_width: t.error_width || 0.8,
        capsize: t.capsize || 2.5,
        zorder: 3 + i * 0.01
      };
    }).filter(Boolean);
    return { traces: out, style: s, format: format || "png", dpi: s.dpi };
  }

  /* ------------------------------------------------------ style control UI */

  function buildControls(host, style, onChange, opts) {
    opts = opts || {};
    host.innerHTML = "";

    function group(title, open, rows) {
      const d = document.createElement("details");
      d.className = "sty";
      if (open) d.open = true;
      d.innerHTML = "<summary>" + title + "</summary>";
      const b = document.createElement("div");
      b.className = "sb";
      rows.forEach(function (r) { b.appendChild(r); });
      d.appendChild(b);
      host.appendChild(d);
      return d;
    }

    function fire() { onChange(style); }

    function text(key, label, placeholder) {
      const w = document.createElement("div");
      w.className = "mini-field";
      w.innerHTML = '<label class="mini-label">' + label + "</label>";
      const inp = document.createElement("input");
      inp.type = "text";
      inp.value = style[key] == null ? "" : style[key];
      if (placeholder) inp.placeholder = placeholder;
      inp.oninput = function () { style[key] = inp.value; fire(); };
      w.appendChild(inp);
      return w;
    }

    function num(key, label, step, min, max, nullable) {
      const w = document.createElement("div");
      w.className = "mini-field";
      w.innerHTML = '<label class="mini-label">' + label + "</label>";
      const inp = document.createElement("input");
      inp.type = "number";
      inp.step = step == null ? "any" : step;
      if (min != null) inp.min = min;
      if (max != null) inp.max = max;
      inp.value = style[key] == null ? "" : style[key];
      inp.oninput = function () {
        const v = inp.value === "" ? (nullable ? null : style[key]) : Number(inp.value);
        style[key] = v;
        fire();
      };
      w.appendChild(inp);
      return w;
    }

    function pick(key, label, options) {
      const w = document.createElement("div");
      w.className = "mini-field";
      w.innerHTML = '<label class="mini-label">' + label + "</label>";
      const sel = document.createElement("select");
      options.forEach(function (o) {
        const val = Array.isArray(o) ? o[0] : o;
        const lab = Array.isArray(o) ? o[1] : o;
        const op = document.createElement("option");
        op.value = val; op.textContent = lab;
        if (String(style[key]) === String(val)) op.selected = true;
        sel.appendChild(op);
      });
      sel.onchange = function () {
        const v = sel.value;
        style[key] = (v === "true") ? true : (v === "false") ? false :
                     (isFinite(Number(v)) && v !== "") ? Number(v) : v;
        fire();
      };
      w.appendChild(sel);
      return w;
    }

    function check(key, label) {
      const l = document.createElement("label");
      l.className = "inline-check";
      const inp = document.createElement("input");
      inp.type = "checkbox";
      inp.checked = !!style[key];
      inp.onchange = function () { style[key] = inp.checked; fire(); };
      l.appendChild(inp);
      l.appendChild(document.createTextNode(label));
      return l;
    }

    function colour(key, label) {
      const w = document.createElement("div");
      w.className = "mini-field";
      w.innerHTML = '<label class="mini-label">' + label + "</label>";
      const inp = document.createElement("input");
      inp.type = "color";
      inp.value = style[key] || "#000000";
      inp.oninput = function () { style[key] = inp.value; fire(); };
      w.appendChild(inp);
      return w;
    }

    function pair(a, b) {
      const d = document.createElement("div");
      d.className = "row c2";
      d.appendChild(a); d.appendChild(b);
      return d;
    }

    group("Labels & title", true, [
      text("x_label", "X-axis label", "$C_e$ (mg L$^{-1}$)"),
      text("y_label", "Y-axis label", "$q_e$ (mg g$^{-1}$)"),
      text("title", "Title (blank for none)"),
      text("annotation", "Panel annotation, e.g. (a)"),
      pair(num("ann_x", "annotation x (0–1)", 0.01),
           num("ann_y", "annotation y (0–1)", 0.01))
    ]);

    group("Typography", false, [
      pick("font_family", "Font family", [
        "DejaVu Sans", "DejaVu Serif", "Arial", "Helvetica",
        "Times New Roman", "Calibri", "Cambria", "Georgia",
        "Courier New", "STIXGeneral"
      ]),
      pair(num("font_size", "Base size (pt)", 0.5, 4, 32),
           num("tick_scale", "Tick label scale", 0.01, 0.4, 2)),
      pair(pick("label_weight", "Axis label weight", ["normal", "bold"]),
           pick("title_weight", "Title weight", ["normal", "bold"]))
    ]);

    group("Axes & ticks", false, [
      pair(check("x_log", "Log X"), check("y_log", "Log Y")),
      pair(num("x_min", "X min (blank = auto)", null, null, null, true),
           num("x_max", "X max", null, null, null, true)),
      pair(num("y_min", "Y min (blank = auto)", null, null, null, true),
           num("y_max", "Y max", null, null, null, true)),
      pair(pick("tick_direction", "Tick direction", ["in", "out"]),
           num("tick_length", "Tick length", 0.5, 0, 20)),
      pair(num("axis_width", "Axis line width", 0.1, 0.1, 5),
           pick("box", "Frame", [[true, "full box"], [false, "left + bottom"]])),
      check("mirror_ticks", "Mirror ticks on top and right"),
      check("minor_ticks", "Show minor ticks")
    ]);

    group("Grid", false, [
      check("grid", "Show grid"),
      pick("grid_which", "Apply to", [["major", "major only"], ["both", "major + minor"]]),
      pick("grid_style", "Line style",
           [["-", "solid"], ["--", "dashed"], [":", "dotted"], ["-.", "dash-dot"]]),
      pair(num("grid_width", "Width", 0.1, 0.1, 3),
           num("grid_alpha", "Opacity", 0.05, 0, 1)),
      colour("grid_color", "Colour")
    ]);

    group("Legend", false, [
      check("legend", "Show legend"),
      pick("legend_loc", "Position", [
        "best", "upper left", "upper right", "lower left", "lower right",
        "upper center", "lower center", "center left", "center right"
      ]),
      pair(num("legend_scale", "Font scale", 0.01, 0.3, 2),
           num("legend_cols", "Columns", 1, 1, 6)),
      check("legend_frame", "Draw a frame around it"),
      pair(num("legend_handle", "Handle length", 0.1, 0.3, 5),
           num("legend_spacing", "Row spacing", 0.05, 0, 3))
    ]);

    group("Canvas & export", false, [
      pair(num("width_cm", "Width (cm)", 0.1, 2, 40),
           num("height_cm", "Height (cm)", 0.1, 2, 40)),
      pick("dpi", "Resolution (dpi)",
           [[150, "150 — screen"], [300, "300 — journal minimum"],
            [600, "600 — journal line art"], [900, "900"], [1200, "1200 — maximum"]]),
      check("transparent", "Transparent background"),
      check("tight", "Trim whitespace (tight bounding box)"),
      num("pad", "Padding", 0.05, 0, 3)
    ]);

    const presets = document.createElement("div");
    presets.className = "mini-field";
    presets.innerHTML = '<label class="mini-label">Journal size presets</label>';
    const pr = document.createElement("div");
    pr.className = "btn-row";
    [["Single column", 8.5, 6.5], ["1.5 column", 12.0, 8.5],
     ["Double column", 17.4, 10.0], ["Square", 9.0, 9.0]
    ].forEach(function (p) {
      const b = document.createElement("button");
      b.className = "btn sm";
      b.textContent = p[0];
      b.onclick = function () {
        style.width_cm = p[1]; style.height_cm = p[2];
        buildControls(host, style, onChange, opts);
        fire();
      };
      pr.appendChild(b);
    });
    presets.appendChild(pr);
    host.appendChild(presets);
  }

  return {
    DEFAULT_STYLE: DEFAULT_STYLE, PALETTE: PALETTE, SYMBOL_CYCLE: SYMBOL_CYCLE,
    MARKERS: MARKERS, newStyle: newStyle, draw: draw,
    toMatplotlib: toMatplotlib, buildControls: buildControls, mathify: mathify
  };
})();
