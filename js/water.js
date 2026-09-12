/* ==========================================================================
   AdsorpFit: background water motion.

   Two effects, both deliberately cheap so they never compete with the
   fitting work for CPU:

     1. Caustics: the rippling light pattern you see on the bottom of a
        pool. Rendered into a small offscreen canvas (about 160 x 90 px) and
        scaled up by the browser, which is what makes it affordable. Updated
        at ~20 fps rather than 60.

     2. Bubbles: a few dozen DOM elements animated purely by CSS, so they
        cost nothing on the main thread.

   Both stop when the tab is hidden.

   On the setting that governs them: this file reads data-motion, which is
   what Prefs writes, and nothing here consults prefers-reduced-motion
   directly. That is the whole point. The operating system's setting decides
   the default, and Prefs folds it in on first visit, but once a reader
   opens Settings and picks Full they have asked for motion on this page and
   must get it. An earlier version captured the OS preference once at load
   into a const, which meant a machine with Windows animation effects
   switched off could never show the caustics no matter what the reader
   chose, because nothing re-read it.
   ========================================================================== */

(function () {
  "use strict";

  /* Absent means Prefs has not run yet, and the media query in style.css is
     in charge for that instant. Treat it as full here. */
  function motion() {
    return document.documentElement.getAttribute("data-motion") || "full";
  }

  function wantsMotion() { return motion() !== "off"; }

  /* ---------------------------------------------------------------- bubbles */

  // Water tones drawn from the SWAT palette, plus a couple of cooler and
  // warmer neighbours so the drift has some variety instead of one flat hue.
  const BUBBLE_HUES = [
    "#37c8cf",   // SWAT cyan
    "#6fdce1",   // pale aqua
    "#2aa9bd",   // teal
    "#5cc6d8",   // sky
    "#7fe3c9",   // mint
    "#4fb3e8",   // cornflower
    "#a6ebee",   // ice
    "#3fd0a8"    // sea green
  ];

  const N_BUBBLES = 46;

  function makeBubbles() {
    const host = document.getElementById("bubbles");
    if (!host || host.children.length) return;
    for (let i = 0; i < N_BUBBLES; i++) {
      const b = document.createElement("span");
      b.className = "bubble";
      // Small, with a long tail of even smaller ones: raising the random
      // number to a power biases the draw towards the bottom of the range,
      // so most are fine specks and only a few are large enough to read as
      // near the glass. Many small bubbles are easier to ignore than a few
      // big ones, which is the point of the density.
      const size = 3.5 + Math.pow(Math.random(), 1.9) * 13;
      b.style.width = size + "px";
      b.style.height = size + "px";
      b.style.left = Math.random() * 100 + "%";
      b.style.setProperty("--bub",
        BUBBLE_HUES[Math.floor(Math.random() * BUBBLE_HUES.length)]);
      // bigger bubbles rise faster, as real ones do
      b.style.animationDuration = (34 - size * 0.55 + Math.random() * 16) + "s";
      b.style.animationDelay = (-Math.random() * 40) + "s";
      host.appendChild(b);
    }
  }

  /* --------------------------------------------------------------- caustics */
  function startCaustics() {
    const cv = document.getElementById("caustics");
    if (!cv) return;
    const ctx = cv.getContext("2d", { alpha: true });
    if (!ctx) return;

    // Small internal resolution; the CSS size does the upscaling for free.
    const W = 168, H = 96;
    cv.width = W;
    cv.height = H;

    const img = ctx.createImageData(W, H);
    const data = img.data;
    let t = 0;
    let raf = null;
    let last = 0;

    function frame(now) {
      raf = requestAnimationFrame(frame);
      if (now - last < 50) return;          // cap at ~20 fps
      last = now;
      t += 0.045;

      for (let y = 0; y < H; y++) {
        const fy = y / H;
        for (let x = 0; x < W; x++) {
          const fx = x / W;
          // Three interfering wave trains at different angles and speeds.
          // Their product, sharpened by a power, gives the bright filament
          // pattern characteristic of real caustics.
          const a = Math.sin((fx * 9.1 + t) + Math.sin(fy * 5.3 - t * 0.7) * 1.7);
          const b = Math.sin((fy * 7.4 - t * 0.85) + Math.sin(fx * 6.1 + t * 0.6) * 1.5);
          const c = Math.sin((fx * 4.2 + fy * 5.8 + t * 1.15));
          let v = (a * b + c * 0.45) * 0.5 + 0.5;
          v = Math.pow(Math.max(0, v), 4.2);

          const i = (y * W + x) * 4;
          data[i] = 210 + v * 45;
          data[i + 1] = 240 + v * 15;
          data[i + 2] = 255;
          data[i + 3] = v * 190;
        }
      }
      ctx.putImageData(img, 0, 0);
    }

    function play() {
      if (raf === null && !document.hidden && wantsMotion()) {
        last = 0;
        raf = requestAnimationFrame(frame);
      }
    }
    function pause() {
      if (raf !== null) { cancelAnimationFrame(raf); raf = null; }
    }

    document.addEventListener("visibilitychange", function () {
      document.hidden ? pause() : play();
    });

    // Follow the setting while the page is open, so choosing Full in
    // Settings starts the caustics immediately rather than on next load.
    // A MutationObserver rather than a Prefs callback keeps this file
    // independent of load order.
    new MutationObserver(function () {
      wantsMotion() ? play() : pause();
    }).observe(document.documentElement,
               { attributes: true, attributeFilter: ["data-motion"] });

    play();
  }

  function boot() {
    makeBubbles();
    startCaustics();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
