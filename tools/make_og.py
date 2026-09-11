# -*- coding: utf-8 -*-
"""Draw the link preview card, assets/og-card.png.

This is the image search engines and chat apps show beside the link, so it
should say what the site is rather than decorate it. The curve on it is not
an illustration: it is a real Langmuir fit to the Ca-biochar phosphate data
from Wang et al. (2021), run through the same fitter the site uses.

Run:  python tools/make_og.py
"""
import os
import sys

sys.path.insert(0, "py")
sys.path.insert(0, os.path.join("validation", "datasets"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from core import fit_model
from isotherms import ISOTHERM_MODELS
import wang2021_phosphate as W

INK = "#eaf6f8"
DIM = "#9fc3cc"
ACCENT = "#37c8cf"
BG_TOP = "#0b2436"
BG_BOT = "#061019"

W_PX, H_PX = 1200, 630
DPI = 100


def gradient(ax):
    """A vertical wash, echoing the deep water behind the site itself."""
    top = np.array([int(BG_TOP[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    bot = np.array([int(BG_BOT[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    ramp = np.linspace(0, 1, 256).reshape(-1, 1)
    img = top * (1 - ramp[:, :, None]) + bot * ramp[:, :, None]
    ax.imshow(img, extent=[0, 1, 0, 1], aspect="auto",
              origin="upper", zorder=0)


def main():
    ce = np.array(W.ISOTHERMS["Ca-BC"]["ce"], float)
    qe = np.array(W.ISOTHERMS["Ca-BC"]["qe"], float)
    f = fit_model(ISOTHERM_MODELS["langmuir"], ce, qe,
                  ctx={"T": 298.15}, n_restarts=14)
    xs = np.linspace(0, ce.max() * 1.05, 300)
    ys = ISOTHERM_MODELS["langmuir"].func(xs, *[f.params[p.key]
                                                for p in ISOTHERM_MODELS["langmuir"].params])

    fig = plt.figure(figsize=(W_PX / DPI, H_PX / DPI), dpi=DPI)
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_axis_off()
    gradient(bg)

    fig.text(0.055, 0.80, "AdsorpFit", color=INK, fontsize=64,
             fontweight="bold", va="center")
    # kept narrow on purpose: the plot starts at x = 0.58 of the canvas
    fig.text(0.055, 0.675,
             "Adsorption kinetics, isotherms\nand thermodynamics,\nfitted in your browser",
             color=ACCENT, fontsize=22, va="top", linespacing=1.5)
    fig.text(0.055, 0.40,
             "21 isotherm models\n13 kinetic models\nvan 't Hoff thermodynamics",
             color=INK, fontsize=20, va="top", linespacing=1.9)
    fig.text(0.055, 0.10,
             "SWAT Lab, Sungkyunkwan University    |    free and open source",
             color=DIM, fontsize=16, va="center")

    # the fit itself, sitting on the right like a figure panel in a paper
    ax = fig.add_axes([0.58, 0.20, 0.37, 0.60])
    ax.set_facecolor("none")
    ax.plot(xs, ys, color=ACCENT, lw=2.6, zorder=2)
    ax.plot(ce, qe, "o", ms=8, mfc="none", mec=INK, mew=1.8, zorder=3)
    ax.set_xlabel("$C_e$  (mg L$^{-1}$)", color=DIM, fontsize=13)
    ax.set_ylabel("$q_e$  (mg g$^{-1}$)", color=DIM, fontsize=13)
    ax.tick_params(colors=DIM, labelsize=11)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(DIM)
    ax.text(0.97, 0.08, "Langmuir, $R^2$ = %.4f" % f.stats["R2"],
            transform=ax.transAxes, ha="right", color=INK, fontsize=13)

    out = os.path.join("assets", "og-card.png")
    fig.savefig(out, dpi=DPI, facecolor=BG_BOT)
    plt.close(fig)
    print("wrote %s  (%d x %d)" % (out, W_PX, H_PX))


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
