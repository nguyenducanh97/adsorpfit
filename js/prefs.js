/* ==========================================================================
   AdsorpFit: display preferences and saved projects.

   Preferences (theme, background motion, layout, density) and projects both
   live in localStorage, which means they are per-browser and per-device.
   That is a deliberate trade: there is no server, so nothing you enter is
   ever transmitted, but a project saved here will not follow you to another
   machine unless you export it to a file.
   ========================================================================== */

const Prefs = (function () {
  "use strict";

  const KEY = "adsorpfit-prefs";
  const DEFAULTS = {
    theme: "auto",       // light | dark | auto
    motion: "full",      // full | calm | off
    layout: "side",      // side | right | stack
    density: "comfy"     // comfy | compact
  };

  let state = Object.assign({}, DEFAULTS);
  const listeners = [];

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) state = Object.assign({}, DEFAULTS, JSON.parse(raw));
    } catch (e) { /* private mode, blocked storage; defaults are fine */ }
    // honour the OS setting for people who asked for reduced motion, unless
    // they have explicitly chosen otherwise in this app
    try {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
          !localStorage.getItem(KEY)) {
        state.motion = "off";
      }
    } catch (e) {}
    return state;
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  function resolvedTheme() {
    if (state.theme !== "auto") return state.theme;
    try {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark" : "light";
    } catch (e) { return "light"; }
  }

  function applyAll() {
    const root = document.documentElement;
    root.setAttribute("data-theme", resolvedTheme());
    root.setAttribute("data-motion", state.motion);
    root.setAttribute("data-layout", state.layout);
    root.setAttribute("data-density", state.density);
    listeners.forEach(function (fn) { try { fn(state); } catch (e) {} });
  }

  function set(key, value) {
    if (!(key in DEFAULTS)) return;
    state[key] = value;
    save();
    applyAll();
  }

  function init() {
    load();
    applyAll();
    try {
      window.matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", function () {
          if (state.theme === "auto") applyAll();
        });
    } catch (e) {}
  }

  return {
    init: init, set: set, applyAll: applyAll, resolvedTheme: resolvedTheme,
    get: function (k) { return k ? state[k] : Object.assign({}, state); },
    onChange: function (fn) { listeners.push(fn); }
  };
})();


const Projects = (function () {
  "use strict";

  const KEY = "adsorpfit-projects";
  const VERSION = 1;

  function all() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) { return []; }
  }

  function persist(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
      return true;
    } catch (e) {
      // QuotaExceededError is the realistic failure here: a project carries
      // its raw data, and a few large datasets can fill the 5 MB budget.
      console.error("Could not save project", e);
      return false;
    }
  }

  function newId() {
    return "p" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  function save(name, payload, id) {
    const list = all();
    const now = new Date().toISOString();
    let rec;
    if (id) {
      rec = list.find(function (p) { return p.id === id; });
    }
    if (rec) {
      rec.name = name;
      rec.payload = payload;
      rec.modified = now;
    } else {
      rec = { id: newId(), name: name, created: now, modified: now,
              version: VERSION, payload: payload };
      list.unshift(rec);
    }
    return persist(list) ? rec : null;
  }

  function remove(id) {
    const list = all().filter(function (p) { return p.id !== id; });
    return persist(list);
  }

  function rename(id, name) {
    const list = all();
    const rec = list.find(function (p) { return p.id === id; });
    if (!rec) return false;
    rec.name = name;
    rec.modified = new Date().toISOString();
    return persist(list);
  }

  function get(id) {
    return all().find(function (p) { return p.id === id; }) || null;
  }

  function usage() {
    try {
      const raw = localStorage.getItem(KEY) || "";
      return { bytes: raw.length, count: all().length };
    } catch (e) { return { bytes: 0, count: 0 }; }
  }

  return { all: all, save: save, remove: remove, rename: rename,
           get: get, usage: usage, VERSION: VERSION };
})();
