# -*- coding: utf-8 -*-
"""Korean for the model advisor: what the data look like, and why a model
is recommended, usable or not advised.
"""

KO_ADVISOR = {

    # ------------------------------------------------- shape of the data
    "You have {n} equilibrium points spanning C_e = {xlo} to {xhi} {span}, "
    "with q_e from {ylo} to {yhi}.":
        "평형점 {n}개가 C_e = {xlo}부터 {xhi}까지 {span} 분포하며, q_e는 "
        "{ylo}부터 {yhi}까지입니다.",

    "({d:.1f} decades)": "({d:.1f}자릿수)",

    "You have {n} time points from {tlo} to {thi}, reaching q = {q}.":
        "시간점 {n}개가 {tlo}부터 {thi}까지 있으며, q = {q}에 도달합니다.",

    "The isotherm **reaches a plateau**, the top third of the "
    "concentration range adds little further uptake. Saturation models "
    "(Langmuir, Sips, Tóth) can therefore give a capacity that is measured "
    "rather than extrapolated.":
        "등온선이 **평탄역에 도달**했습니다. 농도 범위의 상위 3분의 1에서 "
        "흡착량이 거의 늘지 않습니다. 따라서 포화 모델(Langmuir, Sips, Tóth)이 "
        "외삽이 아니라 실제로 측정된 흡착용량을 줄 수 있습니다.",

    "The isotherm is **still rising steeply** at your highest "
    "concentration. Nothing here determines a saturation capacity, so "
    "treat any q_max as an extrapolation and prefer models that do not "
    "assume a plateau.":
        "가장 높은 농도에서도 등온선이 **여전히 가파르게 상승** 중입니다. "
        "포화 용량을 결정할 근거가 없으므로 q_max는 외삽으로 보아야 하며, "
        "평탄역을 가정하지 않는 모델을 우선하세요.",

    "The isotherm is beginning to level off but has not fully plateaued, "
    "so a fitted capacity is only moderately constrained.":
        "등온선이 완만해지기 시작했지만 완전한 평탄역에는 이르지 못했으므로, "
        "적합된 흡착용량은 제한적으로만 결정됩니다.",

    "The overall log–log slope is {sl}, so the Freundlich 1/n is about "
    "{sl}. {verdict}":
        "전체 log–log 기울기가 {sl}이므로 Freundlich의 1/n도 약 {sl}입니다. "
        "{verdict}",

    "Well below 1, so adsorption is strongly favourable and the surface is "
    "energetically heterogeneous.":
        "1보다 충분히 작으므로 흡착이 강하게 유리하며, 표면은 에너지적으로 "
        "불균일합니다.",

    "Close to 1, so uptake is nearly proportional to concentration. You "
    "may be in the linear Henry's-law regime, where most isotherm models "
    "become hard to distinguish.":
        "1에 가까우므로 흡착량이 농도에 거의 비례합니다. 선형 헨리 법칙 "
        "영역일 수 있으며, 이 영역에서는 대부분의 등온흡착식을 서로 구별하기 "
        "어렵습니다.",

    "Between 0.5 and 1, the usual favourable range.":
        "0.5와 1 사이로, 일반적인 유리한 범위입니다.",

    "**Caution:** your data are nearly a straight line through the origin. "
    "In this regime almost every isotherm model will fit well and they "
    "cannot be told apart; extend the concentration range before claiming "
    "a mechanism.":
        "**주의:** 데이터가 원점을 지나는 직선에 가깝습니다. 이 영역에서는 "
        "거의 모든 등온흡착식이 잘 맞아 서로 구별할 수 없으므로, 메커니즘을 "
        "주장하기 전에 농도 범위를 넓히세요.",

    "The curve appears **sigmoidal** (uptake accelerates before it "
    "saturates). Langmuir, Freundlich and Tóth are all strictly concave "
    "and cannot reproduce that; Hill and BET can.":
        "곡선이 **S자형**으로 보입니다(포화 전에 흡착이 가속됩니다). "
        "Langmuir, Freundlich, Tóth는 모두 순수하게 오목하여 이를 재현할 수 "
        "없지만, Hill과 BET는 가능합니다.",

    "The run **reaches equilibrium**; uptake is flat over the final third: "
    "so q_e is directly measured and the models that fit it are on solid "
    "ground.":
        "실험이 **평형에 도달**했습니다. 마지막 3분의 1 구간에서 흡착량이 "
        "평탄하므로 q_e를 직접 측정한 셈이며, 이를 적합하는 모델들은 탄탄한 "
        "근거 위에 있습니다.",

    "Uptake is **still climbing** at your last time point. Every model "
    "that fits q_e will be extrapolating, and because q_e and the rate "
    "constant are correlated, both become unreliable. Extend the contact "
    "time.":
        "마지막 시간점에서도 흡착량이 **계속 증가** 중입니다. q_e를 적합하는 "
        "모든 모델이 외삽하게 되며, q_e와 속도상수는 서로 상관되어 있으므로 "
        "둘 다 신뢰할 수 없게 됩니다. 접촉 시간을 늘리세요.",

    "{k} point(s) fall below half the final uptake. {enough}":
        "최종 흡착량의 절반 아래에 있는 점이 {k}개입니다. {enough}",

    "That is enough to define the early, fast stage that fixes the rate "
    "constant.":
        "속도상수를 결정하는 초기의 빠른 단계를 규정하기에 충분합니다.",

    "**That is too few.** Rate constants are determined almost entirely "
    "by the early stage, so sample more densely at short times.":
        "**너무 적습니다.** 속도상수는 거의 전적으로 초기 단계에서 "
        "결정되므로, 짧은 시간대를 더 촘촘히 측정하세요.",

    "The uptake rate against √t drops by a factor of {ratio} partway "
    "through, which indicates **two distinct stages**: typically fast "
    "external-surface adsorption followed by slower intraparticle "
    "diffusion. The Weber–Morris multi-region analysis and the "
    "double-exponential model are both worth running.":
        "√t에 대한 흡착 속도가 도중에 {ratio}배로 떨어집니다. 이는 **뚜렷이 "
        "구분되는 두 단계**를 뜻하며, 대개 빠른 외부 표면 흡착에 이어 느린 "
        "입자 내 확산이 일어나는 경우입니다. Weber–Morris 다구간 해석과 "
        "이중지수 모델을 모두 실행해 볼 가치가 있습니다.",

    "**Your uptake curve decreases somewhere.** That breaks the core "
    "assumption of every kinetic model here; check those points for "
    "desorption or measurement error first.":
        "**흡착 곡선이 중간에 감소하는 구간이 있습니다.** 이는 여기 있는 모든 "
        "속도식의 핵심 가정을 깨뜨립니다. 먼저 해당 점들에서 탈착이나 측정 "
        "오차가 있었는지 확인하세요.",

    # ------------------------------------------------------- verdicts
    "The fit did not converge on these data.":
        "이 데이터에서 적합이 수렴하지 않았습니다.",

    "It reproduces only {pct:.0f}% of the variance in your data "
    "(R² = {r2}), so it is not describing this system.":
        "데이터 분산의 {pct:.0f}%만 재현합니다(R² = {r2}). 이 계를 설명하지 "
        "못하고 있습니다.",

    "Fits as well as anything here (R² = {r2}), but {other} matches it "
    "with only {np_other} parameters instead of {np_this}. The extra "
    "parameters are not earning their place, so prefer the simpler model "
    "unless you need this one's specific physical meaning.":
        "여기 있는 어느 모델 못지않게 잘 맞습니다(R² = {r2}). 다만 {other}이(가) "
        "매개변수 {np_this}개가 아니라 {np_other}개만으로 같은 수준에 "
        "도달합니다. 추가된 매개변수가 제 몫을 하지 못하므로, 이 모델 고유의 "
        "물리적 의미가 꼭 필요한 경우가 아니라면 더 단순한 모델을 택하세요.",

    "Best-supported model for these data, and the most parsimonious of the "
    "equally good ones (ΔAICc = {delta}, R² = {r2}, {np} parameters).":
        "이 데이터에서 가장 강하게 뒷받침되는 모델이며, 같은 수준의 모델 "
        "가운데 가장 간결합니다(ΔAICc = {delta}, R² = {r2}, 매개변수 {np}개).",

    "Describes the data well (R² = {r2}) but is ΔAICc = {delta} behind the "
    "leading model, so it costs accuracy or parameters without a "
    "compensating gain.":
        "데이터를 잘 설명하지만(R² = {r2}) 선두 모델보다 ΔAICc = {delta}만큼 "
        "뒤처집니다. 그만한 이득 없이 정확도나 매개변수를 더 쓰는 셈입니다.",

    "Still reproduces the data (R² = {r2}), but at ΔAICc = {delta} the "
    "evidence clearly favours another model. Report it only if its "
    "physical interpretation is what you specifically need.":
        "데이터를 재현하기는 하지만(R² = {r2}), ΔAICc = {delta}에서는 근거가 "
        "다른 모델을 분명히 지지합니다. 이 모델의 물리적 해석이 특별히 필요한 "
        "경우에만 보고하세요.",

    # -------------------------------------------------- physics notes
    "This model's capacity parameter is a saturation plateau, and your "
    "data have not reached one, so q_max will be an extrapolation well "
    "beyond the measured range.":
        "이 모델의 용량 매개변수는 포화 평탄역을 뜻하는데 데이터가 아직 거기에 "
        "이르지 못했으므로, q_max는 측정 범위를 크게 벗어난 외삽이 됩니다.",

    "Your data reach a clear plateau, which is exactly what this model's "
    "saturation capacity is meant to describe.":
        "데이터가 뚜렷한 평탄역에 도달했으며, 이는 이 모델의 포화 용량이 "
        "설명하려는 바로 그 상황입니다.",

    "Freundlich has no plateau: it rises without limit: so it cannot "
    "reproduce the flat region your data show, and K_F must not be quoted "
    "as a capacity.":
        "Freundlich에는 평탄역이 없고 한없이 상승하므로, 데이터에 나타난 평탄 "
        "구간을 재현할 수 없습니다. K_F를 흡착용량으로 인용해서는 안 됩니다.",

    "Freundlich suits data that are still rising, as yours are, because it "
    "makes no saturation assumption.":
        "Freundlich는 포화를 가정하지 않으므로, 지금처럼 아직 상승 중인 "
        "데이터에 적합합니다.",

    "Temkin is a mid-coverage model with no plateau and a logarithmic "
    "divergence at low C_e; it is best kept for the middle of a "
    "concentration series.":
        "Temkin은 평탄역이 없고 낮은 C_e에서 로그로 발산하는 중간 피복률 "
        "모델이므로, 농도 계열의 중간 영역에 한정해 쓰는 것이 좋습니다.",

    "Your isotherm looks sigmoidal, and Hill is one of the few models here "
    "that can produce an S-shape; that is a genuine reason to prefer it "
    "over Langmuir.":
        "등온선이 S자형으로 보이며, Hill은 여기서 S자 형태를 만들 수 있는 몇 "
        "안 되는 모델입니다. Langmuir보다 이 모델을 택할 실질적인 근거입니다.",

    "Your isotherm appears sigmoidal. This model is strictly concave and "
    "cannot reproduce an inflection point.":
        "등온선이 S자형으로 보입니다. 이 모델은 순수하게 오목하여 변곡점을 "
        "재현할 수 없습니다.",

    "Your data are close to a straight line through the origin (R² = "
    "{r2}). In the Henry's-law regime the affinity and capacity parameters "
    "become strongly correlated and neither is well determined.":
        "데이터가 원점을 지나는 직선에 가깝습니다(R² = {r2}). 헨리 법칙 "
        "영역에서는 친화도와 용량 매개변수가 강하게 상관되어 둘 다 제대로 "
        "결정되지 않습니다.",

    "{np} parameters against {n} data points leaves very little to "
    "constrain them, so this model will fit almost anything at this sample "
    "size.":
        "데이터점 {n}개에 매개변수가 {np}개여서 이를 제약할 정보가 거의 "
        "없습니다. 이 표본 크기에서는 거의 무엇이든 잘 맞습니다.",

    "The log–log slope changes noticeably from the dilute to the "
    "concentrated end of your data, which is the signature of a "
    "heterogeneous surface: the situation this model's extra exponent "
    "exists to capture.":
        "묽은 쪽에서 진한 쪽으로 가면서 log–log 기울기가 뚜렷이 변합니다. 이는 "
        "불균일 표면의 특징이며, 이 모델의 추가 지수가 포착하려는 상황입니다.",

    "This model fits an equilibrium capacity, and your run has not "
    "equilibrated: q_e and the rate constant will trade off against each "
    "other.":
        "이 모델은 평형 흡착량을 적합하는데 실험이 아직 평형에 이르지 "
        "않았습니다. q_e와 속도상수가 서로 상쇄되며 맞춰집니다.",

    "Your run reaches a clear plateau, so q_e is well defined.":
        "실험이 뚜렷한 평탄역에 도달했으므로 q_e가 잘 정의됩니다.",

    "Only {k} point(s) before half the uptake was reached, and rate "
    "constants are determined by that region.":
        "흡착량의 절반에 이르기 전 점이 {k}개뿐이며, 속도상수는 바로 그 "
        "구간에서 결정됩니다.",

    "Elovich rises logarithmically without limit, so it cannot match the "
    "plateau in your data.":
        "Elovich는 한없이 로그 형태로 상승하므로, 데이터의 평탄역을 맞출 수 "
        "없습니다.",

    "Your curve shows a distinct break between a fast and a slow stage, "
    "which is the specific case this model exists for.":
        "곡선에 빠른 단계와 느린 단계 사이의 뚜렷한 꺾임이 있으며, 이 모델이 "
        "바로 그 경우를 위해 존재합니다.",

    "Your curve shows no clear two-stage break, so the second exponential "
    "has little to explain.":
        "뚜렷한 2단계 꺾임이 없으므로, 두 번째 지수항이 설명할 것이 거의 "
        "없습니다.",

    "A break in the q vs √t slope is visible in your data, the "
    "multi-region analysis on the Diffusion tab is the right tool for it.":
        "데이터에서 q 대 √t 기울기의 꺾임이 보입니다. 확산 탭의 다구간 해석이 "
        "이를 다루기에 알맞은 도구입니다.",

    "Your uptake curve is not monotonic. Every kinetic model here assumes "
    "uptake only increases, so check those points before modelling.":
        "흡착 곡선이 단조증가가 아닙니다. 여기 있는 모든 속도식은 흡착량이 "
        "증가하기만 한다고 가정하므로, 모델링 전에 해당 점들을 확인하세요.",
}
