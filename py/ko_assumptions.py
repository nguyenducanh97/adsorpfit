# -*- coding: utf-8 -*-
"""Korean for the assumptions each model asks you to accept.

These appear under every model on the Interpretation tab, which is where a
reader decides whether a good fit actually means anything, so they matter as
much as the fitted numbers.
"""

KO_ASSUMPTIONS = {

    # ------------------------------------------------------------ kinetics
    "The uptake rate is proportional to the number of unoccupied sites, "
    "d q_t/dt = k₁(q_e − q_t).":
        "흡착 속도가 비어 있는 흡착점의 수에 비례합니다, "
        "d q_t/dt = k₁(q_e − q_t).",
    "Usually describes the initial, fast stage of adsorption best.":
        "보통 흡착의 초기 빠른 단계를 가장 잘 설명합니다.",
    "Applies when adsorption is not limited by intraparticle diffusion.":
        "흡착이 입자 내 확산으로 제한되지 않을 때 적용됩니다.",
    "Does NOT mean the process is a first-order chemical reaction.":
        "이 과정이 1차 화학반응이라는 뜻은 아닙니다.",

    "The uptake rate is proportional to the square of the number of "
    "unoccupied sites, d q_t/dt = k₂(q_e − q_t)².":
        "흡착 속도가 비어 있는 흡착점 수의 제곱에 비례합니다, "
        "d q_t/dt = k₂(q_e − q_t)².",
    "Conventionally interpreted as rate-limiting chemisorption.":
        "관례적으로 화학흡착이 속도를 결정하는 것으로 해석합니다.",
    "Describes the whole uptake curve including the approach to "
    "equilibrium.":
        "평형에 접근하는 구간을 포함해 흡착 곡선 전체를 설명합니다.",
    "k₂ depends on experimental conditions, so it is not transferable.":
        "k₂는 실험 조건에 의존하므로 다른 조건으로 옮겨 쓸 수 없습니다.",

    "The activation energy for adsorption increases linearly with "
    "coverage.":
        "흡착 활성화 에너지가 피복률에 따라 선형으로 증가합니다.",
    "The adsorbent surface is energetically heterogeneous.":
        "흡착제 표면이 에너지적으로 불균일합니다.",
    "Describes chemisorption; has no equilibrium plateau, so it cannot be "
    "used to estimate q_e.":
        "화학흡착을 설명하며, 평형 평탄역이 없으므로 q_e를 추정하는 데 쓸 수 "
        "없습니다.",
    "Assumes the desorption rate is negligible.":
        "탈착 속도를 무시할 수 있다고 가정합니다.",

    "Adapted from nucleation and crystal-growth theory.":
        "핵생성 및 결정 성장 이론에서 가져온 식입니다.",
    "Allows a fractional reaction order rather than forcing 1 or 2.":
        "반응차수를 1이나 2로 강요하지 않고 분수 차수를 허용합니다.",
    "n_AV is interpreted as reflecting possible changes in the adsorption "
    "mechanism over the course of the process.":
        "n_AV는 과정이 진행되면서 흡착 메커니즘이 달라질 수 있음을 반영하는 "
        "값으로 해석합니다.",

    "Interpolates continuously between PFO and PSO rather than forcing a "
    "choice between them.":
        "유사 1차와 유사 2차 가운데 하나를 고르도록 강요하지 않고 그 사이를 "
        "연속적으로 보간합니다.",
    "f₂ is the fraction of the process behaving as second order.":
        "f₂는 이 과정 가운데 2차로 거동하는 비율입니다.",

    "Generalises PFO and PSO by letting the order n be fitted.":
        "차수 n을 적합하게 하여 유사 1차와 유사 2차를 일반화합니다.",
    "d q_t/dt = k_n (q_e − q_t)ⁿ.": "d q_t/dt = k_n (q_e − q_t)ⁿ.",
    "A fitted n far from 1 or 2 means neither standard model is "
    "appropriate.":
        "적합된 n이 1이나 2에서 멀면 두 표준 모델 모두 적절하지 않다는 "
        "뜻입니다.",

    "Derived from the fraction of surface sites occupied, not from a "
    "concentration-driven rate law.":
        "농도에 의한 속도식이 아니라, 점유된 표면 흡착점의 비율에서 "
        "유도되었습니다.",
    "n has a concrete meaning here: the number of sites occupied by one "
    "adsorbate molecule.":
        "여기서 n에는 구체적인 의미가 있습니다. 흡착질 분자 하나가 차지하는 "
        "흡착점의 수입니다.",
    "Assumes the rate depends only on the fraction of vacant sites.":
        "속도가 빈 흡착점의 비율에만 의존한다고 가정합니다.",

    "The rate 'constant' is not constant: on a fractal or energetically "
    "disordered surface it decays as a power of time, k(t) = k′t^(−h).":
        "속도 '상수'가 일정하지 않습니다. 프랙탈이거나 에너지적으로 무질서한 "
        "표면에서는 시간의 거듭제곱으로 감소합니다, k(t) = k′t^(−h).",
    "h = 0 recovers classical pseudo-first-order kinetics.":
        "h = 0이면 고전적인 유사 1차 속도론이 됩니다.",
    "Physically motivated for rough, porous or geometrically disordered "
    "adsorbents where reactant and site cannot mix freely.":
        "반응물과 흡착점이 자유롭게 섞이지 못하는 거칠거나 다공성이거나 "
        "기하학적으로 무질서한 흡착제를 위해 고안되었습니다.",

    "Uptake varies with the square root of time when intraparticle "
    "diffusion controls the rate.":
        "입자 내 확산이 속도를 지배할 때 흡착량이 시간의 제곱근에 따라 "
        "변합니다.",
    "Should be analysed as multiple linear segments, not one line.":
        "직선 하나가 아니라 여러 개의 선형 구간으로 나누어 해석해야 합니다.",
    "An intercept C = 0 is the diagnostic for intraparticle diffusion "
    "being the sole rate-limiting step.":
        "절편 C = 0은 입자 내 확산이 유일한 속도결정 단계임을 가리키는 "
        "진단 지표입니다.",

    "The rate is controlled by diffusion of adsorbate across the stagnant "
    "liquid film around the adsorbent particle.":
        "흡착제 입자를 둘러싼 정체된 액막을 가로지르는 흡착질의 확산이 속도를 "
        "지배합니다.",
    "Diagnostic: a plot of ln(1 − F) vs t is linear and passes through the "
    "origin if film diffusion controls.":
        "진단 지표: 막 확산이 지배하면 ln(1 − F) 대 t 그래프가 직선이고 원점을 "
        "지납니다.",
    "Mathematically identical to pseudo-first-order; the difference is "
    "interpretive, not algebraic.":
        "수학적으로 유사 1차식과 동일하며, 차이는 대수적인 것이 아니라 "
        "해석상의 것입니다.",

    "Pore diffusion is the rate-controlling step.":
        "세공 확산이 속도결정 단계입니다.",
    "A linear double-log Bangham plot supports pore diffusion control; "
    "curvature argues against it.":
        "이중 로그 Bangham 그래프가 직선이면 세공 확산 지배를 뒷받침하고, "
        "휘어 있으면 그에 반하는 근거가 됩니다.",
    "AdsorpFit fits the equivalent power-law form q_t = k₀tᵅ directly, "
    "which avoids the double logarithm's severe error distortion.":
        "AdsorpFit은 동등한 멱법칙 형태 q_t = k₀tᵅ를 직접 적합하므로, 이중 "
        "로그가 일으키는 심한 오차 왜곡을 피합니다.",

    "Spherical, homogeneous particles of uniform radius r.":
        "반지름 r이 균일한 구형의 균질 입자를 가정합니다.",
    "Diffusion within the particle follows Fick's law with a constant D.":
        "입자 내 확산이 일정한 D를 갖는 픽의 법칙을 따릅니다.",
    "Surface concentration reaches equilibrium instantaneously (no film "
    "resistance).":
        "표면 농도가 즉시 평형에 도달합니다(막 저항 없음).",
    "D and r are strongly correlated, fix r at its measured value.":
        "D와 r은 강하게 상관되어 있으므로, r은 측정값으로 고정하세요.",

    "Adsorption proceeds in two parallel or sequential steps with distinct "
    "rate constants: typically a fast external surface step and a slow "
    "internal diffusion step.":
        "서로 다른 속도상수를 갖는 두 단계가 병렬 또는 순차로 진행됩니다. "
        "보통 빠른 외부 표면 단계와 느린 내부 확산 단계입니다.",
    "Appropriate when the uptake curve shows a clear two-stage shape that "
    "a single exponential cannot follow.":
        "단일 지수항으로는 따라갈 수 없는 뚜렷한 2단계 형태가 흡착 곡선에 "
        "나타날 때 적절합니다.",

    # ----------------------------------------------------------- isotherms
    "Adsorption is confined to a monolayer, with no stacking of "
    "adsorbate.":
        "흡착이 단분자층에 한정되며, 흡착질이 겹겹이 쌓이지 않습니다.",
    "All sites are energetically identical (a homogeneous surface).":
        "모든 흡착점의 에너지가 동일합니다(균일한 표면).",
    "Adsorbed molecules do not interact with each other laterally.":
        "흡착된 분자들 사이에 측면 상호작용이 없습니다.",
    "Each site holds exactly one molecule, and adsorption is reversible.":
        "흡착점 하나에 분자 하나만 결합하며, 흡착은 가역적입니다.",

    "The surface is energetically heterogeneous, with an exponential "
    "distribution of site energies.":
        "표면이 에너지적으로 불균일하며, 흡착점 에너지가 지수 분포를 "
        "따릅니다.",
    "Adsorption is multilayer and not limited to a fixed number of sites.":
        "흡착이 다층이며 정해진 수의 흡착점에 한정되지 않습니다.",
    "The heat of adsorption falls logarithmically as coverage increases.":
        "피복률이 증가하면 흡착열이 로그 형태로 감소합니다.",

    "The heat of adsorption of all molecules in the layer decreases "
    "linearly with surface coverage, because of adsorbate–adsorbate "
    "repulsion.":
        "흡착질 사이의 반발 때문에, 층 안 모든 분자의 흡착열이 표면 피복률에 "
        "따라 선형으로 감소합니다.",
    "Adsorption is characterised by a uniform distribution of binding "
    "energies up to a maximum.":
        "결합 에너지가 최댓값까지 균일하게 분포하는 것으로 봅니다.",
    "Valid only at intermediate coverage; it diverges as Ce → 0.":
        "중간 피복률에서만 유효하며, Ce → 0에서 발산합니다.",

    "Adsorption proceeds by pore filling rather than layer-by-layer "
    "coverage.":
        "층을 하나씩 덮는 것이 아니라 세공을 채우는 방식으로 흡착이 "
        "진행됩니다.",
    "The adsorption potential is temperature-invariant (the "
    "characteristic curve).":
        "흡착 퍼텐셜이 온도에 무관합니다(특성 곡선).",
    "Designed for microporous adsorbents; less appropriate for flat "
    "surfaces.":
        "미세다공성 흡착제를 위해 고안되었으며, 평탄한 표면에는 덜 "
        "적절합니다.",
    "Gives the mean free energy E, which is the model's main purpose.":
        "이 모델의 주된 목적인 평균 자유에너지 E를 제공합니다.",

    "Monolayer coverage as in Langmuir, but allowing for mechanical "
    "contact between adsorbing and desorbing molecules.":
        "Langmuir처럼 단분자층 피복을 가정하되, 흡착하는 분자와 탈착하는 분자 "
        "사이의 역학적 접촉을 허용합니다.",
    "Approaches the Langmuir result at low coverage and the same plateau "
    "at saturation, but rises more sharply in between.":
        "낮은 피복률에서는 Langmuir의 결과에, 포화에서는 같은 평탄역에 "
        "가까워지지만, 그 사이에서는 더 가파르게 상승합니다.",

    "Describes multilayer adsorption at a relatively large distance from "
    "the surface.":
        "표면에서 비교적 멀리 떨어진 곳에서의 다층 흡착을 설명합니다.",
    "Suited to heteroporous solids; mathematically equivalent to "
    "Freundlich with n_H = -n, so the two always give the same R².":
        "이질적인 세공 구조의 고체에 적합합니다. n_H = -n으로 두면 Freundlich와 "
        "수학적으로 동등하므로 둘의 R²은 언제나 같습니다.",

    "Multilayer adsorption on a heterogeneous pore distribution.":
        "불균일한 세공 분포 위에서의 다층 흡착을 가정합니다.",
    "Assumes the existence of a condensed film on the adsorbent surface.":
        "흡착제 표면에 응축된 막이 존재한다고 가정합니다.",

    "Multilayer adsorption: molecules adsorb on top of already-adsorbed "
    "molecules.":
        "다층 흡착입니다. 이미 흡착된 분자 위에 다른 분자가 흡착합니다.",
    "The first layer has a distinct adsorption energy; all higher layers "
    "have the energy of condensation of the bulk adsorbate.":
        "첫 번째 층은 고유한 흡착 에너지를 가지며, 그 위의 모든 층은 벌크 "
        "흡착질의 응축 에너지를 갖습니다.",
    "Requires the saturation concentration Cs, the solute's solubility "
    "limit.":
        "용질의 용해도 한계인 포화 농도 Cs가 필요합니다.",

    "Adsorption sites increase exponentially with coverage, implying "
    "multilayer adsorption.":
        "피복률이 증가하면 흡착점이 지수적으로 늘어나며, 이는 다층 흡착을 "
        "뜻합니다.",
    "Derived from a kinetic principle rather than an equilibrium one.":
        "평형이 아니라 속도론적 원리에서 유도되었습니다.",

    "A hybrid of Langmuir and Freundlich: Freundlich-like at low Ce, "
    "Langmuir-like at high Ce.":
        "Langmuir와 Freundlich의 혼합형입니다. 낮은 Ce에서는 Freundlich에, "
        "높은 Ce에서는 Langmuir에 가깝게 거동합니다.",
    "Reduces exactly to Langmuir when m_s = 1 and to Freundlich at low "
    "Ce.":
        "m_s = 1이면 정확히 Langmuir가 되고, 낮은 Ce에서는 Freundlich가 "
        "됩니다.",
    "Describes localised adsorption without adsorbate–adsorbate "
    "interaction.":
        "흡착질 사이의 상호작용이 없는 국재화된 흡착을 설명합니다.",

    "Derived from potential theory for heterogeneous adsorption.":
        "불균일 흡착에 대한 퍼텐셜 이론에서 유도되었습니다.",
    "Obeys the Henry's law limit as Ce → 0 and saturates at high Ce, the "
    "main advantage over Langmuir and Freundlich respectively.":
        "Ce → 0에서 헨리 법칙 극한을 따르고 높은 Ce에서 포화합니다. 각각 "
        "Freundlich와 Langmuir에 대한 주된 장점입니다.",
    "Assumes an asymmetric quasi-Gaussian distribution of site energies, "
    "with most sites having energies below the mean.":
        "흡착점 에너지가 비대칭 준가우스 분포를 따르며, 대부분의 흡착점이 평균 "
        "이하의 에너지를 갖는다고 가정합니다.",

    "An empirical hybrid of Langmuir and Freundlich.":
        "Langmuir와 Freundlich의 경험적 혼합형입니다.",
    "Applies over a wide concentration range and to both homogeneous and "
    "heterogeneous systems.":
        "넓은 농도 범위에, 그리고 균일한 계와 불균일한 계 모두에 "
        "적용됩니다.",
    "Reduces to Langmuir at g = 1 and to Henry's law at g = 0.":
        "g = 1에서는 Langmuir가, g = 0에서는 헨리 법칙이 됩니다.",

    "A general model for pure solutions, intended for multi-component "
    "systems.":
        "순수 용액을 위한 일반 모델로, 다성분계를 염두에 두고 만들어졌습니다.",
    "Reduces to Langmuir at a_K = 1 and to Freundlich at high Ce with "
    "a_K < 1.":
        "a_K = 1에서는 Langmuir가 되고, a_K < 1인 높은 Ce에서는 Freundlich가 "
        "됩니다.",

    "Performs particularly well at dilute concentrations, its original "
    "purpose.":
        "본래 목적대로 묽은 농도에서 특히 잘 맞습니다.",
    "Reduces to Langmuir at m_RP = 1, to Freundlich at intermediate "
    "values, and to Henry's law at m_RP = 0.":
        "m_RP = 1에서는 Langmuir, 중간값에서는 Freundlich, m_RP = 0에서는 헨리 "
        "법칙이 됩니다.",

    "Derived for binding of a ligand to a homogeneous substrate.":
        "균일한 기질에 대한 리간드 결합을 위해 유도되었습니다.",
    "Explicitly models cooperativity, whether bound molecules help or "
    "hinder further binding at the remaining sites.":
        "결합한 분자가 남은 흡착점에서의 추가 결합을 돕는지 방해하는지, 즉 "
        "협동성을 명시적으로 모델링합니다.",
    "Can produce sigmoidal isotherms, which Langmuir and Freundlich "
    "cannot.":
        "Langmuir와 Freundlich가 만들지 못하는 S자형 등온선을 만들 수 "
        "있습니다.",

    "An empirical combination of the Langmuir and Freundlich forms.":
        "Langmuir와 Freundlich 형태를 경험적으로 결합한 식입니다.",
    "n must be ≥ 1 for the model to be thermodynamically consistent; "
    "n < 1 means the data are better described by another model.":
        "모델이 열역학적으로 정합하려면 n ≥ 1이어야 합니다. n < 1이면 다른 "
        "모델이 데이터를 더 잘 설명한다는 뜻입니다.",
    "Saturation capacity is A/B.": "포화 흡착용량은 A/B입니다.",

    "Derived from a statistical distribution of adsorption energies (a "
    "deformed exponential / Weibull form).":
        "흡착 에너지의 통계적 분포에서 유도되었습니다(변형 지수 또는 Weibull "
        "형태).",
    "α characterises the width of the site-energy distribution.":
        "α는 흡착점 에너지 분포의 폭을 나타냅니다.",
    "Reduces to the Jovanović isotherm when α = 1.":
        "α = 1이면 Jovanović 등온식이 됩니다.",

    "Two populations of adsorbate coexist: one dissolved into the solid "
    "following Henry's law, one bound to discrete sites following "
    "Langmuir.":
        "두 종류의 흡착질이 공존합니다. 하나는 헨리 법칙에 따라 고체에 "
        "용해되고, 다른 하나는 Langmuir에 따라 개별 흡착점에 결합합니다.",
    "Originally derived for gas diffusion in polymers; used for adsorbents "
    "with both a dissolution and a site-binding mechanism.":
        "본래 고분자 내 기체 확산을 위해 유도되었으며, 용해와 흡착점 결합 "
        "메커니즘을 모두 갖는 흡착제에 사용합니다.",

    "A flexible empirical equation with no single mechanistic derivation.":
        "단일한 메커니즘적 유도가 없는 유연한 경험식입니다.",
    "Reduces to Langmuir when α = β = 1 and to Sips when α = β.":
        "α = β = 1이면 Langmuir가, α = β이면 Sips가 됩니다.",
    "Its flexibility means it almost always fits well, which makes a good "
    "fit weak evidence for anything mechanistic.":
        "유연한 만큼 거의 언제나 잘 맞으므로, 잘 맞는다는 사실은 메커니즘에 "
        "대한 약한 근거일 뿐입니다.",

    "An extension of Langmuir in which the affinity b_0 is itself allowed "
    "to vary with coverage.":
        "친화도 b_0 자체가 피복률에 따라 변하도록 허용한 Langmuir의 "
        "확장입니다.",
    "Valid only over a restricted range: 1 + x + y and 1 + x must both "
    "stay between 0 and 1.":
        "제한된 범위에서만 유효합니다. 1 + x + y와 1 + x가 모두 0과 1 사이에 "
        "있어야 합니다.",

    "Derived from a generalised (quasi-Gaussian) distribution of "
    "adsorption energies, with m and n controlling each tail "
    "independently.":
        "일반화된 준가우스 흡착 에너지 분포에서 유도되었으며, m과 n이 각 꼬리를 "
        "따로 결정합니다.",
    "Reduces to Langmuir–Freundlich (Sips) when m = n, and to Langmuir "
    "when m = n = 1.":
        "m = n이면 Langmuir–Freundlich(Sips)가 되고, m = n = 1이면 Langmuir가 "
        "됩니다.",
}
