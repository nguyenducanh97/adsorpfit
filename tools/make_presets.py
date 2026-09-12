# -*- coding: utf-8 -*-
"""Generate js/presets.js from the dataset modules in validation/datasets/.

Every preset is real measured data from an open-access paper whose authors
deposited the raw numbers under an open licence. Nothing here is synthetic,
and nothing is digitised from a figure: each series is the authors' own
tabulated measurements, which is why each carries a citation to both the
paper and the deposited dataset.

Keeping the presets generated rather than hand-written means the numbers in
the interface and the numbers the validation suite refits are the same
arrays, so the two cannot drift apart.

Run:  python tools/make_presets.py
      python tools/make_presets.py --check   exit non-zero if presets.js is stale
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join("validation", "datasets"))

import wang2021_phosphate as W
import zhang2018_fluoride_arsenic as Z
import tao2020_levofloxacin as T
import xue2019_cadmium as X

ISO_MODELS = ["langmuir", "freundlich", "sips", "toth", "redlich_peterson"]
KIN_MODELS = ["pfo", "pso", "elovich", "avrami"]


def rows(*cols):
    """Tab separated rows from parallel columns, blanks dropped."""
    out = []
    for vals in zip(*cols):
        out.append("\t".join(fmt(v) for v in vals))
    return "\n".join(out)


def fmt(v):
    if isinstance(v, float):
        s = ("%.6g" % v)
        return s
    return str(v)


def iso_block(ce, qe, sd=None, c0=None):
    head = ["Ce (mg/L)", "qe (mg/g)"]
    cols = [ce, qe]
    if sd is not None:
        head.append("sd"); cols.append(sd)
    if c0 is not None:
        head.append("C0 (mg/L)"); cols.append(c0)
    return "\t".join(head) + "\n" + rows(*cols)


def kin_block(t, q, sd=None, unit="min"):
    """Time column labelled with the unit the source actually used.

    The Wang runs are tabulated in hours and the rest in minutes, and the
    reader's unit selector keys off this header, so it cannot be assumed.
    """
    head = ["t (%s)" % unit, "qt (mg/g)"]
    cols = [t, q]
    if sd is not None:
        head.append("sd"); cols.append(sd)
    return "\t".join(head) + "\n" + rows(*cols)


P = []


def add(pid, cat, cite, en, ko, data, ctx, models):
    P.append({"id": pid, "cat": cat, "cite": cite, "en": en, "ko": ko,
              "data": data, "ctx": ctx, "models": models})


# ======================================================== Wang 2021, phosphate
WANG_ISO_NOTES = {
    "Mg-BC": ("Phosphate on Mg-biochar (isotherm)",
              "Ten equilibrium points with replicate standard deviations, reaching a clear plateau. The authors' best performer. Langmuir gives 106.3 mg/g, Sips 112.5 mg/g.",
              "Mg-바이오차의 인산염 흡착 (등온)",
              "반복 측정 표준편차를 포함한 평형 데이터 10점이며 뚜렷한 평형값에 도달합니다. 논문에서 가장 성능이 좋은 흡착제로, Langmuir는 106.3 mg/g, Sips는 112.5 mg/g를 보고했습니다."),
    "Ca-BC": ("Phosphate on Ca-biochar (isotherm)",
              "A textbook saturating isotherm: the top third of the concentration range adds almost nothing, so the fitted capacity is measured rather than extrapolated.",
              "Ca-바이오차의 인산염 흡착 (등온)",
              "교과서적인 포화형 등온선입니다. 농도 범위의 상위 3분의 1에서 흡착량이 거의 늘지 않으므로, 적합된 흡착용량은 외삽이 아니라 측정된 값입니다."),
    "Al-BC": ("Phosphate on Al-biochar (no plateau)",
              "Still rising at the highest concentration. Every saturation model will report a q_max here, and every one of them is an extrapolation. AdsorpFit says so.",
              "Al-바이오차의 인산염 흡착 (평탄역 없음)",
              "가장 높은 농도에서도 계속 상승합니다. 모든 포화 모델이 q_max를 보고하지만 그 값은 모두 외삽이며, AdsorpFit은 이를 경고합니다."),
    "BC": ("Phosphate on plain biochar (a failing adsorbent)",
           "The unmodified biochar adsorbs almost nothing and one measured loading is negative. Kept deliberately: it is the case every diagnostic should object to.",
           "무처리 바이오차의 인산염 흡착 (실패한 흡착제)",
           "개질하지 않은 바이오차는 거의 흡착하지 않으며 측정된 흡착량 하나는 음수입니다. 모든 진단 기능이 문제를 제기해야 하는 사례로 일부러 포함했습니다."),
}

for key, (en_n, en_t, ko_n, ko_t) in WANG_ISO_NOTES.items():
    d = W.ISOTHERMS[key]
    add("wang_%s_iso" % key.split("-")[0].lower(), "isotherm", W.CITATION,
        {"name": en_n, "note": en_t}, {"name": ko_n, "note": ko_t},
        iso_block(d["ce"], d["qe"], d["qe_sd"], W.C0_ISOTHERM),
        {"T": "298.15", "MW": "94.97", "Cs": "", "dose": "2"}, ISO_MODELS)

WANG_KIN_NOTES = {
    "Ca-BC": ("Phosphate on Ca-biochar (kinetics)",
              "Twelve time points over 72 h that reach a clean plateau. The authors report PFO k1 = 6.26 and PSO k2 = 0.664 mg/g.",
              "Ca-바이오차의 인산염 흡착 (속도)",
              "72시간에 걸친 12개 시간점이 뚜렷한 평탄역에 도달합니다. 논문은 PFO k₁ = 6.26, PSO k₂ = 0.664 mg/g를 보고했습니다."),
    "Al-BC": ("Phosphate on Al-biochar (never equilibrates)",
              "Uptake is still climbing at 72 h, which the paper states in its own text. Any q_e fitted to this is an extrapolation, and the rate constant goes with it.",
              "Al-바이오차의 인산염 흡착 (평형 미도달)",
              "72시간에도 흡착량이 계속 증가하며, 논문 본문도 이를 밝히고 있습니다. 여기에 적합한 q_e는 외삽이며 속도상수도 함께 불확실해집니다."),
    "Mg-BC": ("Phosphate on Mg-biochar (two-stage uptake)",
              "A fast surface stage followed by a slower one, which is what the Weber-Morris multi-region analysis and the double exponential model exist for.",
              "Mg-바이오차의 인산염 흡착 (2단계 흡착)",
              "빠른 표면 단계에 이어 느린 단계가 나타납니다. Weber–Morris 다구간 해석과 이중지수 모델이 바로 이런 경우를 위한 것입니다."),
    "La-BC": ("Phosphate on La-biochar (equilibrium before the first point)",
              "Adsorption was essentially complete within the first half hour, so nothing in the data constrains the rate constant however tight its confidence interval looks.",
              "La-바이오차의 인산염 흡착 (첫 측정 이전에 평형 도달)",
              "첫 30분 안에 흡착이 사실상 끝나므로, 신뢰구간이 아무리 좁아 보여도 데이터가 속도상수를 제약하지 못합니다."),
}

for key, (en_n, en_t, ko_n, ko_t) in WANG_KIN_NOTES.items():
    d = W.KINETICS[key]
    add("wang_%s_kin" % key.split("-")[0].lower(), "kinetics", W.CITATION,
        {"name": en_n, "note": en_t}, {"name": ko_n, "note": ko_t},
        kin_block(W.KIN_TIME, d["qt"], d.get("sd"), unit="h"),
        {"T": "298.15", "C0": "20", "dose": "2", "radius": "0.05"}, KIN_MODELS)


# ============================================ Zhang 2018, fluoride and arsenic
# the deposited times are in hours and land on whole minutes
ZHANG_MIN = [round(h * 60) for h in Z.T_KINETIC]

ZHANG = {
    ("As", "BC3"): (
        "Arsenic on yak dung biochar",
        "Arsenic(V) on plain biochar at 10 g/L. The uptake is small and the isotherm never turns over, so the fitted capacity sits well beyond the measured range.",
        "야크 분변 바이오차의 비소 흡착",
        "10 g/L 조건에서 무처리 바이오차에 흡착된 비소(V)입니다. 흡착량이 적고 등온선이 꺾이지 않으므로, 적합된 흡착용량은 측정 범위를 크게 벗어납니다.",
        "74.92"),
    ("As", "Fe-BC3"): (
        "Arsenic on iron-modified biochar",
        "The same biochar after FeCl2 treatment removes 99% of the arsenic. The isotherm rises steeply and then bends over, which is what a genuine affinity looks like.",
        "철 개질 바이오차의 비소 흡착",
        "FeCl₂로 개질한 같은 바이오차가 비소의 99%를 제거합니다. 등온선이 가파르게 올라간 뒤 꺾이며, 이는 실제로 친화도가 높을 때 나타나는 형태입니다.",
        "74.92"),
    ("F", "BC3"): (
        "Fluoride on yak dung biochar",
        "A well-shaped fluoride isotherm. Our non-linear Langmuir gives 4.98 mg/g against the 4.851 the paper reports, and R2 = 0.997.",
        "야크 분변 바이오차의 불소 흡착",
        "형태가 좋은 불소 등온선입니다. 비선형 Langmuir 적합은 4.98 mg/g로, 논문의 4.851과 가깝고 R²은 0.997입니다.",
        "19.00"),
    ("F", "Fe-BC3"): (
        "Fluoride on iron-modified biochar",
        "Iron modification raises the affinity but lowers the capacity, so the two curves cross. Fitting both and comparing is the point of this pair.",
        "철 개질 바이오차의 불소 흡착",
        "철 개질은 친화도를 높이지만 흡착용량은 낮추므로 두 곡선이 교차합니다. 두 데이터를 함께 적합해 비교하는 것이 이 쌍의 목적입니다.",
        "19.00"),
}

for key, (en_n, en_t, ko_n, ko_t, mw) in ZHANG.items():
    pid = "zhang_%s_%s" % (key[0].lower(),
                           "febc" if key[1].startswith("Fe") else "bc")
    add(pid + "_iso", "isotherm", Z.CITATION,
        {"name": en_n + " (isotherm)", "note": en_t},
        {"name": ko_n + " (등온)", "note": ko_t},
        iso_block(Z.CE_ISOTHERM[key], Z.qe(key), None, Z.C0_ISOTHERM),
        {"T": "298.15", "MW": mw, "Cs": "", "dose": "10"}, ISO_MODELS)

ZHANG_KIN = {
    ("As", "BC3"): (
        "Arsenic on yak dung biochar (kinetics)",
        "Nineteen points over 12 h, but the whole signal is 0.07 mg/g and the scatter is a large fraction of it. A good test of whether a rate constant means anything.",
        "야크 분변 바이오차의 비소 흡착 (속도)",
        "12시간에 걸친 19개 점이지만 전체 신호가 0.07 mg/g에 불과하고 산포가 그중 상당 부분을 차지합니다. 속도상수에 의미가 있는지 시험해 보기 좋은 사례입니다."),
    ("As", "Fe-BC3"): (
        "Arsenic on iron-modified biochar (kinetics)",
        "Removal is 95% complete at the first measurement. The paper tabulates a pseudo-second-order q_e of 1.069 mg/g, but its own deposited data never exceed 0.364, which is what the fit here returns.",
        "철 개질 바이오차의 비소 흡착 (속도)",
        "첫 측정 시점에 이미 95%가 제거되었습니다. 논문은 유사 2차 q_e를 1.069 mg/g로 표에 실었지만, 함께 공개된 원자료는 0.364를 넘지 않으며 여기서의 적합 결과도 그 값입니다."),
    ("F", "BC3"): (
        "Fluoride on yak dung biochar (kinetics)",
        "A clean approach to equilibrium over 12 h. Pseudo-second-order gives 1.725 mg/g against the paper's 1.737.",
        "야크 분변 바이오차의 불소 흡착 (속도)",
        "12시간에 걸쳐 평형에 깔끔하게 접근합니다. 유사 2차식은 1.725 mg/g를 주며, 논문 값 1.737과 일치합니다."),
    ("F", "Fe-BC3"): (
        "Fluoride on iron-modified biochar (kinetics)",
        "Faster than the unmodified biochar and flat after about an hour, so both q_e and the rate constant are well determined here.",
        "철 개질 바이오차의 불소 흡착 (속도)",
        "무처리 바이오차보다 빠르며 약 1시간 뒤부터 평탄해집니다. 따라서 q_e와 속도상수 모두 잘 결정됩니다."),
}

for key, (en_n, en_t, ko_n, ko_t) in ZHANG_KIN.items():
    pid = "zhang_%s_%s_kin" % (key[0].lower(),
                               "febc" if key[1].startswith("Fe") else "bc")
    add(pid, "kinetics", Z.CITATION,
        {"name": en_n, "note": en_t}, {"name": ko_n, "note": ko_t},
        kin_block(ZHANG_MIN, Z.qt(key)),
        {"T": "298.15", "C0": str(Z.C0_KINETIC[key[0]]), "dose": "10",
         "radius": ""}, KIN_MODELS)


# ================================================== Tao 2020, levofloxacin
TAO_ISO = {
    293.15: ("Levofloxacin on cellulose nanocrystal / graphene oxide, 20 C",
             "An antibiotic on a composite adsorbent. Sips returns 17.29 mg/g, the same figure the paper reports, while Langmuir returns 49.7 mg/g from data that never approach saturation.",
             "셀룰로스 나노결정/산화graphene 복합체의 레보플록사신 흡착, 20 °C",
             "복합 흡착제에 대한 항생제 흡착입니다. Sips는 논문과 같은 17.29 mg/g를 주지만, Langmuir는 포화에 전혀 접근하지 않은 데이터로부터 49.7 mg/g를 내놓습니다."),
    303.15: ("Levofloxacin on cellulose nanocrystal / graphene oxide, 30 C",
             "The middle of the three temperatures. Uptake rises with temperature here, which is the signature of an endothermic process.",
             "셀룰로스 나노결정/산화graphene 복합체의 레보플록사신 흡착, 30 °C",
             "세 온도 가운데 중간입니다. 온도가 오를수록 흡착량이 증가하며, 이는 흡열 과정의 특징입니다."),
    313.15: ("Levofloxacin on cellulose nanocrystal / graphene oxide, 40 C",
             "The warmest of the three isotherms, and the highest capacity. Load all three into the thermodynamics tab to get the van 't Hoff parameters.",
             "셀룰로스 나노결정/산화graphene 복합체의 레보플록사신 흡착, 40 °C",
             "세 등온선 가운데 가장 높은 온도이며 흡착용량도 가장 큽니다. 세 데이터를 열역학 탭에 함께 넣으면 van 't Hoff 매개변수를 얻을 수 있습니다."),
}

for temp, (en_n, en_t, ko_n, ko_t) in TAO_ISO.items():
    d = T.ISOTHERMS[temp]
    add("tao_levo_iso_%d" % round(temp - 273.15), "isotherm", T.CITATION,
        {"name": en_n, "note": en_t}, {"name": ko_n, "note": ko_t},
        iso_block(d["ce"], d["qe"]),
        {"T": "%.2f" % temp, "MW": str(T.MW), "Cs": "", "dose": ""},
        ISO_MODELS)

add("tao_levo_kin", "kinetics", T.CITATION,
    {"name": "Levofloxacin on cellulose nanocrystal / graphene oxide (kinetics)",
     "note": "Fifteen points from 3 min to 18 h, spanning nearly three decades of time. The long tail is what makes the difference between the kinetic models visible."},
    {"name": "셀룰로스 나노결정/산화graphene 복합체의 레보플록사신 흡착 (속도)",
     "note": "3분부터 18시간까지 15개 점으로, 시간 축을 거의 세 자릿수에 걸쳐 덮습니다. 긴 꼬리 덕분에 속도식 사이의 차이가 드러납니다."},
    kin_block(T.KINETIC_TIME, T.KINETIC_Q),
    {"T": "293.15", "C0": "", "dose": "", "radius": ""}, KIN_MODELS)


# ==================================================== Xue 2019, cadmium
add("xue_cd_iso", "isotherm", X.CITATION,
    {"name": "Cadmium on a mesoporous ceramic nanomaterial",
     "note": "Worth fitting carefully. The paper reports a Langmuir capacity of 97.09 mg/g with R2 = 0.9832, but those come from the linearised Ce/qe plot. Fitting the same points directly gives 72.3 mg/g with R2 = 0.65, and the linear plots tab shows why the two disagree."},
    {"name": "메조다공성 세라믹 나노소재의 카드뮴 흡착",
     "note": "주의해서 적합해 볼 가치가 있습니다. 논문은 Langmuir 흡착용량 97.09 mg/g와 R² = 0.9832를 보고하지만, 이는 Ce/qe 선형 그래프에서 얻은 값입니다. 같은 점들을 직접 적합하면 72.3 mg/g, R² = 0.65가 나오며, 선형 그래프 탭에서 그 차이의 이유를 볼 수 있습니다."},
    iso_block(X.CE_ISOTHERM, X.QE_ISOTHERM, X.QE_SD, X.C0_ISOTHERM),
    {"T": "298.15", "MW": "112.41", "Cs": "", "dose": "4"}, ISO_MODELS)

add("xue_cd_kin", "kinetics", X.CITATION,
    {"name": "Cadmium on a mesoporous ceramic nanomaterial (kinetics)",
     "note": "Eight points with replicate error bars, flat from 150 min onward, so q_e is measured rather than fitted. Pseudo-first-order fails here while pseudo-second-order and Avrami both describe it."},
    {"name": "메조다공성 세라믹 나노소재의 카드뮴 흡착 (속도)",
     "note": "반복 측정 오차막대를 포함한 8개 점이며 150분 이후 평탄하므로 q_e는 적합이 아니라 측정된 값입니다. 유사 1차식은 맞지 않고 유사 2차식과 Avrami가 잘 설명합니다."},
    kin_block(X.KINETIC_TIME, X.KINETIC_Q, X.KINETIC_SD),
    {"T": "298.15", "C0": str(X.C0_KINETIC), "dose": "4", "radius": ""},
    KIN_MODELS)


# ======================================================== thermodynamics
THERMO = [{
    "id": "tao_levo_thermo",
    "cat": "thermo",
    "cite": T.CITATION,
    "en": {"name": "Levofloxacin on cellulose nanocrystal / graphene oxide",
           "note": "Isotherms at 293.15, 303.15 and 313.15 K from one paper, which is the minimum a van 't Hoff analysis needs. The capacity rises with temperature and the enthalpy comes out endothermic at about +34 kJ/mol, but with three points the line is only moderately determined, and the Langmuir route gives a different answer from the distribution coefficient used here. That disagreement is the reason the route has to be stated in any paper quoting these numbers."},
    "ko": {"name": "셀룰로스 나노결정/산화graphene 복합체의 레보플록사신 흡착",
           "note": "한 논문에서 293.15, 303.15, 313.15 K에 측정한 등온선으로, van 't Hoff 해석에 필요한 최소 구성입니다. 온도가 오를수록 흡착용량이 커지고 엔탈피는 약 +34 kJ/mol의 흡열로 나옵니다. 다만 점이 세 개뿐이라 직선이 제한적으로만 결정되며, Langmuir 경로는 여기서 사용한 분배계수 경로와 다른 값을 줍니다. 이 불일치야말로 이 값을 인용하는 논문이 변환 경로를 반드시 밝혀야 하는 이유입니다."},
    "MW": str(T.MW),
    "model": "sips",
    "route": "kd_density",
    "datasets": [[("%.2f" % t),
                  rows(T.ISOTHERMS[t]["ce"], T.ISOTHERMS[t]["qe"])]
                 for t in T.TEMPERATURES],
}]


HEADER = '''/* ==========================================================================
   AdsorpFit: built-in example datasets.

   Generated by tools/make_presets.py from validation/datasets/. Every entry
   is real measured data from an open-access paper whose authors deposited
   the raw numbers under an open licence, not a synthetic curve and not a
   figure read off with a ruler, and each carries its citation.

   The set is chosen to span behaviours rather than to flatter the tool:
   isotherms that saturate and isotherms that never do, an adsorbent that
   fails outright and records negative uptake, kinetic runs that finish
   before the first measurement and others still climbing at the end, a
   capacity the source paper obtained from a linearised plot that the
   non-linear fit does not support, and a tabulated rate constant that its
   own deposited data contradict.

   Five contaminants across nine adsorbents: phosphate, arsenic, fluoride,
   cadmium and an antibiotic.
   ========================================================================== */

'''


def render():
    body = "const PRESETS = " + json.dumps(P, ensure_ascii=False, indent=2) + ";\n"
    thermo = ("\n/* Thermodynamics needs a set of isotherms at different\n"
              "   temperatures rather than a single series. */\n"
              "const THERMO_PRESETS = "
              + json.dumps(THERMO, ensure_ascii=False, indent=2) + ";\n")
    return HEADER + body + thermo


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.join("validation", "datasets"))
    out = render()
    path = "js/presets.js"
    old = io.open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if "--check" in sys.argv:
        stale = out != old
        print("presets.js is %s" % ("STALE, run tools/make_presets.py"
                                    if stale else "up to date"))
        sys.exit(1 if stale else 0)
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("wrote %s: %d presets (%d isotherm, %d kinetics) + %d thermodynamic"
          % (path, len(P),
             sum(1 for p in P if p["cat"] == "isotherm"),
             sum(1 for p in P if p["cat"] == "kinetics"), len(THERMO)))
