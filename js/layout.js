/* ==========================================================================
   AdsorpFit: manual layout control.

   Three things you can adjust by hand, all persisted per browser:

     1. Column split. Drag the bar between the controls and the results to
        give either side more room.
     2. Panel size and order. Every panel collapses from its header, and can
        be dragged by its header to a new position within its column.
     3. Plot height. Drag the grip under any figure to make it taller or
        shorter.

   State is keyed by panel id so it survives re-renders. Panels created at
   runtime (the results panel) are picked up by calling Layout.refresh().
   ========================================================================== */

const Layout = (function () {
  "use strict";

  const KEY = "adsorpfit-layout";
  let state = { split: {}, collapsed: {}, order: {}, plotH: {}, panelH: {} };

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) state = Object.assign(state, JSON.parse(raw));
    } catch (e) {}
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* ------------------------------------------------------ column splitter */

  function gridKey(grid) {
    const pane = grid.closest(".tabpane");
    return pane ? pane.id : "grid";
  }

  function applySplit(grid) {
    const k = gridKey(grid);
    const v = state.split[k];
    if (v) grid.style.setProperty("--split", v + "px");
    else grid.style.removeProperty("--split");
  }

  function setupSplitter(grid) {
    if (grid.dataset.splitReady) return;
    grid.dataset.splitReady = "1";

    const bar = document.createElement("div");
    bar.className = "col-splitter";
    bar.setAttribute("role", "separator");
    bar.setAttribute("aria-orientation", "vertical");
    bar.title = "Drag to resize, double-click to reset";
    const left = grid.querySelector(".col-left");
    const right = grid.querySelector(".col-right");
    if (!left || !right) return;
    grid.insertBefore(bar, right);

    let startX = 0, startW = 0, dragging = false;

    function down(e) {
      // A stacked layout has no second column to resize against.
      if (getComputedStyle(grid).gridTemplateColumns.split(" ").length < 3) return;
      dragging = true;
      startX = (e.touches ? e.touches[0].clientX : e.clientX);
      startW = left.getBoundingClientRect().width;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      e.preventDefault();
    }
    function move(e) {
      if (!dragging) return;
      const x = (e.touches ? e.touches[0].clientX : e.clientX);
      const total = grid.getBoundingClientRect().width;
      // keep both sides usable however far the pointer travels
      const w = Math.max(280, Math.min(total - 340, startW + (x - startX)));
      grid.style.setProperty("--split", w + "px");
    }
    function up() {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      state.split[gridKey(grid)] =
        Math.round(left.getBoundingClientRect().width);
      save();
      resizePlots();
    }

    bar.addEventListener("mousedown", down);
    bar.addEventListener("touchstart", down, { passive: false });
    window.addEventListener("mousemove", move);
    window.addEventListener("touchmove", move, { passive: false });
    window.addEventListener("mouseup", up);
    window.addEventListener("touchend", up);
    bar.addEventListener("dblclick", function () {
      delete state.split[gridKey(grid)];
      grid.style.removeProperty("--split");
      save();
      resizePlots();
    });

    applySplit(grid);
  }

  /* ------------------------------------------------------- panel controls */

  let panelSeq = 0;

  function panelKey(panel) {
    if (!panel.dataset.pkey) {
      // prefer a stable id from the panel's own content
      const h = panel.querySelector(".panel-head h2, .panel-head h3");
      const body = panel.querySelector(".panel-body");
      const id = (body && body.id) || (h && h.textContent.trim()) ||
                 ("panel" + (++panelSeq));
      panel.dataset.pkey = id.replace(/\s+/g, "-").toLowerCase().slice(0, 40);
    }
    return panel.dataset.pkey;
  }

  function decorate(panel) {
    const head = panel.querySelector(".panel-head");
    if (!head || panel.dataset.layoutReady) return;
    panel.dataset.layoutReady = "1";
    const key = panelKey(panel);

    const grip = document.createElement("span");
    grip.className = "panel-grip";
    grip.title = "Drag to reorder";
    grip.innerHTML =
      '<svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor">' +
      '<circle cx="5" cy="3" r="1.4"/><circle cx="11" cy="3" r="1.4"/>' +
      '<circle cx="5" cy="8" r="1.4"/><circle cx="11" cy="8" r="1.4"/>' +
      '<circle cx="5" cy="13" r="1.4"/><circle cx="11" cy="13" r="1.4"/></svg>';
    head.insertBefore(grip, head.firstChild);

    const toggle = document.createElement("button");
    toggle.className = "panel-toggle";
    toggle.type = "button";
    toggle.setAttribute("aria-label", "Collapse or expand this panel");
    toggle.innerHTML =
      '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" ' +
      'stroke="currentColor" stroke-width="2.2" stroke-linecap="round">' +
      '<path d="M4 6l4 4 4-4"/></svg>';
    toggle.onclick = function (e) {
      e.stopPropagation();
      panel.classList.toggle("collapsed");
      state.collapsed[key] = panel.classList.contains("collapsed");
      save();
      resizePlots();
    };
    head.appendChild(toggle);

    const focus = document.createElement("button");
    focus.className = "panel-focus-btn";
    focus.type = "button";
    focus.setAttribute("aria-label", "Focus this panel over the window");
    focus.innerHTML =
      '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
      'stroke-linejoin="round"><path d="M6 2H2v4M10 14h4v-4M14 6V2h-4M2 10v4h4"/>' +
      "</svg>";
    focus.onclick = function (e) { e.stopPropagation(); toggleFocus(panel); };
    head.appendChild(focus);

    if (state.collapsed[key]) panel.classList.add("collapsed");
    if (state.panelH[key]) {
      panel.style.height = state.panelH[key] + "px";
      panel.classList.add("sized");
    }

    setupDrag(panel, grip);
    addPanelResize(panel, key);
  }

  /* --------------------------------------------------------- focus a panel */

  let focused = null;

  function toggleFocus(panel) {
    if (focused === panel) { clearFocus(); return; }
    clearFocus();
    focused = panel;
    const back = document.createElement("div");
    back.className = "focus-back";
    back.onclick = clearFocus;
    document.body.appendChild(back);
    panel.classList.add("focused");
    panel.classList.remove("collapsed");
    document.addEventListener("keydown", escFocus);
    resizePlots();
  }

  function escFocus(e) { if (e.key === "Escape") clearFocus(); }

  function clearFocus() {
    document.querySelectorAll(".focus-back").forEach(function (n) { n.remove(); });
    if (focused) focused.classList.remove("focused");
    focused = null;
    document.removeEventListener("keydown", escFocus);
    resizePlots();
  }

  /* ----------------------------------------------- panel bottom-edge resize */

  function addPanelResize(panel, key) {
    const h = document.createElement("div");
    h.className = "panel-resize";
    h.title = "Drag to set this panel's height, double-click to fit its content";
    panel.appendChild(h);

    let startY = 0, startH = 0, dragging = false;
    function down(e) {
      dragging = true;
      startY = (e.touches ? e.touches[0].clientY : e.clientY);
      startH = panel.getBoundingClientRect().height;
      document.body.style.cursor = "row-resize";
      document.body.style.userSelect = "none";
      e.preventDefault();
      e.stopPropagation();
    }
    function move(e) {
      if (!dragging) return;
      const y = (e.touches ? e.touches[0].clientY : e.clientY);
      const nh = Math.max(90, startH + (y - startY));
      panel.style.height = nh + "px";
      panel.classList.add("sized");
    }
    function up() {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      state.panelH[key] = Math.round(panel.getBoundingClientRect().height);
      save();
      resizePlots();
    }
    h.addEventListener("mousedown", down);
    h.addEventListener("touchstart", down, { passive: false });
    window.addEventListener("mousemove", move);
    window.addEventListener("touchmove", move, { passive: false });
    window.addEventListener("mouseup", up);
    window.addEventListener("touchend", up);
    h.addEventListener("dblclick", function () {
      delete state.panelH[key];
      panel.style.height = "";
      panel.classList.remove("sized");
      save();
      resizePlots();
    });
  }

  /* --------------------------------------------------------- panel reorder */

  function setupDrag(panel, grip) {
    let placeholder = null, col = null, startY = 0, offset = 0, dragging = false;

    function down(e) {
      col = panel.parentElement;
      if (!col) return;
      dragging = true;
      const rect = panel.getBoundingClientRect();
      startY = (e.touches ? e.touches[0].clientY : e.clientY);
      offset = startY - rect.top;

      placeholder = document.createElement("div");
      placeholder.className = "panel-placeholder";
      placeholder.style.height = rect.height + "px";

      panel.style.width = rect.width + "px";
      panel.style.position = "fixed";
      panel.style.left = rect.left + "px";
      panel.style.top = rect.top + "px";
      panel.style.zIndex = "120";
      panel.classList.add("dragging");
      col.insertBefore(placeholder, panel);
      document.body.style.userSelect = "none";
      e.preventDefault();
    }

    function move(e) {
      if (!dragging) return;
      const y = (e.touches ? e.touches[0].clientY : e.clientY);
      panel.style.top = (y - offset) + "px";

      // A panel can move to the other column as well as within its own, so
      // first work out which column the pointer is currently over.
      const x = (e.touches ? e.touches[0].clientX : e.clientX);
      const grid = col.closest(".grid-2");
      if (grid) {
        const cols = grid.querySelectorAll(".col-left, .col-right");
        for (const c of cols) {
          const cr = c.getBoundingClientRect();
          if (x >= cr.left && x <= cr.right) { col = c; break; }
        }
      }

      // then the sibling whose midpoint the pointer has passed
      const sibs = Array.prototype.filter.call(col.children, function (n) {
        return n !== panel && n !== placeholder && n.classList.contains("panel");
      });
      let target = null;
      for (const s of sibs) {
        const r = s.getBoundingClientRect();
        if (y < r.top + r.height / 2) { target = s; break; }
      }
      if (target) col.insertBefore(placeholder, target);
      else col.appendChild(placeholder);
    }

    function up() {
      if (!dragging) return;
      dragging = false;
      panel.classList.remove("dragging");
      panel.style.position = panel.style.left = panel.style.top =
        panel.style.width = panel.style.zIndex = "";
      document.body.style.userSelect = "";
      if (placeholder) {
        col.insertBefore(panel, placeholder);
        placeholder.remove();
        placeholder = null;
      }
      const grid = col.closest(".grid-2");
      if (grid) grid.querySelectorAll(".col-left, .col-right").forEach(rememberOrder);
      else rememberOrder(col);
      resizePlots();
    }

    grip.addEventListener("mousedown", down);
    grip.addEventListener("touchstart", down, { passive: false });
    window.addEventListener("mousemove", move);
    window.addEventListener("touchmove", move, { passive: false });
    window.addEventListener("mouseup", up);
    window.addEventListener("touchend", up);
  }

  function colKey(col) {
    const pane = col.closest(".tabpane");
    return (pane ? pane.id : "x") + ":" +
           (col.classList.contains("col-left") ? "L" : "R");
  }

  function rememberOrder(col) {
    state.order[colKey(col)] = $$(".panel", col)
      .filter(function (p) { return p.parentElement === col; })
      .map(panelKey);
    save();
  }

  function applyOrder(col) {
    const want = state.order[colKey(col)];
    if (!want || !want.length) return;
    const have = {};
    $$(".panel", col).forEach(function (p) {
      if (p.parentElement === col) have[panelKey(p)] = p;
    });
    want.forEach(function (k) { if (have[k]) col.appendChild(have[k]); });
  }

  /* ----------------------------------------------------------- plot resize */

  function addPlotHandle(plot) {
    if (plot.dataset.resizeReady) return;
    plot.dataset.resizeReady = "1";
    const key = plot.id;
    if (state.plotH[key]) plot.style.height = state.plotH[key] + "px";

    const h = document.createElement("div");
    h.className = "plot-resize";
    h.title = "Drag to change the plot height, double-click to reset";
    plot.parentElement.insertBefore(h, plot.nextSibling);

    let startY = 0, startH = 0, dragging = false;
    function down(e) {
      dragging = true;
      startY = (e.touches ? e.touches[0].clientY : e.clientY);
      startH = plot.getBoundingClientRect().height;
      document.body.style.cursor = "row-resize";
      document.body.style.userSelect = "none";
      e.preventDefault();
    }
    function move(e) {
      if (!dragging) return;
      const y = (e.touches ? e.touches[0].clientY : e.clientY);
      const nh = Math.max(220, Math.min(1400, startH + (y - startY)));
      plot.style.height = nh + "px";
      if (window.Plotly && plot.data) Plotly.Plots.resize(plot);
    }
    function up() {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      state.plotH[key] = Math.round(plot.getBoundingClientRect().height);
      save();
    }
    h.addEventListener("mousedown", down);
    h.addEventListener("touchstart", down, { passive: false });
    window.addEventListener("mousemove", move);
    window.addEventListener("touchmove", move, { passive: false });
    window.addEventListener("mouseup", up);
    window.addEventListener("touchend", up);
    h.addEventListener("dblclick", function () {
      delete state.plotH[key];
      plot.style.height = "";
      save();
      if (window.Plotly && plot.data) Plotly.Plots.resize(plot);
    });
  }

  function resizePlots() {
    if (!window.Plotly) return;
    setTimeout(function () {
      $$(".js-plotly-plot").forEach(function (p) {
        try { Plotly.Plots.resize(p); } catch (e) {}
      });
    }, 60);
  }

  /* ------------------------------------------------------------------ api */

  function refresh() {
    $$(".grid-2").forEach(setupSplitter);
    $$(".grid-2").forEach(applySplit);
    $$(".panel").forEach(decorate);
    $$(".col-left, .col-right").forEach(applyOrder);
    $$("[id$='-plot'], #th-fig-preview").forEach(function (p) {
      if (p.id) addPlotHandle(p);
    });
  }

  function reset() {
    state = { split: {}, collapsed: {}, order: {}, plotH: {}, panelH: {} };
    save();
    $$(".grid-2").forEach(function (g) { g.style.removeProperty("--split"); });
    $$(".panel").forEach(function (p) { p.classList.remove("collapsed"); });
    $$("[id$='-plot']").forEach(function (p) { p.style.height = ""; });
    $$(".panel").forEach(function (p) {
      p.style.height = ""; p.classList.remove("sized", "focused");
    });
    clearFocus();
    resizePlots();
  }

  function init() {
    load();
    refresh();
    window.addEventListener("resize", resizePlots);
  }

  return { init: init, refresh: refresh, reset: reset,
           resizePlots: resizePlots, clearFocus: clearFocus };
})();
