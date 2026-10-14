# -*- coding: utf-8 -*-
"""Build the public landing page at the site root.

The application moved behind a password, and a login box has nothing in it
for a search engine to read. This page is what stays public: it carries the
metadata, the structured data and the full model catalogue that the SEO work
put there, so the site keeps its place in search, and it hands the reader a
button through to the gated tool.

It is assembled from src/app.html rather than written separately, so the
head metadata, the water background and the footer cannot drift apart from
the application's own.

Run:  python tools/make_landing.py
      python tools/make_landing.py --check   exit non-zero if index.html is stale
"""
import io
import os
import re
import sys

SOURCE = os.path.join("src", "app.html")
OUT = "index.html"

BODY = '''
<header class="masthead">
  <div class="masthead-inner">
    <div class="brandwrap">
      <a class="labchip" href="http://www.swatlab.or.kr/" target="_blank" rel="noopener"
         title="SWAT Lab, Sustainable Water Treatment Laboratory, Sungkyunkwan University">
        <span class="mark mark-swat" role="img" aria-label="SWAT Lab"></span>
      </a>
      <span class="vr"></span>
      <div class="title">
        <h1>Adsorp<b>Fit</b><span class="ver">v1.0</span></h1>
        <p>Adsorption data modelling</p>
      </div>
    </div>
    <div class="masthead-tools">
      <a class="btn primary" href="app/">Open the tool</a>
    </div>
  </div>
</header>

<main class="shell">
  <section class="hero">
    <h2>Fit adsorption kinetics, isotherms and thermodynamics in your browser.</h2>
    <p class="lead">AdsorpFit fits 21 isotherm models and 13 kinetic models to your own
    measurements by bounded non-linear least squares, ranks them on AICc, checks that your
    data fall inside each model's valid domain, derives van 't Hoff thermodynamic parameters,
    draws publication-quality figures, and explains every fitted parameter in writing.
    The whole scientific Python stack runs inside your browser, so nothing you paste is
    ever uploaded.</p>
    <p class="cta">
      <a class="btn primary lg" href="app/">Open the tool</a>
      <span class="tiny">Sign in with the ID and password from your group.</span>
    </p>
  </section>

  <section class="facts">
    <div class="fact"><b>34</b><span>models, each with its assumptions, its valid domain
      and its original citation</span></div>
    <div class="fact"><b>23</b><span>worked examples from published papers whose raw data
      were deposited openly</span></div>
    <div class="fact"><b>2</b><span>languages, English and Korean, including every
      generated interpretation</span></div>
    <div class="fact"><b>0</b><span>data leave your machine: the fitting runs locally
      through WebAssembly</span></div>
  </section>

  <section class="panel why">
    <div class="panel-head"><h2>Three things it does differently</h2></div>
    <div class="panel-body">
      <p><b>It ranks on AICc, not R².</b> R² can only rise when a parameter is added, so
      comparing a two-parameter Langmuir against a four-parameter Fritz&ndash;Schl&uuml;nder on
      R² is guaranteed to favour the latter whether or not the extra parameters mean
      anything. AdsorpFit reports Akaike weights and says plainly when two models are not
      statistically distinguishable.</p>
      <p><b>It fits the untransformed equation.</b> Linearising an isotherm changes which
      points dominate the regression, which is the main reason pseudo-second-order appears
      to fit almost every published dataset. The linear plots are shown for comparison with
      the older literature, and flagged where the straight line is flattering the fit.</p>
      <p><b>It refuses to report impossible parameters.</b> A model that predicts a negative
      loading over your measured range is rejected however high its R², and a capacity fitted
      to data that never plateau is labelled as the extrapolation it is.</p>
    </div>
  </section>
'''

TAIL = '''
</main>
'''


def read(p):
    return io.open(p, encoding="utf-8").read()


def build():
    src = read(SOURCE)

    head = src[src.index("<head>"):src.index("</head>")]
    # the application's loader and its noindex are not wanted here
    head = head.replace('<meta name="robots" content="noindex, nofollow">',
                        '<meta name="robots" content="index, follow">')
    head = re.sub(r'<script src="https://cdn\.plot\.ly[^>]*></script>\s*', "", head)
    head = re.sub(r'<script src="https://cdn\.jsdelivr\.net/pyodide[^>]*></script>\s*',
                  "", head)
    head = re.sub(r'<script defer src="https://cdn\.jsdelivr\.net/npm/katex[^>]*></script>\s*',
                  "", head)
    head = re.sub(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/katex[^>]*>\s*',
                  "", head)

    water = src[src.index('<div id="water-bg"'):
                src.index('<!-- ===================== boot overlay')]
    foot = src[src.index('<footer class="site-foot">'):src.index("</footer>") + 9]
    # strip the data-i18n hooks: this page ships in one language
    foot = re.sub(r'\s*data-i18n="[^"]*"', "", foot)

    ver = re.search(r'window\.APP_VERSION = "([^"]+)"', src).group(1)

    page = ("<!DOCTYPE html>\n"
            "<!-- Generated by tools/make_landing.py from src/app.html. -->\n"
            '<html lang="en" data-theme="light" data-layout="side" data-density="comfy">\n'
            + head + LANDING_CSS + "</head>\n<body>\n"
            + water + BODY + MODELS_PLACEHOLDER + TAIL + foot + "\n"
            + '<script src="js/water.js?v=%s"></script>\n' % ver
            + "</body>\n</html>\n")
    return page


LANDING_CSS = '''
<style>
/* Landing-page only. The application's own stylesheet is already linked
   above, so this adds the few pieces the tool itself has no use for. */
.hero { max-width: 760px; margin: 38px auto 10px; text-align: center; }
.hero h2 { font-size: clamp(22px, 3.4vw, 33px); line-height: 1.25;
  letter-spacing: -0.5px; margin: 0 0 14px; }
.hero .lead { color: var(--text-2); font-size: 15px; line-height: 1.7; margin: 0 auto; }
.hero .cta { margin: 26px 0 0; display: flex; flex-direction: column;
  align-items: center; gap: 9px; }
.btn.lg { font-size: 15px; padding: 12px 26px; }
.facts { max-width: 980px; margin: 34px auto 6px; display: grid; gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }
.fact { background: var(--surface-glass); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px 18px; text-align: center; }
.fact b { display: block; font-size: 30px; color: var(--accent);
  letter-spacing: -1px; line-height: 1.1; }
.fact span { display: block; margin-top: 6px; font-size: 12px;
  color: var(--text-2); line-height: 1.5; }
.panel.why { max-width: 880px; margin: 30px auto; }
.panel.why p { color: var(--text-2); line-height: 1.7; }
.panel.why b { color: var(--text); }
.masthead-tools .btn.primary { text-decoration: none; }
</style>
'''

MODELS_PLACEHOLDER = "\n  <!-- SEO:MODELS placeholder -->\n"


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    page = build()
    old = read(OUT) if os.path.exists(OUT) else ""

    # keep the generated model catalogue across rebuilds
    m = re.search(r"<!-- SEO:MODELS start.*?<!-- SEO:MODELS end -->", old, re.S)
    if m:
        page = page.replace(MODELS_PLACEHOLDER, "\n  " + m.group(0) + "\n")

    if "--check" in sys.argv:
        stale = page != old
        print("index.html is %s" % ("STALE, run tools/make_landing.py"
                                    if stale else "up to date"))
        sys.exit(1 if stale else 0)
    io.open(OUT, "w", encoding="utf-8", newline="").write(page)
    print("wrote %s (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
