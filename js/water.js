/* ==========================================================================
   AdsorpFit: background water motion.

   Two effects, both deliberately cheap so they never compete with the
   fitting work for CPU:

     1. Caustics: the rippling light pattern you see on the bottom of a
        pool. Rendered into a small offscreen canvas (about 160 x 90 px) and
        scaled up by the browser, which is what makes it affordable. Updated
        at ~20 fps rather than 60.

     2. Bubbles: a handful of DOM elements animated purely by CSS, so they
        cost nothing on the main thread.

   Both stop entirely when the tab is hidden, and respect
   prefers-reduced-motion.
   ========================================================================== */

(function () {
  "use strict";

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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

  function makeBubbles() {
    const host = document.getElementById("bubbles");
    if (!host) return;
    const n = reduced ? 6 : 18;
    for (let i = 0; i < n; i++) {
      const b = document.createElement("span");
      b.className = "bubble";
      // A wide spread of sizes reads as depth: the small ones sit far back,
      // the large ones near the glass.
      const size = 7 + Math.pow(Math.random(), 1.6) * 30;
      b.style.width = size + "px";
      b.style.height = size + "px";
      b.style.left = Math.random() * 100 + "%";
      b.style.setProperty("--bub",
        BUBBLE_HUES[Math.floor(Math.random() * BUBBLE_HUES.length)]);
      // bigger bubbles rise faster, as real ones do
      b.style.animationDuration = (26 - size * 0.42 + Math.random() * 14) + "s";
      b.style.animationDelay = (-Math.random() * 34) + "s";
      host.appendChild(b);
    }
  }

  /* --------------------------------------------------------------- caustics */
  function startCaustics() {
    const cv = document.getElementById("caustics");
    if (!cv || reduced) return;
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

    function play() { if (raf === null) raf = requestAnimationFrame(frame); }
    function pause() { if (raf !== null) { cancelAnimationFrame(raf); raf = null; } }

    document.addEventListener("visibilitychange", function () {
      document.hidden ? pause() : play();
    });
    play();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      makeBubbles(); startCaustics();
    });
  } else {
    makeBubbles();
    startCaustics();
  }
})();
