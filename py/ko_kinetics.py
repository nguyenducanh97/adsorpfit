# -*- coding: utf-8 -*-
"""Korean for the kinetic model interpretations and their domain warnings."""

KO_KINETICS = {

    # ------------------------------------------------ pseudo-first-order
    "The calculated equilibrium capacity is q_e,cal = {qe} mg/g and the "
    "pseudo-first-order rate constant is k₁ = {k1} min⁻¹.":
        "계산된 평형 흡착량은 q_e,cal = {qe} mg/g, 유사 1차 속도상수는 "
        "k₁ = {k1} min⁻¹입니다.",

    "k₁ sets the timescale of uptake: the half-time is t₁/₂ = ln2/k₁ = "
    "{t_half} min, and 95% of equilibrium is reached at about {t95} min. "
    "Those numbers, not k₁ itself, are what a column or batch reactor "
    "design actually needs.":
        "k₁은 흡착의 시간 척도를 정합니다. 반감시간은 t₁/₂ = ln2/k₁ = "
        "{t_half} min이고, 평형의 95%에는 약 {t95} min에 도달합니다. 컬럼이나 "
        "회분식 반응기 설계에 실제로 필요한 값은 k₁ 자체가 아니라 이 "
        "수치들입니다.",

    "Lagergren's model assumes the rate of uptake is proportional to the "
    "number of *unoccupied* sites, (q_e − q_t). Mechanistically that "
    "corresponds to adsorption controlled by physisorption onto a surface "
    "where the driving force is simply the remaining free capacity; it "
    "does not imply a first-order chemical reaction.":
        "Lagergren 모델은 흡착 속도가 *비어 있는* 흡착점의 수 (q_e − q_t)에 "
        "비례한다고 가정합니다. 메커니즘으로 보면 남은 여유 용량 자체가 "
        "추진력인 물리흡착에 지배되는 경우에 해당하며, 1차 화학반응을 "
        "뜻하지는 않습니다.",

    "Consistency warning: the fitted q_e,cal ({qe} mg/g) differs from your "
    "highest measured loading ({q_obs} mg/g) by {diff:.0f}%. A PFO fit "
    "whose q_e,cal disagrees badly with q_e,exp is the classic sign that "
    "the model is wrong for these data, no matter how good R² looks. "
    "Compare q_e,cal against q_e,exp for every kinetic model you report: "
    "this check catches more bad fits than R² does.":
        "정합성 경고: 적합된 q_e,cal({qe} mg/g)이 측정된 최대 흡착량"
        "({q_obs} mg/g)과 {diff:.0f}% 차이가 납니다. q_e,cal이 q_e,exp와 크게 "
        "어긋나는 유사 1차 적합은 R²이 아무리 좋아 보여도 모델이 이 데이터에 "
        "맞지 않다는 전형적인 신호입니다. 보고하는 모든 속도식에 대해 "
        "q_e,cal과 q_e,exp를 비교하세요. 이 점검이 R²보다 더 많은 잘못된 "
        "적합을 걸러냅니다.",

    "q_e,cal ({qe} mg/g) agrees with the observed plateau ({q_obs} mg/g) "
    "to within {diff:.0f}%, which supports the model.":
        "q_e,cal({qe} mg/g)이 관측된 평탄역({q_obs} mg/g)과 {diff:.0f}% 이내로 "
        "일치하며, 이는 모델을 뒷받침합니다.",

    "PFO is generally the better description of the *early* stage of "
    "adsorption and tends to underpredict the approach to equilibrium. If "
    "it fits your first few points but drifts later, that pattern is "
    "expected rather than surprising.":
        "유사 1차식은 대체로 흡착의 *초기* 단계를 더 잘 설명하며, 평형에 "
        "가까워지는 구간은 과소예측하는 경향이 있습니다. 앞쪽 몇 점은 잘 맞고 "
        "뒤로 갈수록 어긋난다면, 놀랄 일이 아니라 예상되는 양상입니다.",

    # ----------------------------------------------- pseudo-second-order
    "q_e,cal = {qe} mg/g and k₂ = {k2} g mg⁻¹ min⁻¹.":
        "q_e,cal = {qe} mg/g, k₂ = {k2} g mg⁻¹ min⁻¹입니다.",

    "The initial adsorption rate is h = k₂·q_e² = {h} mg g⁻¹ min⁻¹, the "
    "slope of uptake at t = 0, and the most directly comparable number "
    "between experiments. The half-time is t₁/₂ = 1/(k₂q_e) = "
    "{t_half} min.":
        "초기 흡착 속도는 h = k₂·q_e² = {h} mg g⁻¹ min⁻¹로, t = 0에서의 흡착 "
        "기울기이며 실험 사이에 가장 직접 비교할 수 있는 값입니다. 반감시간은 "
        "t₁/₂ = 1/(k₂q_e) = {t_half} min입니다.",

    "The pseudo-second-order model assumes the rate depends on the "
    "*square* of the number of free sites, d q_t/dt = k₂(q_e − q_t)². It "
    "is conventionally read as evidence that chemisorption, meaning "
    "valency forces through sharing or exchange of electrons: controls the "
    "rate.":
        "유사 2차 모델은 속도가 비어 있는 흡착점 수의 *제곱*에 의존한다고 "
        "가정합니다(d q_t/dt = k₂(q_e − q_t)²). 관례적으로는 전자의 공유나 "
        "교환에 의한 원자가 힘, 즉 화학흡착이 속도를 지배한다는 근거로 "
        "읽습니다.",

    "q_e,cal vs q_e,exp: {qe} vs {q_obs} mg/g ({diff:.0f}% apart).":
        "q_e,cal 대 q_e,exp: {qe} 대 {q_obs} mg/g({diff:.0f}% 차이).",

    "Two cautions that the literature routinely omits. First, PSO fits "
    "almost every batch dataset well, because its algebraic form happens "
    "to match the shape of a saturating curve, so a high R² for PSO is "
    "weak evidence of chemisorption, not strong evidence. Second, k₂ is "
    "not a true constant: it varies systematically with initial "
    "concentration, adsorbent dose and particle size, so k₂ values are "
    "only comparable between experiments run under identical conditions.":
        "문헌에서 흔히 빠뜨리는 두 가지 주의점이 있습니다. 첫째, 유사 2차식은 "
        "거의 모든 회분식 데이터에 잘 맞습니다. 그 대수적 형태가 포화 곡선의 "
        "모양과 우연히 일치하기 때문입니다. 따라서 유사 2차식의 높은 R²은 "
        "화학흡착의 강한 근거가 아니라 약한 근거입니다. 둘째, k₂는 진정한 "
        "상수가 아닙니다. 초기 농도, 흡착제 투입량, 입자 크기에 따라 체계적으로 "
        "변하므로, k₂ 값은 동일한 조건에서 수행한 실험끼리만 비교할 수 "
        "있습니다.",

    "Because your data were collected at C₀ = {c0} mg/L, the k₂ reported "
    "here belongs to that concentration only. To claim a "
    "concentration-independent mechanism you would need k₂ measured across "
    "several C₀ values and shown to be constant: which it usually is not.":
        "데이터가 C₀ = {c0} mg/L에서 얻어졌으므로, 여기 보고된 k₂는 그 농도에만 "
        "해당합니다. 농도에 무관한 메커니즘을 주장하려면 여러 C₀에서 k₂를 "
        "측정해 일정함을 보여야 하는데, 보통은 일정하지 않습니다.",

    # ------------------------------------------------------------ Elovich
    "α = {a} mg g⁻¹ min⁻¹ is the initial adsorption rate, the uptake rate "
    "when the surface is still bare.":
        "α = {a} mg g⁻¹ min⁻¹은 초기 흡착 속도로, 표면이 아직 비어 있을 때의 "
        "흡착 속도입니다.",

    "β = {b} g mg⁻¹ is the desorption constant, related to the extent of "
    "surface coverage and the activation energy for chemisorption. 1/β = "
    "{v1} mg/g indicates how much the surface can take up before the rate "
    "falls off appreciably.":
        "β = {b} g mg⁻¹은 탈착 상수로, 표면 피복 정도 및 화학흡착 활성화 "
        "에너지와 관련됩니다. 1/β = {v1} mg/g은 속도가 뚜렷이 느려지기 전까지 "
        "표면이 받아들일 수 있는 양을 나타냅니다.",

    "The Elovich equation assumes the activation energy for adsorption "
    "rises *linearly* with coverage. That is the behaviour of a genuinely "
    "heterogeneous surface undergoing chemisorption: the strongest sites "
    "are consumed first, so each additional molecule faces a higher "
    "barrier.":
        "Elovich 식은 흡착 활성화 에너지가 피복률에 따라 *선형으로* 증가한다고 "
        "가정합니다. 이는 화학흡착이 일어나는 진짜 불균일 표면의 거동입니다. "
        "가장 강한 흡착점이 먼저 소모되므로, 분자가 하나씩 더해질 때마다 더 "
        "높은 장벽을 만납니다.",

    "The product αβ = {v2} min⁻¹ sets where the logarithmic regime begins; "
    "the usual simplification q_t = (1/β)ln(αβ) + (1/β)ln t requires "
    "αβt ≫ 1, which holds here for t ≫ {v1} min. AdsorpFit fits the exact "
    "form q_t = (1/β)ln(1 + αβt) instead, so it stays valid at short times "
    "too.":
        "곱 αβ = {v2} min⁻¹은 로그 영역이 시작되는 지점을 정합니다. 흔히 쓰는 "
        "단순화 q_t = (1/β)ln(αβ) + (1/β)ln t는 αβt ≫ 1을 요구하며, 여기서는 "
        "t ≫ {v1} min에서 성립합니다. AdsorpFit은 대신 정확한 형태 "
        "q_t = (1/β)ln(1 + αβt)를 적합하므로 짧은 시간에서도 유효합니다.",

    "A good Elovich fit is one of the more specific pieces of evidence for "
    "a heterogeneous surface, because the model has no plateau and cannot "
    "mimic a simple saturating curve the way PSO can.":
        "Elovich 적합이 좋다는 것은 불균일 표면을 가리키는 비교적 구체적인 "
        "근거입니다. 이 모델에는 평탄역이 없어, 유사 2차식처럼 단순한 포화 "
        "곡선을 흉내 낼 수 없기 때문입니다.",

    "Your data have clearly reached a plateau. The Elovich equation has no "
    "equilibrium plateau: it rises logarithmically without limit: so it "
    "cannot reproduce the flat region and will systematically overshoot at "
    "long times. It suits data still in the rising, "
    "chemisorption-controlled stage.":
        "데이터가 분명히 평탄역에 도달했습니다. Elovich 식에는 평형 평탄역이 "
        "없고 한없이 로그 형태로 상승하므로, 평탄 구간을 재현할 수 없고 긴 "
        "시간대에서 체계적으로 과대예측합니다. 아직 상승 중인, 화학흡착이 "
        "지배하는 단계의 데이터에 적합합니다.",

    # ------------------------------------------------------------- Avrami
    "q_e = {qe} mg/g, k_AV = {kav} min⁻¹, n_AV = {n}.":
        "q_e = {qe} mg/g, k_AV = {kav} min⁻¹, n_AV = {n}입니다.",

    "The Avrami equation comes from nucleation-and-growth theory and was "
    "adapted to adsorption to allow a *fractional* reaction order. Its "
    "value is that n_AV is not forced to 1 or 2; it is fitted, so the data "
    "choose.":
        "Avrami 식은 핵생성 및 성장 이론에서 온 것으로, *분수* 반응차수를 "
        "허용하기 위해 흡착에 적용되었습니다. 이 식의 장점은 n_AV를 1이나 2로 "
        "강요하지 않고 적합한다는 점, 즉 데이터가 차수를 고르게 한다는 "
        "점입니다.",

    "n_AV = {n} is the fractional kinetic order. It reflects possible "
    "changes in the adsorption mechanism as the process advances, rather "
    "than a single elementary step.":
        "n_AV = {n}은 분수 반응차수입니다. 단일 소단계가 아니라, 과정이 "
        "진행되면서 흡착 메커니즘이 달라질 수 있음을 반영합니다.",

    "n_AV ≈ 1 makes Avrami equivalent to pseudo-first-order.":
        "n_AV ≈ 1이면 Avrami는 유사 1차식과 같아집니다.",

    "n_AV ≈ 2 puts the kinetics close to second-order behaviour.":
        "n_AV ≈ 2이면 속도 거동이 2차에 가깝습니다.",

    "n_AV = {n} below 1 indicates the rate decays faster than first-order "
    "at early times: often read as a broad distribution of site "
    "reactivities, or as diffusion beginning to limit the rate.":
        "n_AV = {n}으로 1보다 작으면 초기에 속도가 1차보다 빠르게 감소한다는 "
        "뜻입니다. 흡착점 반응성의 분포가 넓거나, 확산이 속도를 제한하기 "
        "시작한 것으로 해석하는 경우가 많습니다.",

    "n_AV = {n} between 1 and 2 sits between first- and second-order "
    "behaviour, which is the common outcome and is the main argument for "
    "fitting Avrami rather than forcing PFO or PSO.":
        "n_AV = {n}으로 1과 2 사이이면 1차와 2차 거동의 중간입니다. 가장 흔한 "
        "결과이며, 유사 1차나 유사 2차를 강요하는 대신 Avrami를 적합하는 주된 "
        "근거이기도 합니다.",

    # ------------------------------------------------------- mixed order
    "q_e = {qe} mg/g, k = {k} min⁻¹, f₂ = {f2}.":
        "q_e = {qe} mg/g, k = {k} min⁻¹, f₂ = {f2}입니다.",

    "f₂ is the headline number: it is the fraction of the uptake behaving "
    "as second order. f₂ = {f2} means the process is ":
        "핵심 수치는 f₂로, 흡착 가운데 2차로 거동하는 비율입니다. f₂ = {f2}은 "
        "이 과정이 ",

    "genuinely mixed, roughly {v1:.0f}% second-order in character. This is "
    "the case where MOE earns its extra parameter: neither PFO nor PSO "
    "alone is right.":
        "실제로 혼합형이며 성격상 약 {v1:.0f}%가 2차임을 뜻합니다. 혼합차수 "
        "모델이 추가 매개변수를 쓸 값어치를 하는 경우로, 유사 1차나 유사 2차 "
        "어느 하나만으로는 맞지 않습니다.",

    # --------------------------------------------------------- nth order
    "q_e = {qe} mg/g, k_n = {kn}, n = {n}.":
        "q_e = {qe} mg/g, k_n = {kn}, n = {n}입니다.",

    "The fitted order n = {n} is the result that matters. ":
        "중요한 결과는 적합된 차수 n = {n}입니다. ",

    "It is far from both 1 and 2, which means neither PFO nor PSO is the "
    "right description: forcing one of them onto these data would give a "
    "rate constant with no physical meaning.":
        "1과 2 모두에서 멀리 떨어져 있으므로 유사 1차도 유사 2차도 올바른 "
        "설명이 아닙니다. 둘 중 하나를 이 데이터에 강요하면 물리적 의미가 없는 "
        "속도상수가 나옵니다.",

    # ---------------------------------------------------------- Ritchie
    "q_e = {qe} mg/g, k_R = {kR} min⁻¹, n = {n}.":
        "q_e = {qe} mg/g, k_R = {kR} min⁻¹, n = {n}입니다.",

    "Unlike the empirical nth-order model, Ritchie's n has a physical "
    "referent: the number of surface sites occupied by a single adsorbate "
    "molecule. n = {n} therefore suggests ":
        "경험적인 n차 모델과 달리 Ritchie의 n에는 물리적 대응물이 있습니다. "
        "흡착질 분자 하나가 차지하는 표면 흡착점의 수입니다. 따라서 n = {n}은 ",

    "roughly {n:.1f} sites per molecule, a non-integer value that usually "
    "means the site picture is an oversimplification here.":
        "분자당 약 {n:.1f}개의 흡착점을 뜻합니다. 정수가 아니라는 것은 보통 "
        "흡착점 개념이 여기서는 지나친 단순화임을 의미합니다.",

    # ----------------------------------------------------- fractal PFO
    "q_e = {qe} mg/g, k₁′ = {k1}, h = {h}.":
        "q_e = {qe} mg/g, k₁′ = {k1}, h = {h}입니다.",

    "The fractal exponent h = {h} is the point of this model. ":
        "이 모델의 핵심은 프랙탈 지수 h = {h}입니다. ",

    "h > 0 means the effective rate constant decays with time as t^(−h). "
    "This is what happens on a geometrically disordered or fractal "
    "surface: the adsorbate and the remaining free sites become "
    "progressively segregated, so the encounter rate falls even though "
    "sites remain available. A larger h means stronger disorder.":
        "h > 0은 유효 속도상수가 시간에 따라 t^(−h)로 감소함을 뜻합니다. "
        "기하학적으로 무질서하거나 프랙탈인 표면에서 일어나는 일로, 흡착질과 "
        "남은 빈 흡착점이 점점 분리되어 자리가 남아 있어도 만날 확률이 "
        "떨어집니다. h가 클수록 무질서가 강합니다.",

    # ------------------------------------------------------ Weber–Morris
    "k_id = {kid} mg g⁻¹ min⁻⁰·⁵ is the intraparticle diffusion rate "
    "constant, and C = {C} mg/g is the intercept.":
        "k_id = {kid} mg g⁻¹ min⁻⁰·⁵은 입자 내 확산 속도상수이고, "
        "C = {C} mg/g은 절편입니다.",

    "The intercept C is the informative parameter here, and it is what the "
    "Weber–Morris plot is actually for. C is proportional to the thickness "
    "of the boundary layer surrounding the particle.":
        "여기서 정보를 담고 있는 매개변수는 절편 C이며, Weber–Morris 그래프는 "
        "본래 이를 보기 위한 것입니다. C는 입자를 둘러싼 경계층의 두께에 "
        "비례합니다.",

    "C = {C} mg/g is essentially zero, so the line passes through the "
    "origin. That is the specific condition under which intraparticle "
    "diffusion is the **sole** rate-limiting step, external film diffusion "
    "contributes nothing measurable.":
        "C = {C} mg/g은 사실상 0이므로 직선이 원점을 지납니다. 이는 입자 내 "
        "확산이 **유일한** 속도결정 단계이고 외부 막 확산의 기여를 측정할 수 "
        "없는 특정 조건입니다.",

    "C = {C} mg/g is significantly greater than zero, so the plot does NOT "
    "pass through the origin. Intraparticle diffusion is therefore "
    "involved but is **not the only** rate-controlling step: film "
    "(boundary layer) diffusion contributes as well. The larger C is, the "
    "greater the boundary-layer contribution.":
        "C = {C} mg/g은 0보다 뚜렷이 크므로 그래프가 원점을 지나지 "
        "**않습니다**. 따라서 입자 내 확산이 관여하지만 **유일한** 속도결정 "
        "단계는 아니며, 막(경계층) 확산도 함께 기여합니다. C가 클수록 경계층의 "
        "기여가 큽니다.",

    "The fitted intercept C = {C} mg/g is negative, so the line predicts a "
    "negative loading for all t below {t_zero} min. C is meant to be "
    "proportional to boundary-layer thickness and cannot be negative "
    "physically. This is the usual sign that a single straight line has "
    "been forced through what are really two or three distinct diffusion "
    "stages; use the multi-region analysis on the Diffusion tab instead of "
    "this single-line fit.":
        "적합된 절편 C = {C} mg/g이 음수이므로, {t_zero} min 미만의 모든 t에서 "
        "직선이 음의 흡착량을 예측합니다. C는 경계층 두께에 비례하는 값이어서 "
        "물리적으로 음수가 될 수 없습니다. 실제로는 둘 또는 셋으로 구분되는 "
        "확산 단계에 직선 하나를 억지로 맞춘 경우의 전형적인 신호입니다. 이 "
        "단일 직선 적합 대신 확산 탭의 다구간 해석을 사용하세요.",

    "Important methodological point: a single straight line fitted through "
    "all your q_t vs √t points is almost always the wrong analysis. The "
    "standard interpretation requires you to identify *multiple linear "
    "regions*, typically an initial fast external surface adsorption "
    "stage, a second gradual stage where intraparticle diffusion is "
    "rate-limiting, and a final plateau as equilibrium is approached. Use "
    "the multi-region tool in AdsorpFit to segment the plot; each segment "
    "gets its own k_id and C, and their relative slopes tell you which "
    "step controls the rate.":
        "방법론적으로 중요한 점이 있습니다. q_t 대 √t의 모든 점에 직선 하나를 "
        "맞추는 것은 거의 언제나 잘못된 해석입니다. 표준적인 해석은 *여러 개의 "
        "선형 구간*을 찾는 것이며, 보통 초기의 빠른 외부 표면 흡착 단계, 입자 "
        "내 확산이 속도를 제한하는 완만한 두 번째 단계, 평형에 가까워지며 "
        "나타나는 마지막 평탄역으로 나뉩니다. AdsorpFit의 다구간 도구로 "
        "그래프를 나누세요. 구간마다 고유한 k_id와 C가 얻어지며, 구간들의 상대 "
        "기울기가 어느 단계가 속도를 지배하는지 알려 줍니다.",

    "Fitted here as one straight line over all points. That is almost "
    "never the right analysis: the standard interpretation requires "
    "identifying separate linear regions. The Diffusion tab does that "
    "segmentation and is what you should report.":
        "여기서는 모든 점에 직선 하나로 적합했습니다. 이는 거의 언제나 올바른 "
        "해석이 아닙니다. 표준적인 해석은 구간을 나누어 선형 영역을 찾는 "
        "것입니다. 확산 탭이 그 분할을 수행하며, 보고해야 할 것은 그 "
        "결과입니다.",

    # ------------------------------------------------------ film diffusion
    "q_e = {qe} mg/g and k_fd = {kfd} min⁻¹.":
        "q_e = {qe} mg/g, k_fd = {kfd} min⁻¹입니다.",

    # ----------------------------------------------------------- Bangham
    "k₀ = {k0} and α = {alpha}.":
        "k₀ = {k0}, α = {alpha}입니다.",

    "α = {alpha} is the diagnostic. ":
        "진단 지표는 α = {alpha}입니다. ",

    "Being below 1, it is consistent with diffusion into the pore network "
    "controlling the rate: uptake slows progressively as the adsorbate "
    "must travel further into the particle.":
        "1보다 작으므로, 세공 구조 안으로의 확산이 속도를 지배한다는 해석과 "
        "맞습니다. 흡착질이 입자 안쪽으로 더 멀리 이동해야 하므로 흡착이 "
        "점차 느려집니다.",

    "α ≥ 1 means uptake is not decelerating the way pore diffusion "
    "requires, which argues against pore-diffusion control.":
        "α ≥ 1은 세공 확산이 요구하는 방식으로 흡착이 감속하지 않는다는 "
        "뜻이므로, 세공 확산 지배에 반하는 근거입니다.",

    "The Bangham power law is undefined at t = 0; that point is handled by "
    "clamping and contributes little to the fit.":
        "Bangham 멱법칙은 t = 0에서 정의되지 않습니다. 해당 점은 값을 제한해 "
        "처리하며 적합에 거의 기여하지 않습니다.",

    # ------------------------------------------------------------- Crank
    "q_e = {qe} mg/g, D = {D} cm²/min, r = {r} cm.":
        "q_e = {qe} mg/g, D = {D} cm²/min, r = {r} cm입니다.",

    "D is the effective intraparticle diffusion coefficient and is the "
    "only parameter here with transferable physical meaning. ":
        "D는 유효 입자 내 확산계수이며, 여기서 다른 계로 옮겨 쓸 수 있는 "
        "물리적 의미를 가진 유일한 매개변수입니다. ",

    "D and r enter this model only as D/r², so they cannot be determined "
    "separately. Enter your measured particle radius in the experiment "
    "panel and treat D as the single fitted quantity; otherwise neither "
    "number means anything on its own.":
        "이 모델에서 D와 r은 D/r² 형태로만 들어가므로 따로 결정할 수 없습니다. "
        "실험 패널에 측정한 입자 반지름을 입력하고 D를 적합되는 유일한 값으로 "
        "보세요. 그렇게 하지 않으면 두 수치 모두 단독으로는 아무 의미가 "
        "없습니다.",

    # ------------------------------------------------- double exponential
    "q_e = {qe} mg/g. Fast step: a₁ = {a1} mg/g at k_D1 = {k1} min⁻¹. Slow "
    "step: {v1} mg/g at k_D2 = {k2} min⁻¹.":
        "q_e = {qe} mg/g입니다. 빠른 단계: a₁ = {a1} mg/g, "
        "k_D1 = {k1} min⁻¹. 느린 단계: {v1} mg/g, k_D2 = {k2} min⁻¹.",

    "The fast step accounts for {v1:.0f}% of the total uptake.":
        "빠른 단계가 전체 흡착량의 {v1:.0f}%를 차지합니다.",

    "The two rate constants differ by a factor of {v1}. ":
        "두 속도상수는 {v1}배 차이가 납니다. ",

    "The two rate constants differ by only a factor of {v1}. Two "
    "exponentials that close together are not distinguishable from a "
    "single one: the extra two parameters are fitting noise. Prefer the "
    "pseudo-first-order model unless the standard errors say otherwise.":
        "두 속도상수가 {v1}배밖에 차이 나지 않습니다. 이만큼 가까운 두 "
        "지수항은 하나의 지수항과 구별되지 않으며, 추가된 매개변수 두 개는 "
        "잡음을 적합하고 있는 셈입니다. 표준오차가 달리 말하지 않는 한 유사 "
        "1차 모델을 택하세요.",

    "The fast-step amplitude a₁ = {a1} mg/g exceeds the total capacity "
    "q_e = {qe} mg/g, which makes the slow step's amplitude negative: i.e. "
    "the model is describing desorption in the second stage. That is "
    "rarely intended; the two exponentials are probably not separable in "
    "these data.":
        "빠른 단계의 진폭 a₁ = {a1} mg/g이 전체 용량 q_e = {qe} mg/g을 "
        "넘어서므로 느린 단계의 진폭이 음수가 됩니다. 즉 모델이 두 번째 "
        "단계에서 탈착을 기술하고 있다는 뜻인데, 의도한 경우는 드뭅니다. 이 "
        "데이터에서는 두 지수항을 분리할 수 없을 가능성이 큽니다.",

    # ------------------------------------------------------ domain checks
    "Only {early} point(s) were measured before half the final uptake was "
    "reached. The rate constant is determined almost entirely by that "
    "early region, so with this sampling it is poorly constrained however "
    "tight the confidence interval looks. Add earlier time points.":
        "최종 흡착량의 절반에 이르기 전까지 측정된 점이 {early}개뿐입니다. "
        "속도상수는 거의 전적으로 그 초기 구간에서 결정되므로, 이런 측정 "
        "간격에서는 신뢰구간이 아무리 좁아 보여도 사실상 제대로 제약되지 "
        "않습니다. 더 이른 시간점을 추가하세요.",

    "Uptake is still climbing at your last time point: the slope over the "
    "final quarter of the run is {v2:.0f}% of the average slope, and the "
    "last third accounts for {v1:.0f}% of the total change in q_t. At "
    "equilibrium both would be near zero. Any q_e this model reports is an "
    "extrapolation beyond the measured window, and the rate constant is "
    "correlated with it, so both numbers are soft. Run the experiment "
    "longer if q_e matters.":
        "마지막 시간점에서도 흡착량이 계속 증가하고 있습니다. 실험 후반 4분의 "
        "1 구간의 기울기가 평균 기울기의 {v2:.0f}%이고, 마지막 3분의 1이 q_t "
        "전체 변화의 {v1:.0f}%를 차지합니다. 평형이라면 둘 다 0에 가까워야 "
        "합니다. 이 모델이 보고하는 q_e는 측정 구간을 넘어선 외삽이며 "
        "속도상수도 그와 상관되어 있으므로, 두 값 모두 견고하지 않습니다. "
        "q_e가 중요하다면 실험을 더 길게 수행하세요.",
}
