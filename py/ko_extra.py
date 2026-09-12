# -*- coding: utf-8 -*-
"""Korean for the interpretation paragraphs written as lambdas.

The shorter models declare their interpretation inline as
``interpretation=lambda f, c: [...]`` rather than as a named function, and
those sentences are collected here.
"""

KO_EXTRA = {

    # ------------------------------------------------------------ Langmuir
    "All values fall in 0 < R_L < 1, which classifies the isotherm as "
    "favourable: the surface's affinity for the adsorbate is high enough "
    "that uptake is efficient at low residual concentration.":
        "모든 값이 0 < R_L < 1에 들어가므로 등온선은 유리한 것으로 분류됩니다. "
        "표면의 흡착질에 대한 친화도가 충분히 높아, 낮은 잔류 농도에서도 흡착이 "
        "효율적입니다.",

    "Values outside 0 < R_L < 1 indicate an unfavourable or irreversible "
    "classification and usually mean K_L or C_0 has a unit problem.":
        "0 < R_L < 1을 벗어난 값은 불리하거나 비가역적인 분류를 뜻하며, 보통 "
        "K_L이나 C_0의 단위에 문제가 있다는 의미입니다.",

    # ---------------------------------------------------------------- BET
    "A large C_BET here says the first layer is bound far more strongly "
    "than subsequent ones, so the isotherm shows a clear knee at monolayer "
    "completion (type II behaviour).":
        "여기서 C_BET가 크다는 것은 첫 번째 층이 이후 층들보다 훨씬 강하게 "
        "결합한다는 뜻이므로, 단분자층이 완성되는 지점에서 등온선에 뚜렷한 "
        "꺾임이 나타납니다(II형 거동).",

    "A small C_BET means first-layer and multilayer energies are similar, "
    "so there is no sharp monolayer point and q_s is poorly defined.":
        "C_BET가 작다는 것은 첫 번째 층과 다층의 에너지가 비슷하다는 뜻이므로, "
        "뚜렷한 단분자층 지점이 없고 q_s도 잘 정의되지 않습니다.",

    "The liquid-phase BET model needs the solubility limit Cs. If you left "
    "it at the default, q_s and C_BET are not physically meaningful; enter "
    "the real saturation concentration in the experiment panel.":
        "액상 BET 모델에는 용해도 한계 Cs가 필요합니다. 기본값 그대로 두었다면 "
        "q_s와 C_BET는 물리적으로 의미가 없습니다. 실험 패널에 실제 포화 농도를 "
        "입력하세요.",

    # ------------------------------------------------------- other models
    "Baudu generalises Langmuir by letting the affinity constant itself "
    "depend on coverage: which is why it captures isotherms that "
    "Langmuir's fixed affinity cannot.":
        "Baudu는 친화도 상수 자체가 피복률에 의존하도록 하여 Langmuir를 "
        "일반화합니다. 그래서 Langmuir의 고정된 친화도로는 담아낼 수 없는 "
        "등온선까지 설명합니다.",

    "Validity check FAILED: the Baudu model requires both 1 + x + y and "
    "1 + x to lie between 0 and 1. Your fitted values fall outside that "
    "range, so these parameters are outside the model's domain of "
    "applicability and should not be reported.":
        "타당성 검사 실패: Baudu 모델은 1 + x + y와 1 + x가 모두 0과 1 사이에 "
        "있어야 합니다. 적합된 값이 그 범위를 벗어나므로, 이 매개변수들은 모델의 "
        "적용 범위 밖에 있어 보고해서는 안 됩니다.",

    "Be careful how you present this result. With four adjustable "
    "parameters Fritz–Schlünder will fit almost any monotonic dataset, so "
    "a high R² is close to guaranteed and carries little mechanistic "
    "information. Compare it to simpler models on AICc, not on R².":
        "이 결과를 제시할 때는 주의하세요. 조정 가능한 매개변수가 네 개인 "
        "Fritz–Schlünder는 단조 증가하는 데이터라면 거의 무엇이든 잘 맞추므로, "
        "높은 R²은 사실상 보장되어 있고 메커니즘에 대한 정보를 거의 담지 "
        "않습니다. R²이 아니라 AICc로 더 단순한 모델과 비교하세요.",

    "α ≈ β, which means Fritz–Schlünder has reduced to the Sips equation. "
    "Fit Sips instead and save two parameters.":
        "α ≈ β이므로 Fritz–Schlünder가 Sips 식으로 환원되었습니다. 대신 Sips를 "
        "적합해 매개변수 두 개를 아끼세요.",

    "α and β differ, so the model is using its full flexibility to bend "
    "the isotherm's low- and high-concentration ends independently.":
        "α와 β가 다르므로, 모델이 등온선의 낮은 농도 쪽 끝과 높은 농도 쪽 끝을 "
        "독립적으로 휘게 하는 유연성을 온전히 사용하고 있습니다.",

    "The Halsey equation is algebraically the Freundlich equation "
    "rewritten, with n_H = −n. Its R² will therefore always equal the "
    "Freundlich R². Reporting both as independent evidence is double "
    "counting, a common error in the literature.":
        "Halsey 식은 n_H = −n으로 두고 Freundlich 식을 대수적으로 다시 쓴 "
        "것입니다. 따라서 R²은 언제나 Freundlich의 R²과 같습니다. 둘을 서로 "
        "독립적인 근거로 보고하는 것은 이중 계산이며, 문헌에서 흔한 "
        "오류입니다.",

    "Its stated purpose is different though: Halsey was derived for "
    "multilayer condensation at some distance from the surface, so a good "
    "fit is read as evidence of heteroporous multilayer adsorption.":
        "다만 표방하는 목적은 다릅니다. Halsey는 표면에서 어느 정도 떨어진 "
        "곳에서 일어나는 다층 응축을 위해 유도되었으므로, 잘 맞으면 이질적인 "
        "세공 구조에서의 다층 흡착의 근거로 읽습니다.",

    "The Harkins–Jura constant A is taken as proportional to the "
    "adsorbent's surface area, so a good fit is used as evidence for "
    "multilayer adsorption across a heterogeneous distribution of pores.":
        "Harkins–Jura의 상수 A는 흡착제의 표면적에 비례하는 값으로 보므로, 잘 "
        "맞으면 세공이 불균일하게 분포한 표면에서의 다층 흡착의 근거로 "
        "사용합니다.",

    "This model is very often reported with a poor R². If yours fits "
    "badly, that is the normal result for solution-phase adsorption and is "
    "worth stating rather than omitting.":
        "이 모델은 R²이 낮게 보고되는 경우가 매우 많습니다. 잘 맞지 않더라도 "
        "용액상 흡착에서는 정상적인 결과이므로, 생략하기보다 그대로 밝히는 편이 "
        "좋습니다.",

    "Jovanović differs from Langmuir by allowing mechanical contact "
    "between arriving and departing molecules. It reduces to Langmuir at "
    "low coverage and shares the same plateau, so if Jovanović fits much "
    "better than Langmuir the difference is in the approach to saturation, "
    "not the capacity.":
        "Jovanović는 도달하는 분자와 떠나는 분자 사이의 역학적 접촉을 허용한다는 "
        "점에서 Langmuir와 다릅니다. 낮은 피복률에서는 Langmuir로 환원되고 같은 "
        "평탄역을 가지므로, Jovanović가 Langmuir보다 훨씬 잘 맞는다면 차이는 "
        "흡착용량이 아니라 포화에 접근하는 방식에 있습니다.",

    "The Elovich isotherm assumes the number of available sites grows "
    "exponentially with coverage, which implies multilayer adsorption. It "
    "is implicit in qe, so AdsorpFit solves it numerically at every point "
    "rather than using the usual ln(qe/Ce) linear plot.":
        "Elovich 등온식은 이용 가능한 흡착점의 수가 피복률에 따라 지수적으로 "
        "증가한다고 가정하며, 이는 다층 흡착을 뜻합니다. 이 식은 qe에 대해 "
        "음함수이므로, AdsorpFit은 흔히 쓰는 ln(qe/Ce) 선형 그래프 대신 모든 "
        "점에서 수치적으로 풉니다.",

    "Radke–Prausnitz was built for dilute solutions, so it is the model to "
    "prefer when your data cluster at low Ce and you care about behaviour "
    "near the origin rather than near saturation.":
        "Radke–Prausnitz는 묽은 용액을 위해 만들어졌습니다. 데이터가 낮은 Ce에 "
        "몰려 있고 포화 부근보다 원점 부근의 거동이 중요할 때 택할 "
        "모델입니다.",

    "Vieth–Sladek splits uptake into a linear 'dissolution' term and a "
    "saturable site-binding term. A large k_VS relative to the Langmuir "
    "term says partitioning into the bulk of the solid dominates; a small "
    "one says surface site binding does.":
        "Vieth–Sladek는 흡착을 선형 '용해' 항과 포화 가능한 흡착점 결합 항으로 "
        "나눕니다. Langmuir 항에 비해 k_VS가 크면 고체 내부로의 분배가 "
        "지배적이고, 작으면 표면 흡착점 결합이 지배적입니다.",

    "a_K ≈ 1, so Khan has collapsed to Langmuir; use Langmuir instead.":
        "a_K ≈ 1이므로 Khan이 Langmuir로 환원되었습니다. 대신 Langmuir를 "
        "사용하세요.",

    "n ≈ 1, so Koble–Corrigan has reduced to Langmuir.":
        "n ≈ 1이므로 Koble–Corrigan이 Langmuir로 환원되었습니다.",

    "n > 1 as required for thermodynamic consistency; the model is "
    "describing a heterogeneous surface.":
        "열역학적 정합성이 요구하는 대로 n > 1이며, 이 모델은 불균일한 표면을 "
        "설명하고 있습니다.",

    "n < 1 here. Koble and Corrigan noted that n below 1 makes the model "
    "thermodynamically inconsistent, so this fit should not be reported as "
    "evidence of anything: another model describes these data better.":
        "여기서는 n < 1입니다. Koble과 Corrigan은 n이 1보다 작으면 모델이 "
        "열역학적으로 정합하지 않게 된다고 지적했으므로, 이 적합을 무언가의 "
        "근거로 보고해서는 안 됩니다. 다른 모델이 이 데이터를 더 잘 "
        "설명합니다.",

    "α ≈ 1 recovers the Jovanović isotherm, a narrow, near-uniform energy "
    "distribution.":
        "α ≈ 1이면 Jovanović 등온식이 되며, 이는 좁고 거의 균일한 에너지 "
        "분포를 뜻합니다.",

    "m ≈ n, so the distribution is symmetric and the model has reduced to "
    "Sips. Use Sips instead.":
        "m ≈ n이므로 분포가 대칭이고 모델이 Sips로 환원되었습니다. 대신 Sips를 "
        "사용하세요.",

    "m and n independently shape the two tails of the underlying "
    "site-energy distribution: this is the model's advantage over Sips, "
    "which forces both tails to share one exponent.":
        "m과 n이 바탕이 되는 흡착점 에너지 분포의 두 꼬리를 각각 따로 "
        "결정합니다. 두 꼬리에 하나의 지수를 강요하는 Sips에 대한 이 모델의 "
        "장점입니다.",

    "the low-energy tail is broader.": "저에너지 쪽 꼬리가 더 넓습니다.",
    "the high-energy tail is broader.": "고에너지 쪽 꼬리가 더 넓습니다.",

    # ------------------------------------------------------------ kinetics
    "It is close to 1, so pseudo-first-order is justified for these data.":
        "1에 가까우므로 이 데이터에서는 유사 1차식이 타당합니다.",

    "It is close to 2, so pseudo-second-order is justified.":
        "2에 가까우므로 유사 2차식이 타당합니다.",

    "Note that k_n's units depend on n, so k_n from this fit cannot be "
    "compared with a k₁ or k₂ from PFO/PSO.":
        "k_n의 단위는 n에 따라 달라지므로, 이 적합의 k_n은 유사 1차나 유사 "
        "2차의 k₁, k₂와 비교할 수 없습니다.",

    "essentially pure pseudo-first-order; report PFO instead.":
        "사실상 순수한 유사 1차이므로, 대신 유사 1차식을 보고하세요.",

    "essentially pure pseudo-second-order; report PSO instead.":
        "사실상 순수한 유사 2차이므로, 대신 유사 2차식을 보고하세요.",

    "MOE sidesteps the PFO-vs-PSO argument that dominates the adsorption "
    "literature by letting the data decide the balance rather than forcing "
    "an either/or.":
        "혼합차수 모델은 양자택일을 강요하는 대신 데이터가 균형을 정하게 하여, "
        "흡착 문헌을 지배해 온 유사 1차 대 유사 2차 논쟁을 비껴갑니다.",

    "monodentate binding: one molecule per site.":
        "단일 자리 결합으로, 흡착점 하나에 분자 하나입니다.",

    "bidentate binding: each molecule occupies two sites, which is common "
    "for chelating metal complexes and carboxylate groups.":
        "두 자리 결합으로, 분자 하나가 흡착점 두 개를 차지합니다. 킬레이트 금속 "
        "착물과 카복실기에서 흔합니다.",

    "h ≈ 0 means the rate constant really is constant and classical PFO is "
    "adequate; the fractal correction is unnecessary here.":
        "h ≈ 0은 속도상수가 실제로 일정하다는 뜻이며, 고전적인 유사 1차식으로 "
        "충분합니다. 여기서는 프랙탈 보정이 필요하지 않습니다.",

    "α ≈ 0.5 specifically recovers the Weber–Morris √t dependence, meaning "
    "classical intraparticle diffusion.":
        "α ≈ 0.5는 Weber–Morris의 √t 의존성을 그대로 재현하며, 고전적인 입자 내 "
        "확산을 뜻합니다.",

    "Values around 10⁻¹¹–10⁻¹³ cm²/s indicate strongly hindered pore "
    "diffusion typical of microporous adsorbents; values near the "
    "free-solution value (~10⁻⁵ cm²/s) mean the pore network offers little "
    "resistance.":
        "10⁻¹¹~10⁻¹³ cm²/s 정도의 값은 미세다공성 흡착제에서 전형적인, 크게 "
        "저해된 세공 확산을 뜻합니다. 자유 용액 값(약 10⁻⁵ cm²/s)에 가까우면 "
        "세공 구조가 거의 저항을 주지 않는다는 의미입니다.",

    "Because D appears only as D/r², it is perfectly correlated with the "
    "particle radius. If you fitted r rather than fixing it at a measured "
    "value, neither number is meaningful on its own, only the ratio is.":
        "D는 D/r² 형태로만 나타나므로 입자 반지름과 완전히 상관되어 있습니다. "
        "측정값으로 고정하지 않고 r까지 적합했다면 두 수치 모두 단독으로는 "
        "의미가 없고, 오직 그 비만 의미가 있습니다.",

    "That separation is large enough for the two steps to be genuinely "
    "distinguishable: usually fast adsorption on the external surface "
    "followed by slow diffusion into the interior.":
        "이 정도 차이라면 두 단계를 실제로 구별할 수 있습니다. 보통 외부 표면의 "
        "빠른 흡착에 이어 내부로의 느린 확산이 일어나는 경우입니다.",

    "That separation is small, so the two exponentials are not well "
    "distinguished and the extra parameters are probably not justified. "
    "Check the standard errors before reporting both steps.":
        "차이가 작아 두 지수항이 잘 구별되지 않으며, 추가된 매개변수가 정당화되기 "
        "어렵습니다. 두 단계를 모두 보고하기 전에 표준오차를 확인하세요.",

    " This gap is large enough to question the fit.":
        " 이 정도 차이라면 적합 자체를 의심해 볼 만합니다.",

    "Be aware that the film-diffusion equation is *algebraically "
    "identical* to pseudo-first-order. It will always give exactly the "
    "same R², SSE and curve. What differs is the claim you attach to it: "
    "PFO says the rate depends on free sites, film diffusion says the rate "
    "depends on transport through the boundary layer. Fitting quality "
    "cannot distinguish them.":
        "막 확산식은 유사 1차식과 *대수적으로 동일*하다는 점에 유의하세요. "
        "R², SSE, 곡선이 언제나 정확히 같게 나옵니다. 다른 것은 거기에 붙이는 "
        "주장뿐입니다. 유사 1차식은 속도가 빈 흡착점에 의존한다고 말하고, 막 "
        "확산은 속도가 경계층을 통한 물질 전달에 의존한다고 말합니다. 적합의 "
        "품질로는 둘을 구별할 수 없습니다.",

    "What can distinguish them is experiment: film diffusion is sensitive "
    "to stirring speed, PFO site-limited kinetics is not. If your rate "
    "constant changes when you change the agitation rate, film diffusion "
    "is real. The Boyd plot in the diffusion panel makes the same test "
    "graphically: a straight line through the origin indicates particle "
    "diffusion control, while a non-zero intercept points to film "
    "diffusion.":
        "둘을 구별할 수 있는 것은 실험입니다. 막 확산은 교반 속도에 민감하지만, "
        "흡착점이 제한하는 유사 1차 속도론은 그렇지 않습니다. 교반 속도를 바꿀 때 "
        "속도상수가 달라진다면 막 확산이 실재하는 것입니다. 확산 패널의 Boyd "
        "그래프가 같은 검정을 그림으로 보여 줍니다. 원점을 지나는 직선은 입자 "
        "확산 지배를, 0이 아닌 절편은 막 확산을 가리킵니다.",
}
