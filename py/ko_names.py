# -*- coding: utf-8 -*-
"""Korean model names.

Only the descriptive part is translated. A model named after the person who
derived it keeps that name, because that is how it is cited and searched for
in Korean papers as much as in English ones, so Langmuir, Freundlich, Temkin,
Tóth, Hill and the rest are deliberately absent from this table and fall
through to their original spelling.
"""

KO_NAMES = {
    # kinetics
    "Pseudo-first-order (Lagergren)": "유사 1차 (Lagergren)",
    "Pseudo-second-order (Ho & McKay)": "유사 2차 (Ho & McKay)",
    "Pseudo-nth-order": "유사 n차",
    "Ritchie nth-order": "Ritchie n차",
    "Avrami (fractional order)": "Avrami (분수 차수)",
    "Mixed 1,2-order (MOE)": "혼합 1,2차 (MOE)",
    "Fractal-like pseudo-first-order": "프랙탈형 유사 1차",
    "Weber–Morris (intraparticle diffusion)": "Weber–Morris (입자 내 확산)",
    "Liquid film diffusion (Boyd–Adamson)": "액막 확산 (Boyd–Adamson)",
    "Bangham (pore diffusion)": "Bangham (세공 확산)",
    "Homogeneous surface diffusion (Crank)": "균질 표면 확산 (Crank)",
    "Double exponential": "이중지수",

    # isotherms
    "BET (liquid phase)": "BET (액상)",
    "Elovich (isotherm)": "Elovich (등온식)",
    "Sips (Langmuir–Freundlich)": "Sips (Langmuir–Freundlich)",
    "Brouers–Sotolongo (deformed Weibull)": "Brouers–Sotolongo (변형 Weibull)",
    "Fritz–Schlünder (IV)": "Fritz–Schlünder (IV형)",
}

# Weber–Morris segment labels, shown on the Diffusion tab
KO_NAMES.update({
    "external surface adsorption (instantaneous stage)":
        "외부 표면 흡착 (순간 단계)",
    "stage 1: external surface adsorption / film diffusion":
        "1단계: 외부 표면 흡착 / 막 확산",
    "stage 2: intraparticle diffusion (rate-limiting)":
        "2단계: 입자 내 확산 (속도결정)",
    "stage 3: equilibrium plateau, diffusion slows as sites fill":
        "3단계: 평형 평탄역, 흡착점이 채워지며 확산이 느려짐",
    "stage {i}": "{i}단계",
})
