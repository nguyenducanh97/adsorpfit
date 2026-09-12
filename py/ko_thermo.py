# -*- coding: utf-8 -*-
"""Korean for the van 't Hoff analysis, the activation energy and the
sticking probability.
"""

KO_THERMO = {

    # ------------------------------------------------- K° conversion
    "Equilibrium constant route: {v1}. {detail}. This choice is not "
    "cosmetic: a different route gives a different ΔG°, so it must be "
    "stated explicitly in any paper reporting these numbers.":
        "평형상수 변환 경로: {v1}. {detail}. 이 선택은 형식적인 문제가 "
        "아닙니다. 경로가 달라지면 ΔG°도 달라지므로, 이 값을 보고하는 논문에는 "
        "반드시 명시해야 합니다.",

    "K_L = {kl} L/mg × {mw} g/mol × 1000 mg/g = {kl_molar} L/mol; "
    "× 55.5 mol/L → K° = {k0}":
        "K_L = {kl} L/mg × {mw} g/mol × 1000 mg/g = {kl_molar} L/mol, "
        "× 55.5 mol/L → K° = {k0}",

    "K_D = {kd} L/g × 1000 g/L → K° = {k0}":
        "K_D = {kd} L/g × 1000 g/L → K° = {k0}",

    "K_C = {k0} (dimensionless by construction)":
        "K_C = {k0}(정의상 무차원)",

    "K_RP = {krp} L/g × 1000 g/L → K° = {k0}":
        "K_RP = {krp} L/g × 1000 g/L → K° = {k0}",

    "K_F = {k0} used directly (dimensionally invalid)":
        "K_F = {k0}을 그대로 사용(차원상 타당하지 않음)",

    "K° is not positive, so ln K° is undefined and no thermodynamic "
    "parameters can be computed.":
        "K°가 양수가 아니므로 ln K°가 정의되지 않고, 열역학 매개변수를 계산할 "
        "수 없습니다.",

    "K° = {k0} is less than 1, so ln K° is negative and ΔG° will come out "
    "positive: i.e. the analysis says adsorption is non-spontaneous under "
    "standard-state conditions. That is a legitimate result, but if your "
    "adsorbent clearly works, it usually means the K° conversion is wrong "
    "rather than the thermodynamics.":
        "K° = {k0}으로 1보다 작으므로 ln K°가 음수가 되고 ΔG°는 양수로 "
        "나옵니다. 즉 표준상태에서 흡착이 비자발적이라는 해석이 됩니다. 그 "
        "자체로 가능한 결과이지만, 흡착제가 분명히 작동한다면 보통은 열역학이 "
        "아니라 K° 변환이 잘못된 것입니다.",

    # -------------------------------------------------- van 't Hoff fit
    "Only two temperatures were supplied. A two-point van't Hoff line has "
    "zero residual degrees of freedom: ΔH° and ΔS° can be computed but "
    "have no uncertainty estimate and R² is meaningless (it is always 1). "
    "Three temperatures is the practical minimum; four or five is better.":
        "온도가 두 개만 입력되었습니다. 두 점으로 그린 van 't Hoff 직선은 잔차 "
        "자유도가 0입니다. ΔH°와 ΔS°를 계산할 수는 있지만 불확도를 추정할 수 "
        "없고 R²은 의미가 없습니다(항상 1입니다). 실질적인 최소는 온도 세 "
        "개이며, 네다섯 개면 더 좋습니다.",

    "The van't Hoff regression has R² = {R2:.4f}. Below about 0.95 the "
    "extracted ΔH° and ΔS° are not reliable; check for an outlying "
    "temperature or a K° conversion that varies with temperature in a way "
    "the model does not capture.":
        "van 't Hoff 회귀의 R²은 {R2:.4f}입니다. 약 0.95 아래에서는 얻어진 "
        "ΔH°와 ΔS°를 신뢰할 수 없습니다. 벗어난 온도점이 있는지, 또는 K° "
        "변환이 모델이 포착하지 못하는 방식으로 온도에 따라 변하는지 "
        "확인하세요.",

    "ΔH° and ΔS° are reported at the reference temperature {T_ref} K. A "
    "non-zero ΔCp means the van't Hoff plot is genuinely curved and ΔH° "
    "changes with temperature.":
        "ΔH°와 ΔS°는 기준 온도 {T_ref} K에서 보고됩니다. ΔCp가 0이 아니라는 "
        "것은 van 't Hoff 그래프가 실제로 휘어 있고 ΔH°가 온도에 따라 변한다는 "
        "뜻입니다.",

    "ΔG° computed directly from each K° and ΔG° computed from ΔH° − TΔS° "
    "differ by up to {gap:.2f} kJ/mol. That gap means the van't Hoff plot "
    "is curved: ΔH° is not constant across your temperature range, so a "
    "single ΔH° value misrepresents the system. Consider the non-linear "
    "van't Hoff form with a heat-capacity term, or report ΔH° as a range.":
        "각 K°에서 직접 구한 ΔG°와 ΔH° − TΔS°로 구한 ΔG°가 최대 "
        "{gap:.2f} kJ/mol 차이 납니다. 이 차이는 van 't Hoff 그래프가 휘어 "
        "있다는 뜻입니다. 온도 범위 전체에서 ΔH°가 일정하지 않으므로 하나의 "
        "ΔH° 값은 이 계를 잘못 나타냅니다. 열용량 항을 포함한 비선형 "
        "van 't Hoff 형태를 고려하거나, ΔH°를 범위로 보고하세요.",

    # ------------------------------------------------------------- ΔG°
    "ΔG° is negative at every temperature ({v5} to {v4} kJ/mol from "
    "{v3:.0f} to {v2:.0f} K), so adsorption is **spontaneous** and "
    "thermodynamically favourable across your whole range. ΔG° becomes "
    "{trend} as temperature rises, meaning the driving force {v1} with "
    "heating.":
        "모든 온도에서 ΔG°가 음수입니다({v3:.0f}~{v2:.0f} K에서 "
        "{v5}~{v4} kJ/mol). 따라서 측정한 범위 전체에서 흡착이 **자발적**이며 "
        "열역학적으로 유리합니다. 온도가 오르면 ΔG°가 {trend} 되며, 이는 가열에 "
        "따라 추진력이 {v1}는 뜻입니다.",

    "ΔG° is not negative at all temperatures ({v2} to {v1} kJ/mol). A "
    "positive ΔG° means adsorption is non-spontaneous under standard-state "
    "conditions at that temperature. Before reporting this, check the K° "
    "conversion, because a positive ΔG° for an adsorbent that demonstrably "
    "removes the solute almost always signals a units problem rather than "
    "real thermodynamics.":
        "모든 온도에서 ΔG°가 음수인 것은 아닙니다({v2}~{v1} kJ/mol). ΔG°가 "
        "양수라는 것은 그 온도의 표준상태에서 흡착이 비자발적이라는 뜻입니다. "
        "이를 보고하기 전에 K° 변환을 확인하세요. 용질을 실제로 제거하는 "
        "흡착제에서 ΔG°가 양수로 나오는 것은 거의 언제나 진짜 열역학이 아니라 "
        "단위 문제의 신호입니다.",

    "The magnitude of ΔG° (mean |ΔG°| ≈ {mag} kJ/mol) lies in the "
    "0–20 kJ/mol range conventionally assigned to **physisorption**, where "
    "the adsorbate is held by van der Waals forces, hydrogen bonding or "
    "weak electrostatics.":
        "ΔG°의 크기(평균 |ΔG°| ≈ {mag} kJ/mol)는 관례적으로 **물리흡착**으로 "
        "분류되는 0~20 kJ/mol 범위에 있습니다. 이 경우 흡착질은 반데르발스 힘, "
        "수소결합, 약한 정전기적 상호작용으로 붙잡혀 있습니다.",

    "The magnitude of ΔG° (mean |ΔG°| ≈ {mag} kJ/mol) falls in the "
    "20–80 kJ/mol range usually taken to indicate a contribution from "
    "**chemisorption** alongside physical interactions.":
        "ΔG°의 크기(평균 |ΔG°| ≈ {mag} kJ/mol)는 물리적 상호작용과 함께 "
        "**화학흡착**의 기여가 있다고 보는 20~80 kJ/mol 범위에 있습니다.",

    "Mean |ΔG°| ≈ {mag} kJ/mol exceeds 80 kJ/mol, which would imply strong "
    "chemisorption. Values this large are unusual in aqueous adsorption "
    "and are worth re-checking against the K° conversion.":
        "평균 |ΔG°| ≈ {mag} kJ/mol로 80 kJ/mol을 넘으며, 이는 강한 화학흡착을 "
        "뜻하게 됩니다. 수용액 흡착에서 이렇게 큰 값은 드물므로 K° 변환을 다시 "
        "확인해 볼 필요가 있습니다.",

    # ------------------------------------------------------------- ΔH°
    "ΔH° = {dH} kJ/mol is **negative**, so adsorption is **exothermic**: "
    "heat is released on binding, and uptake falls as temperature rises. "
    "Practically, this means running the process cold gives higher "
    "capacity, and it makes thermal regeneration of the adsorbent "
    "straightforward.":
        "ΔH° = {dH} kJ/mol로 **음수**이므로 흡착은 **발열**입니다. 결합할 때 "
        "열이 방출되고, 온도가 오르면 흡착량이 줄어듭니다. 실무적으로는 낮은 "
        "온도에서 운전할수록 용량이 커지며, 열을 이용한 흡착제 재생이 "
        "수월해집니다.",

    "ΔH° = {dH} kJ/mol is **positive**, so adsorption is **endothermic**: "
    "the system absorbs heat, and uptake improves as temperature rises. "
    "This normally means the energy required to dehydrate the adsorbate "
    "(strip its solvation shell) before it can reach the surface exceeds "
    "the energy released on binding.":
        "ΔH° = {dH} kJ/mol로 **양수**이므로 흡착은 **흡열**입니다. 계가 열을 "
        "흡수하며, 온도가 오르면 흡착량이 늘어납니다. 보통 이는 흡착질이 "
        "표면에 닿기 전에 수화껍질을 벗는 데 드는 에너지가 결합으로 방출되는 "
        "에너지보다 크다는 뜻입니다.",

    "|ΔH°| = {amag} kJ/mol is below ~20 kJ/mol, consistent with "
    "**physisorption** (the enthalpy of physical adsorption is typically "
    "2–40 kJ/mol, similar to a condensation enthalpy).":
        "|ΔH°| = {amag} kJ/mol로 약 20 kJ/mol 아래이며, **물리흡착**과 "
        "부합합니다(물리흡착 엔탈피는 보통 2~40 kJ/mol로 응축 엔탈피와 "
        "비슷합니다).",

    "|ΔH°| = {amag} kJ/mol sits in the 20–40 kJ/mol transition zone, where "
    "physical and chemical contributions are both plausible. Do not claim "
    "a mechanism from this number alone, support it with the D–R mean free "
    "energy E, spectroscopic evidence, or a reversibility test.":
        "|ΔH°| = {amag} kJ/mol로 물리적 기여와 화학적 기여가 모두 가능한 "
        "20~40 kJ/mol 전이 영역에 있습니다. 이 수치만으로 메커니즘을 주장하지 "
        "말고, D–R 평균 자유에너지 E, 분광학적 증거, 가역성 시험으로 "
        "뒷받침하세요.",

    "|ΔH°| = {amag} kJ/mol exceeds 40 kJ/mol, which points to "
    "**chemisorption**: bond formation rather than physical attraction. "
    "Expect the process to be slow to reverse and the adsorbent hard to "
    "regenerate without harsh conditions.":
        "|ΔH°| = {amag} kJ/mol로 40 kJ/mol을 넘으며, 이는 물리적 인력이 아니라 "
        "결합 형성, 곧 **화학흡착**을 가리킵니다. 되돌리기 어렵고, 가혹한 "
        "조건 없이는 흡착제를 재생하기 힘들 것으로 예상됩니다.",

    # ------------------------------------------------------------- ΔS°
    "ΔS° = {dS} J mol⁻¹ K⁻¹ is **positive**, indicating increased "
    "randomness at the solid–liquid interface. This is the usual result in "
    "aqueous systems and is counter-intuitive at first, because fixing a "
    "molecule onto a surface should *lower* entropy. The resolution is "
    "that the adsorbate and the surface are both hydrated: binding "
    "releases several ordered water molecules per adsorbate molecule into "
    "the bulk, and that gain outweighs the entropy lost by the adsorbate "
    "itself. A positive ΔS° is therefore evidence of a desolvation-driven "
    "process.":
        "ΔS° = {dS} J mol⁻¹ K⁻¹로 **양수**이며, 고체–액체 계면에서 무질서도가 "
        "증가함을 뜻합니다. 수용액계에서 흔한 결과이지만 처음에는 직관에 "
        "어긋나 보입니다. 분자를 표면에 고정하면 엔트로피가 *낮아져야* 하기 "
        "때문입니다. 해답은 흡착질과 표면이 모두 수화되어 있다는 데 있습니다. "
        "결합이 일어나면 흡착질 분자 하나당 정렬된 물 분자 여러 개가 "
        "벌크로 풀려나며, 그 이득이 흡착질 자신이 잃는 엔트로피를 "
        "넘어섭니다. 따라서 양의 ΔS°는 탈수화가 이끄는 과정이라는 "
        "증거입니다.",

    "ΔS° = {dS} J mol⁻¹ K⁻¹ is **negative**, indicating decreased "
    "randomness at the interface: the adsorbate loses translational and "
    "rotational freedom on binding, and that loss is not offset by "
    "released solvation water. This is typical of adsorption onto a "
    "well-ordered surface, or of large molecules that adopt a fixed "
    "orientation on binding.":
        "ΔS° = {dS} J mol⁻¹ K⁻¹로 **음수**이며, 계면에서 무질서도가 감소함을 "
        "뜻합니다. 흡착질이 결합하면서 병진 및 회전 자유도를 잃고, 그 손실이 "
        "풀려난 수화수로 상쇄되지 않는 경우입니다. 잘 정렬된 표면에 흡착하거나, "
        "큰 분자가 결합하면서 고정된 배향을 취할 때 전형적으로 나타납니다.",

    # ------------------------------------------------- driving force split
    "Decomposing the driving force at {Tm:.0f} K: the enthalpy term "
    "contributes {enth} kJ/mol and the entropy term (−TΔS°) contributes "
    "{entr} kJ/mol. The process is **enthalpy-driven**, so the strength of "
    "the adsorbate–surface interaction, not the entropy gain, is what "
    "makes it favourable.":
        "{Tm:.0f} K에서 추진력을 나누어 보면 엔탈피 항이 {enth} kJ/mol, "
        "엔트로피 항(−TΔS°)이 {entr} kJ/mol 기여합니다. 이 과정은 **엔탈피가 "
        "이끄는** 경우로, 흡착을 유리하게 만드는 것은 엔트로피 이득이 아니라 "
        "흡착질과 표면 사이 상호작용의 세기입니다.",

    "Decomposing the driving force at {Tm:.0f} K: the enthalpy term "
    "contributes {enth} kJ/mol and the entropy term (−TΔS°) contributes "
    "{entr} kJ/mol. The process is **entropy-driven**, so it proceeds "
    "because of the disorder gained (largely released solvation water), "
    "not because binding is energetically strong. This is the common "
    "situation for endothermic adsorption, where a positive ΔH° is "
    "overcome by a larger positive ΔS°.":
        "{Tm:.0f} K에서 추진력을 나누어 보면 엔탈피 항이 {enth} kJ/mol, "
        "엔트로피 항(−TΔS°)이 {entr} kJ/mol 기여합니다. 이 과정은 **엔트로피가 "
        "이끄는** 경우로, 결합이 에너지적으로 강해서가 아니라 얻어지는 "
        "무질서도(대부분 풀려난 수화수) 때문에 진행됩니다. 양의 ΔH°를 더 큰 "
        "양의 ΔS°가 넘어서는, 흡열 흡착에서 흔한 상황입니다.",

    # ------------------------------------------------- activation energy
    "E_a = {Ea} kJ/mol is below about 40 kJ/mol, which indicates a "
    "**diffusion-controlled, physical** process. Physisorption has a low "
    "energy barrier, so the rate is limited by how fast adsorbate reaches "
    "the surface rather than by the binding event itself.":
        "E_a = {Ea} kJ/mol로 약 40 kJ/mol 아래이며, 이는 **확산이 지배하는 "
        "물리적** 과정을 뜻합니다. 물리흡착은 에너지 장벽이 낮으므로, 속도는 "
        "결합 자체가 아니라 흡착질이 표면에 얼마나 빨리 도달하는지에 따라 "
        "제한됩니다.",

    "E_a = {Ea} kJ/mol exceeds 40 kJ/mol, the conventional threshold for a "
    "**chemically controlled** process. The rate is limited by bond "
    "formation at the surface, which is consistent with chemisorption.":
        "E_a = {Ea} kJ/mol로 **화학적으로 지배되는** 과정의 관례적 기준인 "
        "40 kJ/mol을 넘습니다. 속도가 표면에서의 결합 형성으로 제한되며, 이는 "
        "화학흡착과 부합합니다.",

    "E_a = {Ea} kJ/mol is negative, meaning the rate *decreases* with "
    "temperature. For a single elementary step this is impossible; it "
    "usually means the apparent rate constant lumps together an exothermic "
    "pre-equilibrium with the rate-determining step, or that the kinetic "
    "model does not describe the data at every temperature.":
        "E_a = {Ea} kJ/mol로 음수이며, 온도가 오를수록 속도가 *감소*한다는 "
        "뜻입니다. 단일 소단계에서는 불가능한 일입니다. 보통 겉보기 속도상수가 "
        "발열 전평형과 속도결정 단계를 함께 묶고 있거나, 속도식이 모든 온도에서 "
        "데이터를 설명하지 못한다는 뜻입니다.",

    # ----------------------------------------------- sticking probability
    "S* = {S} lies between 0 and 1, the range in which the "
    "sticking-probability model is valid. It is read as the fraction of "
    "molecular collisions with the surface that result in adsorption: here "
    "about {v1:.1f}% of encounters stick.":
        "S* = {S}으로 부착확률 모델이 유효한 0과 1 사이에 있습니다. 표면과의 "
        "분자 충돌 가운데 흡착으로 이어지는 비율로 읽으며, 여기서는 충돌의 약 "
        "{v1:.1f}%가 부착됩니다.",

    "S* = {S} is not positive, so the model does not apply here.":
        "S* = {S}으로 양수가 아니므로 이 모델은 여기에 적용되지 않습니다.",

    "S* = {S} exceeds 1, which is outside the model's valid range (a "
    "probability cannot exceed unity). The usual cause is that coverage θ "
    "was computed at a concentration where the surface is far from "
    "saturated. Treat this result as uninterpretable.":
        "S* = {S}으로 1을 넘으며, 이는 모델의 유효 범위 밖입니다(확률은 1을 "
        "넘을 수 없습니다). 보통은 표면이 포화와 거리가 먼 농도에서 피복률 θ를 "
        "계산했기 때문입니다. 이 결과는 해석할 수 없는 것으로 보아야 합니다.",
}

