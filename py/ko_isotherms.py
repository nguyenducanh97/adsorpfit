# -*- coding: utf-8 -*-
"""Korean for the isotherm model interpretations and their domain warnings."""

KO_ISOTHERMS = {

    # ---------------------------------------------------------- Langmuir
    "The Langmuir monolayer capacity is q_max = {qm} mg/g. This is the "
    "loading the surface would reach if every adsorption site were "
    "occupied. It is an extrapolated ceiling rather than a measured value, "
    "so it is only trustworthy if your data actually approach a plateau.":
        "Langmuir 단분자층 흡착용량은 q_max = {qm} mg/g입니다. 모든 흡착점이 "
        "채워졌을 때 표면이 도달할 흡착량을 뜻합니다. 측정값이 아니라 외삽된 "
        "상한이므로, 데이터가 실제로 평탄역에 접근할 때만 신뢰할 수 있습니다.",

    "The Langmuir affinity constant is K_L = {kl} L/mg. Physically it is "
    "the ratio of the adsorption to the desorption rate constant, so a "
    "larger K_L means the adsorbate is held more tightly and the isotherm "
    "rises more steeply at low concentration.":
        "Langmuir 친화도 상수는 K_L = {kl} L/mg입니다. 물리적으로는 흡착 "
        "속도상수와 탈착 속도상수의 비이므로, K_L이 클수록 흡착질이 더 단단히 "
        "붙잡히고 낮은 농도에서 등온선이 더 가파르게 올라갑니다.",

    "Caution: your highest measured loading ({q_max_obs} mg/g) is only "
    "{v1:.0f}% of the fitted q_max. The plateau is far outside the "
    "measured range, so q_max here is an extrapolation with a large real "
    "uncertainty regardless of what the standard error says. Extend the "
    "concentration range before quoting this capacity.":
        "주의: 측정된 최대 흡착량({q_max_obs} mg/g)이 적합된 q_max의 "
        "{v1:.0f}%에 불과합니다. 평탄역이 측정 범위에서 한참 벗어나 있으므로, "
        "여기의 q_max는 표준오차가 무엇을 말하든 실제 불확도가 큰 외삽입니다. "
        "이 용량을 인용하기 전에 농도 범위를 넓히세요.",

    "Your data reach {v1:.0f}% of the fitted q_max, so the plateau is "
    "genuinely observed and this capacity is well constrained.":
        "데이터가 적합된 q_max의 {v1:.0f}%에 도달하므로 평탄역이 실제로 "
        "관측되었고, 이 흡착용량은 잘 결정되어 있습니다.",

    "The dimensionless separation factor R_L = 1/(1 + K_L·C_0) spans "
    "{lo}–{hi} over your initial concentrations. ":
        "무차원 분리계수 R_L = 1/(1 + K_L·C_0)은 입력한 초기 농도에서 "
        "{lo}~{hi} 범위입니다. ",

    "R_L below about 0.1 is the 'strongly favourable' regime: the isotherm "
    "is close to rectangular, which is what you want for a practical "
    "adsorbent because it strips the solute down to very low residual "
    "levels.":
        "R_L이 약 0.1 아래이면 '매우 유리한' 영역입니다. 등온선이 직사각형에 "
        "가까워지며, 용질을 매우 낮은 잔류 농도까지 제거하므로 실용 흡착제에서 "
        "바라는 형태입니다.",

    "To report the separation factor R_L, enter the initial concentrations "
    "C_0 in the experiment panel, R_L depends on C_0 and cannot be "
    "computed from the equilibrium data alone.":
        "분리계수 R_L을 보고하려면 실험 패널에 초기 농도 C_0을 입력하세요. "
        "R_L은 C_0에 의존하므로 평형 데이터만으로는 계산할 수 없습니다.",

    # -------------------------------------------------------- Freundlich
    "K_F = {kf} (mg/g)(L/mg)^(1/n) measures the adsorption capacity, but "
    "note its units depend on n: so K_F values can only be compared "
    "between systems that have similar n. It is not a capacity in mg/g.":
        "K_F = {kf} (mg/g)(L/mg)^(1/n)는 흡착 능력을 나타내지만, 단위가 n에 "
        "따라 달라진다는 점에 유의하세요. 따라서 K_F는 n이 비슷한 계끼리만 "
        "비교할 수 있으며, mg/g 단위의 흡착용량이 아닙니다.",

    "The heterogeneity exponent is n = {n} (1/n = {inv}).":
        "불균일성 지수는 n = {n}입니다(1/n = {inv}).",

    "Because 1/n = {inv} is below 1, the isotherm is favourable and "
    "concave to the concentration axis: the first molecules bind to the "
    "strongest sites, and the surface's affinity falls as those sites "
    "fill. The smaller 1/n is, the more energetically heterogeneous the "
    "surface.":
        "1/n = {inv}으로 1보다 작으므로 등온선은 유리하며 농도 축에 대해 "
        "오목합니다. 처음 분자들이 가장 강한 흡착점에 결합하고, 그 자리가 "
        "채워지면서 표면의 친화도가 떨어집니다. 1/n이 작을수록 표면이 "
        "에너지적으로 더 불균일합니다.",

    "With 1/n ≈ 1 the isotherm is effectively linear (Henry's law "
    "regime): loading is proportional to concentration, which means either "
    "the surface is homogeneous and far from saturation, or your "
    "concentration range is too low to probe site heterogeneity.":
        "1/n ≈ 1이면 등온선이 사실상 선형입니다(헨리 법칙 영역). 흡착량이 농도에 "
        "비례한다는 뜻이며, 표면이 균일하고 포화와 거리가 멀거나, 농도 범위가 "
        "너무 낮아 흡착점의 불균일성을 탐색하지 못하고 있다는 의미입니다.",

    "1/n = {inv} exceeds 1, giving an unfavourable, convex isotherm. This "
    "is the signature of cooperative adsorption, already-adsorbed "
    "molecules make further adsorption easier, as happens with surfactant "
    "hemimicelle formation or solute self-association on the surface. It "
    "is uncommon; check the data before claiming it.":
        "1/n = {inv}으로 1을 넘어 불리하고 볼록한 등온선이 됩니다. 이미 흡착된 "
        "분자가 다음 흡착을 쉽게 만드는 협동적 흡착의 특징으로, 계면활성제의 "
        "반미셀 형성이나 표면에서 용질이 서로 결합하는 경우에 나타납니다. 흔치 "
        "않으므로 주장하기 전에 데이터를 확인하세요.",

    "1/n below ~0.1 describes an almost irreversible isotherm; uptake is "
    "nearly independent of concentration over your range. Check that this "
    "is not an artefact of too narrow a concentration window.":
        "1/n이 약 0.1 아래이면 거의 비가역적인 등온선을 뜻하며, 측정 범위에서 "
        "흡착량이 농도에 거의 무관해집니다. 농도 구간이 지나치게 좁아서 생긴 "
        "인위적 결과가 아닌지 확인하세요.",

    "The Freundlich model has no plateau: it predicts loading rising "
    "without limit as Ce increases. That is physically impossible at high "
    "concentration, so never extrapolate it beyond your measured range, "
    "and do not quote a 'Freundlich capacity' as an adsorbent capacity.":
        "Freundlich 모델에는 평탄역이 없어 Ce가 커질수록 흡착량이 한없이 "
        "증가한다고 예측합니다. 높은 농도에서 물리적으로 불가능하므로 측정 "
        "범위 밖으로 절대 외삽하지 말고, 'Freundlich 용량'을 흡착제의 "
        "흡착용량으로 인용하지 마세요.",

    # ------------------------------------------------------------ Temkin
    "A_T = {at} L/g is the Temkin equilibrium binding constant, "
    "corresponding to the maximum binding energy.":
        "A_T = {at} L/g는 Temkin 평형 결합상수로, 최대 결합 에너지에 "
        "대응합니다.",

    "b_T = {bt} J/mol is the Temkin constant related to the heat of "
    "adsorption, and B = RT/b_T = {B} J/mol is the Temkin heat constant.":
        "b_T = {bt} J/mol은 흡착열과 관련된 Temkin 상수이고, "
        "B = RT/b_T = {B} J/mol은 Temkin 열상수입니다.",

    "The model's defining assumption is that the heat of adsorption of all "
    "molecules in the layer falls *linearly* with coverage, rather than "
    "logarithmically as Freundlich assumes, because of "
    "adsorbate–adsorbate repulsion. The fitted b_T = {bt} J/mol is the "
    "magnitude of that decline.":
        "이 모델의 핵심 가정은 흡착질 사이의 반발 때문에 층 안 모든 분자의 "
        "흡착열이 Freundlich처럼 로그가 아니라 피복률에 따라 *선형으로* "
        "감소한다는 것입니다. 적합된 b_T = {bt} J/mol이 그 감소의 크기입니다.",

    "b_T = {b_kj} kJ/mol is below about 8 kJ/mol, which is usually read as "
    "physisorption; the interaction is weak, of the order of van der Waals "
    "or weak electrostatic attraction.":
        "b_T = {b_kj} kJ/mol로 약 8 kJ/mol 아래이며, 보통 물리흡착으로 "
        "읽습니다. 상호작용이 약하고 반데르발스 힘이나 약한 정전기적 인력 "
        "수준입니다.",

    "b_T = {b_kj} kJ/mol falls in the 8–16 kJ/mol window often assigned to "
    "ion exchange or strong electrostatic interaction.":
        "b_T = {b_kj} kJ/mol로, 흔히 이온교환이나 강한 정전기적 상호작용으로 "
        "분류되는 8~16 kJ/mol 구간에 있습니다.",

    "b_T = {b_kj} kJ/mol exceeds ~16 kJ/mol, consistent with chemisorption "
    "involving genuine bond formation.":
        "b_T = {b_kj} kJ/mol로 약 16 kJ/mol을 넘으며, 실제 결합 형성을 수반하는 "
        "화학흡착과 부합합니다.",

    "The Temkin equation is undefined as Ce → 0 (it predicts qe → −∞), so "
    "it should only be used over the mid-coverage range and never "
    "extrapolated to dilute solution.":
        "Temkin 식은 Ce → 0에서 정의되지 않으며(qe → −∞로 예측합니다), 따라서 "
        "중간 피복률 범위에서만 사용해야 하고 묽은 용액으로 외삽해서는 "
        "안 됩니다.",

    "The Temkin equation contains ln(A_T·C_e) and is undefined at "
    "C_e = 0.":
        "Temkin 식은 ln(A_T·C_e)를 포함하므로 C_e = 0에서 정의되지 않습니다.",

    "With the fitted A_T = {at} L/g, the Temkin equation predicts a "
    "negative q_e for any C_e below 1/A_T = {c_min} mg/L. {below} of your "
    "{v1} points fall in that region, so the model is being extrapolated "
    "outside its own domain. Either drop the dilute points and refit over "
    "the mid-coverage range Temkin was derived for, or use a model that is "
    "bounded below, Langmuir, Sips or Tóth all behave correctly as "
    "C_e → 0.":
        "적합된 A_T = {at} L/g에서 Temkin 식은 C_e가 1/A_T = {c_min} mg/L보다 "
        "낮은 모든 구간에서 q_e를 음수로 예측합니다. 전체 {v1}개 점 가운데 "
        "{below}개가 그 구간에 있으므로, 모델이 자신의 적용 범위 밖으로 외삽되고 "
        "있습니다. 묽은 쪽 점들을 제외하고 Temkin이 유도된 중간 피복률 범위에서 "
        "다시 적합하거나, 아래로 유계인 모델을 사용하세요. Langmuir, Sips, Tóth는 "
        "모두 C_e → 0에서 올바르게 거동합니다.",

    "Your lowest point (C_e = {v1}) sits close to the threshold "
    "1/A_T = {c_min} below which Temkin turns negative. The fit is valid, "
    "but do not extrapolate it to lower concentrations.":
        "가장 낮은 점(C_e = {v1})이 Temkin이 음수로 바뀌는 경계 "
        "1/A_T = {c_min}에 가깝습니다. 적합 자체는 유효하지만 더 낮은 농도로 "
        "외삽하지 마세요.",

    "Your concentrations span {v1:.0f}-fold ({lo} to {hi}). Temkin is a "
    "mid-coverage approximation; it has no plateau at high C_e and "
    "diverges to −∞ as C_e → 0, so over a range this wide it is likely to "
    "misrepresent at least one end.":
        "농도 범위가 {v1:.0f}배에 걸쳐 있습니다({lo}~{hi}). Temkin은 중간 "
        "피복률 근사로, 높은 C_e에서 평탄역이 없고 C_e → 0에서 −∞로 "
        "발산합니다. 이렇게 넓은 범위에서는 적어도 한쪽 끝을 잘못 나타낼 "
        "가능성이 큽니다.",

    # --------------------------------------------- Dubinin–Radushkevich
    "q_s = {qs} mg/g is the theoretical saturation capacity, which in the "
    "Dubinin–Radushkevich picture is the capacity for filling the "
    "*micropore volume* rather than for covering a surface as a monolayer. "
    "It is normally larger than the Langmuir q_max for the same data.":
        "q_s = {qs} mg/g은 이론적 포화 용량입니다. Dubinin–Radushkevich의 "
        "관점에서는 표면을 단분자층으로 덮는 용량이 아니라 *미세세공 부피*를 "
        "채우는 용량을 뜻합니다. 같은 데이터에서 보통 Langmuir의 q_max보다 "
        "큽니다.",

    "K_ad = {kad} mol²/J² is the activity coefficient related to the mean "
    "adsorption energy.":
        "K_ad = {kad} mol²/J²는 평균 흡착 에너지와 관련된 활동도 계수입니다.",

    "The mean free energy of adsorption is E = 1/√(2·K_ad) = {E} kJ/mol. "
    "This is the energy released when one mole of adsorbate is transferred "
    "to the surface from infinity in solution, and it is the parameter "
    "this model exists to deliver.":
        "평균 흡착 자유에너지는 E = 1/√(2·K_ad) = {E} kJ/mol입니다. 용액 속 "
        "무한히 먼 곳에서 표면으로 흡착질 1몰이 옮겨질 때 방출되는 "
        "에너지이며, 이 모델이 제공하고자 하는 바로 그 매개변수입니다.",

    "E = {E} kJ/mol is below 8 kJ/mol, which indicates **physisorption**, "
    "the adsorbate is held by van der Waals forces, hydrogen bonding or "
    "weak electrostatics. Such adsorption is typically fast, fully "
    "reversible, and the adsorbent should regenerate easily.":
        "E = {E} kJ/mol로 8 kJ/mol 아래이며, 이는 **물리흡착**을 뜻합니다. "
        "흡착질이 반데르발스 힘, 수소결합, 약한 정전기적 상호작용으로 붙잡혀 "
        "있습니다. 이런 흡착은 대개 빠르고 완전히 가역적이며, 흡착제도 쉽게 "
        "재생됩니다.",

    "E = {E} kJ/mol lies in the 8–16 kJ/mol band, the classical signature "
    "of **ion exchange**: the adsorbate displaces a counter-ion from the "
    "surface rather than forming a covalent bond.":
        "E = {E} kJ/mol로 8~16 kJ/mol 구간에 있으며, 이는 **이온교환**의 고전적 "
        "특징입니다. 흡착질이 공유결합을 만드는 대신 표면의 짝이온을 "
        "밀어냅니다.",

    "E = {E} kJ/mol is above 16 kJ/mol, pointing to **chemisorption**, "
    "genuine chemical bond formation between adsorbate and surface. Expect "
    "slow kinetics, poor reversibility and difficult regeneration.":
        "E = {E} kJ/mol로 16 kJ/mol을 넘으며, 이는 **화학흡착**, 곧 흡착질과 "
        "표면 사이의 실제 화학결합 형성을 가리킵니다. 속도가 느리고 가역성이 "
        "떨어지며 재생이 어려울 것으로 예상됩니다.",

    "Treat these energy bands as rough guidance, not proof of mechanism. "
    "They were derived for specific systems and are quoted far more "
    "confidently in the literature than the underlying evidence supports.":
        "이 에너지 구간은 메커니즘의 증명이 아니라 대략적인 지침으로 "
        "보십시오. 특정 계에서 유도된 것인데도 문헌에서는 근거가 뒷받침하는 "
        "것보다 훨씬 단정적으로 인용됩니다.",

    "E could not be computed because K_ad is not positive.":
        "K_ad가 양수가 아니어서 E를 계산할 수 없습니다.",

    "One caveat that most papers skip: the Polanyi potential used here, "
    "ε = RT·ln(1 + 1/Ce), requires Ce in mol/L for E to come out in "
    "J/mol. AdsorpFit converts for you when you supply the molar mass; if "
    "you did not, the E value above inherits the units of your Ce and is "
    "not comparable with published values.":
        "대부분의 논문이 건너뛰는 주의점이 하나 있습니다. 여기서 쓰는 폴라니 "
        "퍼텐셜 ε = RT·ln(1 + 1/Ce)에서 E가 J/mol로 나오려면 Ce가 mol/L여야 "
        "합니다. 몰질량을 입력하면 AdsorpFit이 변환해 주지만, 입력하지 않았다면 "
        "위의 E 값은 입력한 Ce의 단위를 그대로 물려받아 발표된 값과 비교할 수 "
        "없습니다.",

    "The Polanyi potential ε = RT·ln(1 + 1/C_e) requires C_e in mol/L for "
    "the mean free energy E to come out in J/mol. Enter the adsorbate "
    "molar mass and AdsorpFit will convert; without it, E carries the "
    "units of your C_e and is not comparable with published values.":
        "폴라니 퍼텐셜 ε = RT·ln(1 + 1/C_e)에서 평균 자유에너지 E가 J/mol로 "
        "나오려면 C_e가 mol/L여야 합니다. 흡착질의 몰질량을 입력하면 "
        "변환됩니다. 입력하지 않으면 E는 입력한 C_e의 단위를 그대로 지니며 "
        "발표된 값과 비교할 수 없습니다.",

    # ------------------------------------------------------------- Sips
    "q_max = {qm} mg/g is the saturation capacity. Because Sips has a real "
    "plateau (unlike Freundlich), this capacity is physically meaningful.":
        "q_max = {qm} mg/g은 포화 흡착용량입니다. Sips는 Freundlich와 달리 실제 "
        "평탄역을 가지므로 이 용량은 물리적으로 의미가 있습니다.",

    "K_s = {ks} (L/mg)^m is the affinity constant and m_s = {ms} is the "
    "heterogeneity index.":
        "K_s = {ks} (L/mg)^m는 친화도 상수이고, m_s = {ms}는 불균일성 "
        "지수입니다.",

    "Sips (Langmuir–Freundlich) is a hybrid: it behaves like Freundlich at "
    "low concentration and like Langmuir at high concentration, which "
    "fixes Freundlich's unbounded growth while keeping its ability to "
    "describe a heterogeneous surface.":
        "Sips(Langmuir–Freundlich)는 혼합형입니다. 낮은 농도에서는 "
        "Freundlich처럼, 높은 농도에서는 Langmuir처럼 거동하여, 불균일 표면을 "
        "설명하는 능력은 유지하면서 Freundlich의 무한 증가 문제를 "
        "해결합니다.",

    "m_s = {ms} is essentially 1, at which point Sips reduces exactly to "
    "the Langmuir equation. The surface is behaving as energetically "
    "homogeneous, and the third parameter is buying you nothing; prefer "
    "Langmuir on parsimony grounds.":
        "m_s = {ms}으로 사실상 1이며, 이때 Sips는 Langmuir 식과 정확히 "
        "같아집니다. 표면이 에너지적으로 균일하게 거동하고 있어 세 번째 "
        "매개변수가 아무 이득을 주지 못하므로, 간결성 측면에서 Langmuir를 "
        "택하세요.",

    "m_s = {ms} < 1 indicates a heterogeneous surface. The further m_s "
    "falls below 1, the broader the distribution of site energies. This is "
    "the usual result for activated carbons, biochars and most natural "
    "adsorbents.":
        "m_s = {ms} < 1은 불균일한 표면을 뜻합니다. m_s가 1보다 작을수록 흡착점 "
        "에너지의 분포가 넓습니다. 활성탄, 바이오차를 비롯한 대부분의 천연 "
        "흡착제에서 흔한 결과입니다.",

    "m_s = {ms} > 1 implies positive cooperativity between adsorbed "
    "molecules. It is unusual: confirm it is not an artefact of a sparse "
    "high-concentration region.":
        "m_s = {ms} > 1은 흡착된 분자 사이의 양의 협동성을 뜻합니다. 흔치 "
        "않으므로, 높은 농도 구간의 점이 성겨서 생긴 인위적 결과가 아닌지 "
        "확인하세요.",

    # ------------------------------------------------------------- Tóth
    "q_max = {qm} mg/g, K_T = {KT} L/mg, n_T = {nt}.":
        "q_max = {qm} mg/g, K_T = {KT} L/mg, n_T = {nt}입니다.",

    "Tóth was designed to fix Langmuir's poor behaviour at both ends of "
    "the concentration range simultaneously. It satisfies the Henry's law "
    "limit as Ce → 0 and saturates correctly at high Ce, which is why it "
    "usually outperforms Langmuir on wide-range data.":
        "Tóth는 농도 범위의 양쪽 끝에서 Langmuir가 보이는 부정확한 거동을 동시에 "
        "바로잡기 위해 고안되었습니다. Ce → 0에서 헨리 법칙 극한을 만족하고 "
        "높은 Ce에서 올바르게 포화하므로, 넓은 범위의 데이터에서 보통 "
        "Langmuir보다 낫습니다.",

    "n_T = {nt} ≈ 1 collapses Tóth to Langmuir. The surface is behaving "
    "homogeneously; the extra parameter is not earning its place.":
        "n_T = {nt} ≈ 1이면 Tóth는 Langmuir로 환원됩니다. 표면이 균일하게 "
        "거동하고 있어 추가 매개변수가 제 몫을 하지 못합니다.",

    "n_T = {nt} departs from 1, and the size of that departure is the "
    "model's measure of surface heterogeneity, the further from 1, the "
    "more asymmetric the underlying distribution of site energies.":
        "n_T = {nt}은 1에서 벗어나 있으며, 그 벗어난 정도가 이 모델이 말하는 "
        "표면 불균일성의 척도입니다. 1에서 멀수록 흡착점 에너지 분포가 더 "
        "비대칭입니다.",

    # ------------------------------------------------- Redlich–Peterson
    "K_RP = {krp} L/g, a_RP = {arp} (L/mg)^g, g = {g}.":
        "K_RP = {krp} L/g, a_RP = {arp} (L/mg)^g, g = {g}입니다.",

    "Redlich–Peterson is a three-parameter compromise that combines "
    "features of Langmuir and Freundlich; the numerator is Langmuir-like "
    "and the denominator's exponent g controls how the model interpolates "
    "between them.":
        "Redlich–Peterson은 Langmuir와 Freundlich의 특징을 결합한 3-매개변수 "
        "절충안입니다. 분자는 Langmuir에 가깝고, 분모의 지수 g가 둘 사이를 "
        "어떻게 보간할지 결정합니다.",

    "g = {g} ≈ 1 reduces Redlich–Peterson exactly to the Langmuir "
    "equation, with q_max = K_RP/a_RP = {v1} mg/g and K_L = a_RP = "
    "{arp} L/mg. Report Langmuir instead: it gives the same fit with one "
    "fewer parameter.":
        "g = {g} ≈ 1이면 Redlich–Peterson은 Langmuir 식과 정확히 같아지며, "
        "q_max = K_RP/a_RP = {v1} mg/g, K_L = a_RP = {arp} L/mg입니다. 대신 "
        "Langmuir를 보고하세요. 매개변수 하나가 적으면서 같은 적합을 줍니다.",

    "g = {g} is close to 0, where the model approaches Henry's law (linear "
    "partitioning). Your data are probably confined to the dilute, "
    "pre-saturation region.":
        "g = {g}으로 0에 가까우며, 이 영역에서 모델은 헨리 법칙(선형 분배)에 "
        "접근합니다. 데이터가 묽고 포화 이전인 구간에 한정되어 있을 "
        "가능성이 큽니다.",

    "g = {g} lies between 0 and 1, so the isotherm is genuinely "
    "intermediate between Langmuir and Freundlich behaviour, neither "
    "two-parameter model alone would capture it.":
        "g = {g}으로 0과 1 사이이므로, 등온선이 실제로 Langmuir와 Freundlich "
        "거동의 중간에 있습니다. 2-매개변수 모델 어느 하나만으로는 이를 담아낼 "
        "수 없습니다.",

    "Note that Redlich–Peterson has no plateau unless g = 1, so K_RP is "
    "not a capacity. Papers that quote K_RP in mg/g as an adsorption "
    "capacity are making a unit error.":
        "g = 1이 아닌 한 Redlich–Peterson에는 평탄역이 없으므로 K_RP는 "
        "흡착용량이 아닙니다. K_RP를 mg/g 단위의 흡착용량으로 인용하는 논문은 "
        "단위를 잘못 쓰고 있는 것입니다.",

    # ------------------------------------------------------------- Hill
    "q_SH = {qsh} mg/g is the Hill saturation capacity and K_D = {KD} is "
    "the Hill dissociation constant.":
        "q_SH = {qsh} mg/g은 Hill 포화 흡착용량이고, K_D = {KD}는 Hill 해리 "
        "상수입니다.",

    "The Hill coefficient is n_H = {nh}. This is the model's whole point: "
    "it quantifies cooperativity between binding sites, an idea imported "
    "from ligand binding to macromolecules.":
        "Hill 계수는 n_H = {nh}입니다. 이 모델의 핵심으로, 거대분자에 대한 "
        "리간드 결합에서 가져온 개념인 결합점 사이의 협동성을 정량합니다.",

    "n_H ≈ 1 means **non-cooperative** binding, sites act independently, "
    "and Hill reduces to the Langmuir form.":
        "n_H ≈ 1은 **비협동적** 결합을 뜻합니다. 흡착점이 서로 독립적으로 "
        "작용하며, Hill은 Langmuir 형태로 환원됩니다.",

    "n_H = {nh} > 1 means **positive cooperativity**: binding of the first "
    "molecules increases the affinity of the remaining sites. The isotherm "
    "is sigmoidal rather than concave.":
        "n_H = {nh} > 1은 **양의 협동성**을 뜻합니다. 처음 분자들이 결합하면 "
        "남은 흡착점의 친화도가 높아집니다. 등온선은 오목한 형태가 아니라 "
        "S자형이 됩니다.",

    "n_H = {nh} < 1 means **negative cooperativity**: each bound molecule "
    "makes subsequent binding harder, which is the behaviour expected on a "
    "heterogeneous surface where the best sites fill first.":
        "n_H = {nh} < 1은 **음의 협동성**을 뜻합니다. 분자가 하나씩 결합할 "
        "때마다 다음 결합이 어려워지며, 가장 좋은 흡착점부터 채워지는 불균일 "
        "표면에서 예상되는 거동입니다.",

    # -------------------------------------------------------------- BET
    "Monolayer capacity q_s = {qs} mg/g; BET constant C_BET = {cb}.":
        "단분자층 용량 q_s = {qs} mg/g, BET 상수 C_BET = {cb}입니다.",

    "C_BET is the ratio of the first-layer binding constant to the "
    "condensation constant of the higher layers. ":
        "C_BET는 첫 번째 층의 결합상수와 그 위 층들의 응축상수의 비입니다. ",

    "The liquid-phase BET model needs the adsorbate's saturation "
    "concentration C_s (its solubility limit). Without it a placeholder is "
    "used and neither q_s nor C_BET means anything. Enter C_s in the "
    "experiment panel.":
        "액상 BET 모델에는 흡착질의 포화 농도 C_s(용해도 한계)가 필요합니다. "
        "없으면 임시값이 사용되어 q_s와 C_BET 모두 의미가 없습니다. 실험 패널에 "
        "C_s를 입력하세요.",

    "Your highest C_e ({hi} mg/L) is at or above the saturation "
    "concentration C_s = {cs} mg/L. BET contains (C_s − C_e) in its "
    "denominator and diverges there; the solution would be supersaturated, "
    "which is outside the model's physical premise.":
        "가장 높은 C_e({hi} mg/L)가 포화 농도 C_s = {cs} mg/L와 같거나 그보다 "
        "큽니다. BET는 분모에 (C_s − C_e)를 포함하므로 그 지점에서 발산합니다. "
        "용액이 과포화 상태라는 뜻이며, 이는 모델의 물리적 전제를 "
        "벗어납니다.",

    "Your data reach only {v1:.1f}% of the saturation concentration. BET "
    "describes multilayer build-up, which only becomes significant as C_e "
    "approaches C_s, so there is little multilayer behaviour here for the "
    "model to detect.":
        "데이터가 포화 농도의 {v1:.1f}%에만 도달합니다. BET는 다층 형성을 "
        "설명하는데, 이는 C_e가 C_s에 가까워질 때에만 뚜렷해지므로 여기서는 "
        "모델이 감지할 다층 거동이 거의 없습니다.",

    # --------------------------------------------------- other isotherms
    "q_max = {qm} mg/g and K_J = {KJ} L/mg.":
        "q_max = {qm} mg/g, K_J = {KJ} L/mg입니다.",

    "K_H = {KH}, n_H = {nH}.":
        "K_H = {KH}, n_H = {nH}입니다.",

    "A = {A}, B = {B}.":
        "A = {A}, B = {B}입니다.",

    "The Harkins–Jura equation contains 1/(B − log C_e) and is undefined "
    "once C_e reaches 10^B = {c_max} mg/L. {above} of your {v1} points are "
    "at or beyond that, where the model has no value to return. Those "
    "points cannot constrain the fit, so the reported statistics describe "
    "only the remaining ones.":
        "Harkins–Jura 식은 1/(B − log C_e)를 포함하므로 C_e가 "
        "10^B = {c_max} mg/L에 이르면 정의되지 않습니다. 전체 {v1}개 점 가운데 "
        "{above}개가 그 지점 이상에 있어 모델이 반환할 값이 없습니다. 이 점들은 "
        "적합을 제약할 수 없으므로, 보고된 통계는 나머지 점들만을 설명합니다.",

    "q_m = {qm} mg/g, K_E = {KE} L/mg.":
        "q_m = {qm} mg/g, K_E = {KE} L/mg입니다.",

    "q_max = {qm} mg/g, b_K = {bK} L/mg, a_K = {ak}.":
        "q_max = {qm} mg/g, b_K = {bK} L/mg, a_K = {ak}입니다.",

    "a_K = {ak} departs from 1, so the isotherm is Freundlich-like at the "
    "high-concentration end. Khan was formulated for multicomponent "
    "systems, so a strong Khan fit is sometimes taken as a hint that more "
    "than one solute species is competing for sites.":
        "a_K = {ak}이 1에서 벗어나므로 높은 농도 쪽에서 등온선이 Freundlich에 "
        "가깝습니다. Khan은 다성분계를 위해 만들어졌으므로, Khan이 잘 맞으면 "
        "둘 이상의 용질이 흡착점을 두고 경쟁한다는 단서로 보기도 합니다.",

    "q_max = {qm} mg/g, K_RP = {KRP} L/mg, m_RP = {mrp}.":
        "q_max = {qm} mg/g, K_RP = {KRP} L/mg, m_RP = {mrp}입니다.",

    "q_max = {qm} mg/g, K = {K} L/mg, m = {m}, n = {n}.":
        "q_max = {qm} mg/g, K = {K} L/mg, m = {m}, n = {n}입니다.",

    "Koble and Corrigan noted that n must be at least 1 for the model to "
    "be thermodynamically consistent. The fit gives n = {n}, below that "
    "limit, which means another model describes these data better.":
        "Koble과 Corrigan은 이 모델이 열역학적으로 정합하려면 n이 최소 1 이상이어야 "
        "한다고 밝혔습니다. 적합 결과 n = {n}으로 그 한계보다 작으므로, 다른 "
        "모델이 이 데이터를 더 잘 설명한다는 뜻입니다.",

    "q_max = {qm} mg/g, K_BS = {KBS}, α = {alpha}.":
        "q_max = {qm} mg/g, K_BS = {KBS}, α = {alpha}입니다.",

    "α is the fractal exponent describing the width of the site-energy "
    "distribution. ":
        "α는 흡착점 에너지 분포의 폭을 나타내는 프랙탈 지수입니다. ",

    "α = {alpha} indicates a broad distribution of site energies; the "
    "further α is from 1, the more heterogeneous the surface.":
        "α = {alpha}은 흡착점 에너지 분포가 넓음을 뜻합니다. α가 1에서 "
        "멀수록 표면이 더 불균일합니다.",

    "Henry constant k_VS = {kVS} L/g; Langmuir part q_max = {qm} mg/g, "
    "b = {b} L/mg.":
        "헨리 상수 k_VS = {kVS} L/g, Langmuir 항 q_max = {qm} mg/g, "
        "b = {b} L/mg입니다.",

    "A = {A}, B = {B}, n = {n}. The implied saturation capacity is "
    "A/B = {v1} mg/g.":
        "A = {A}, B = {B}, n = {n}입니다. 이로부터 얻어지는 포화 용량은 "
        "A/B = {v1} mg/g입니다.",

    "q_max = {qm} mg/g, b_0 = {b0} L/mg, x = {x}, y = {y}.":
        "q_max = {qm} mg/g, b_0 = {b0} L/mg, x = {x}, y = {y}입니다.",

    "The Baudu model requires both 1+x+y and 1+x to lie strictly between 0 "
    "and 1. The fit gives 1+x+y = {a} and 1+x = {b}, so these parameters "
    "are outside the model's stated domain of applicability and should not "
    "be reported.":
        "Baudu 모델은 1+x+y와 1+x가 모두 0과 1 사이에 엄격히 있어야 합니다. "
        "적합 결과는 1+x+y = {a}, 1+x = {b}이므로, 이 매개변수들은 모델이 "
        "명시한 적용 범위 밖에 있어 보고해서는 안 됩니다.",

    "Validity check passed: 1 + x + y = {v2} and 1 + x = {v1} both lie in "
    "(0, 1), as the model requires.":
        "타당성 검사 통과: 1 + x + y = {v2}와 1 + x = {v1}이 모두 모델이 "
        "요구하는 대로 (0, 1) 안에 있습니다.",

    "A = {A}, B = {B}, α = {alpha}, β = {beta}.":
        "A = {A}, B = {B}, α = {alpha}, β = {beta}입니다.",

    "m ≠ n, so the site-energy distribution is asymmetric: ":
        "m ≠ n이므로 흡착점 에너지 분포가 비대칭입니다: ",

    "The {name} equation is logarithmic in C_e and is undefined at "
    "C_e = 0.":
        "{name} 식은 C_e에 대해 로그 형태이므로 C_e = 0에서 정의되지 "
        "않습니다.",

    "Your isotherm is still rising at the highest concentration: the slope "
    "over the final quarter of the range is {v2:.0f}% of the average "
    "slope, and the top third of the data accounts for {v1:.0f}% of the "
    "total change in q_e. At saturation both would be near zero. A "
    "capacity fitted to data that never plateau is an extrapolation rather "
    "than a measurement, so extend the concentration range if q_max is the "
    "number you want to report.":
        "가장 높은 농도에서도 등온선이 계속 상승하고 있습니다. 범위 후반 "
        "4분의 1 구간의 기울기가 평균 기울기의 {v2:.0f}%이고, 상위 3분의 1이 "
        "q_e 전체 변화의 {v1:.0f}%를 차지합니다. 포화 상태라면 둘 다 0에 "
        "가까워야 합니다. 평탄역에 이르지 못한 데이터로 적합한 흡착용량은 "
        "측정이 아니라 외삽이므로, q_max를 보고하려면 농도 범위를 넓히세요.",
}