# isosteric heat of adsorption, read off the ΔH_iso vs loading trend
KO_THERMO.update({
    "The isosteric heat is essentially constant with loading, which is the "
    "signature of an energetically **homogeneous** surface: every site binds "
    "with the same enthalpy. This is the assumption Langmuir makes, so a "
    "constant ΔH_iso supports a Langmuir description.":
        "등량 흡착열이 흡착량에 따라 사실상 일정합니다. 에너지적으로 **균일한** "
        "표면의 특징이며, 모든 흡착점이 같은 엔탈피로 결합한다는 뜻입니다. "
        "Langmuir가 세우는 가정이므로, ΔH_iso가 일정하다는 것은 Langmuir 설명을 "
        "뒷받침합니다.",

    "|ΔH_iso| decreases as loading increases (the values become less "
    "negative). This is the classic **heterogeneous surface** result: the "
    "highest-energy sites are occupied first, so each additional molecule "
    "binds more weakly than the last. It supports Freundlich, Sips or Tóth "
    "over Langmuir.":
        "흡착량이 늘수록 |ΔH_iso|가 감소합니다(값이 덜 음수가 됩니다). 전형적인 "
        "**불균일 표면**의 결과로, 에너지가 가장 높은 흡착점이 먼저 채워지므로 "
        "분자가 하나씩 더해질수록 결합이 약해집니다. Langmuir보다 Freundlich, "
        "Sips, Tóth를 뒷받침합니다.",

    "|ΔH_iso| increases with loading, meaning later molecules bind *more* "
    "strongly than earlier ones. That indicates **cooperative adsorption**: "
    "adsorbed molecules attract further adsorbate, as in surface aggregation "
    "or hemimicelle formation. Cross-check it against a Hill coefficient "
    "above 1.":
        "흡착량이 늘수록 |ΔH_iso|가 증가합니다. 나중에 결합하는 분자가 먼저 "
        "결합한 분자보다 *더 강하게* 붙는다는 뜻입니다. 이는 **협동적 흡착**을 "
        "가리키며, 표면 응집이나 반미셀 형성처럼 이미 흡착된 분자가 다른 "
        "흡착질을 끌어당기는 경우입니다. Hill 계수가 1보다 큰지와 함께 "
        "확인하세요.",

    "ΔH_iso is obtained at constant loading, so unlike the van't Hoff ΔH° it "
    "resolves how the binding enthalpy changes as the surface fills. Its "
    "variation with coverage is direct evidence about surface heterogeneity.":
        "ΔH_iso는 흡착량을 고정한 상태에서 얻으므로, van 't Hoff의 ΔH°와 달리 "
        "표면이 채워지면서 결합 엔탈피가 어떻게 변하는지를 분해해 보여 줍니다. "
        "피복률에 따른 변화는 표면 불균일성에 대한 직접적인 증거입니다.",
})
