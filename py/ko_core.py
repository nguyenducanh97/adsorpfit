# -*- coding: utf-8 -*-
"""Korean for the fitting engine and the JavaScript bridge.

Keyed by the English sentence. See py/lang.py for how the lookup works and
tools/i18n_py.py for the coverage report.
"""

KO_CORE = {

    # ---------------------------------------------------------- evidence
    "best model in this set": "이 조합에서 가장 좋은 모델",
    "substantial support, indistinguishable from the best model":
        "상당한 근거, 최적 모델과 구별되지 않음",
    "strong support": "강한 근거",
    "considerably less support": "근거가 뚜렷이 약함",
    "weak support": "근거가 약함",
    "essentially no support": "사실상 근거 없음",

    # ---------------------------------------------------- domain checks
    "{n} data points cannot determine {p} parameters.":
        "데이터점 {n}개로는 매개변수 {p}개를 결정할 수 없습니다.",

    "Only {n} points for {p} parameters leaves {df} degrees of freedom. "
    "The fit will look excellent because it is nearly interpolating, and "
    "the confidence intervals will be very wide.":
        "매개변수 {p}개에 데이터점이 {n}개뿐이어서 자유도가 {df}입니다. "
        "사실상 보간에 가까우므로 적합이 훌륭해 보이겠지만, 신뢰구간은 "
        "매우 넓어집니다.",

    "{k} of your q values are negative. A negative uptake usually means "
    "the measured equilibrium concentration exceeded the initial one, so "
    "check for desorption, evaporation or a calibration offset before "
    "modelling.":
        "q 값 가운데 {k}개가 음수입니다. 흡착량이 음수라는 것은 대개 측정된 "
        "평형 농도가 초기 농도보다 높았다는 뜻이므로, 모델링에 앞서 탈착, "
        "증발, 검량선 오프셋을 확인하세요.",

    "Negative concentrations or times cannot be modelled.":
        "음의 농도나 음의 시간은 모델링할 수 없습니다.",

    "Some x values are repeated. That is fine for replicate measurements, "
    "but each replicate is weighted as an independent point.":
        "x 값이 중복됩니다. 반복 측정이라면 문제가 없지만, 각 반복값이 서로 "
        "독립인 점으로 가중됩니다.",

    # ------------------------------------------- impossible predictions
    "This model predicts a NEGATIVE q of {worst} at x = {where}, which is "
    "physically impossible ({neg} of {n} fitted points are affected).":
        "이 모델은 x = {where}에서 q를 {worst}로, 즉 음수로 예측합니다. 이는 "
        "물리적으로 불가능합니다(적합에 사용된 {n}개 점 가운데 {neg}개가 "
        "해당됩니다).",

    "The fit statistics are therefore meaningless no matter how good R² "
    "looks, so do not report these parameters.":
        "따라서 R²이 아무리 좋아 보여도 적합 통계는 의미가 없으며, 이 "
        "매개변수를 보고해서는 안 됩니다.",

    "With these parameters the model is only defined for x > {lo}.":
        "이 매개변수에서 모델은 x > {lo}에서만 정의됩니다.",

    "With these parameters the model is only defined for x < {hi}.":
        "이 매개변수에서 모델은 x < {hi}에서만 정의됩니다.",

    "{below} of your {n} points lie below that.":
        "전체 {n}개 점 가운데 {below}개가 그보다 아래에 있습니다.",

    "The model is undefined at {k} of your data points, so those points "
    "contributed nothing to the fit.":
        "데이터점 {k}개에서 모델이 정의되지 않으므로, 그 점들은 적합에 전혀 "
        "기여하지 못했습니다.",

    # ---------------------------------------------------- fit failures
    "Need at least {p} points to fit {p} parameters, but got {n}.":
        "매개변수 {p}개를 적합하려면 점이 최소 {p}개 필요하지만 {n}개뿐입니다.",

    "Optimiser failed from every start.":
        "모든 초기값에서 최적화가 실패했습니다.",

    "Could not recover parameters: {exc}":
        "매개변수를 복원할 수 없습니다: {exc}",

    # ------------------------------------------------- parameter warnings
    "{sym} is not resolved by these data: its standard error ({se:.3g}) "
    "exceeds the estimate itself ({v:.3g}). Treat this parameter as "
    "indeterminate.":
        "{sym}은(는) 이 데이터로 분해되지 않습니다. 표준오차({se:.3g})가 "
        "추정값({v:.3g}) 자체보다 큽니다. 이 매개변수는 결정 불가로 "
        "보아야 합니다.",

    "{sym} hit its upper bound ({bound:g}), so the optimum lies outside "
    "the physically allowed range.":
        "{sym}이(가) 상한({bound:g})에 도달했으므로, 최적값은 물리적으로 "
        "허용된 범위 밖에 있습니다.",

    "{sym} collapsed to zero, which usually means this model term is not "
    "supported by the data.":
        "{sym}이(가) 0으로 수렴했습니다. 보통 이 모델 항을 데이터가 "
        "뒷받침하지 않는다는 뜻입니다.",

    # -------------------------------------------------- linearised fits
    "Linearisation produced fewer than two valid points (the log or "
    "reciprocal of a non-positive value).":
        "선형화 결과 유효한 점이 두 개 미만입니다(양수가 아닌 값의 로그 또는 "
        "역수 때문입니다).",

    "The {form} transform maps every point to the same x value, so no line "
    "can be fitted through them. This happens when the data are flat. The "
    "non-linear fit is unaffected.":
        "{form} 변환이 모든 점을 같은 x 값으로 보내므로 직선을 적합할 수 "
        "없습니다. 데이터가 평탄할 때 일어나며, 비선형 적합은 영향을 받지 "
        "않습니다.",

    "The {form} linearisation could not be fitted: {exc}":
        "{form} 선형화를 적합할 수 없습니다: {exc}",

    "{dropped} of {n} points were discarded by the {form} linearisation, "
    "because the transform is undefined for them. The non-linear fit uses "
    "all points.":
        "{form} 선형화에서 변환이 정의되지 않아 전체 {n}개 점 가운데 "
        "{dropped}개가 제외되었습니다. 비선형 적합은 모든 점을 사용합니다.",

    "The linear plot reports R^2 = {r2lin:.4f}, but the same parameters "
    "reproduce the raw q data with only R^2 = {r2:.4f}. The linearisation "
    "is flattering the fit.":
        "선형 그래프의 R^2은 {r2lin:.4f}이지만, 같은 매개변수로 원래의 q "
        "데이터를 재현하면 R^2은 {r2:.4f}에 불과합니다. 선형화가 적합을 실제보다 "
        "좋아 보이게 만들고 있습니다.",

    # ------------------------------------------------------- ranking
    "No model converged, so there is nothing to rank.":
        "수렴한 모델이 없어 순위를 매길 대상이 없습니다.",

    "**{name}** ranks first on {crit} ({crit} = {value:.2f}, Akaike weight "
    "{weight:.0f}%), with R² = {r2:.4f} and RMSE = {rmse:.4g}.":
        "**{name}**이(가) {crit} 기준 1위입니다({crit} = {value:.2f}, 아카이케 "
        "가중치 {weight:.0f}%, R² = {r2:.4f}, RMSE = {rmse:.4g}).",

    "However, {names} cannot be distinguished from it statistically "
    "(ΔAICc < 2). On these data you cannot claim one of these models is "
    "correct and the others are not. Say they describe the data equally "
    "well, and choose between them on physical grounds rather than on fit "
    "statistics.":
        "다만 {names}은(는) 통계적으로 이와 구별되지 않습니다(ΔAICc < 2). 이 "
        "데이터만으로는 이 가운데 하나가 옳고 나머지가 틀리다고 주장할 수 "
        "없습니다. 데이터를 똑같이 잘 설명한다고 쓰고, 적합 통계가 아니라 "
        "물리적 근거로 선택하세요.",

    "The next best model, {name}, is Δ = {delta:.1f} behind: {evidence}. "
    "The margin is large enough to prefer {best} on statistical grounds.":
        "다음으로 좋은 모델인 {name}은(는) Δ = {delta:.1f}만큼 뒤처집니다"
        "({evidence}). 이 차이는 통계적 근거만으로 {best}을(를) 선택하기에 "
        "충분합니다.",

    "Note that {name} has the highest raw R² ({r2:.4f}) but uses {np} "
    "parameters against {nb} for {best}. R² can only increase when "
    "parameters are added, so ranking models by R² systematically favours "
    "the most complex one. AICc penalises that and is the criterion to "
    "report.":
        "{name}의 R²({r2:.4f})이 가장 높지만, 매개변수를 {np}개 사용합니다"
        "({best}은(는) {nb}개). 매개변수를 늘리면 R²은 올라가기만 하므로, R²로 "
        "순위를 매기면 언제나 가장 복잡한 모델이 유리해집니다. AICc는 이를 "
        "벌점으로 반영하며, 보고해야 할 기준입니다.",

    # -------------------------------------------------------- bridge
    "x has {size2} values but y has {size}. Every point needs both a "
    "concentration/time and a q value.":
        "x에는 값이 {size2}개, y에는 {size}개 있습니다. 모든 점에는 농도 또는 "
        "시간과 q 값이 함께 있어야 합니다.",

    "This model could not be fitted to these data: {exc}":
        "이 모델은 이 데이터에 적합할 수 없습니다: {exc}",

    "This linearisation is not defined for these data: {exc}":
        "이 선형화는 이 데이터에서 정의되지 않습니다: {exc}",

    "This model needs {v1} from the experiment panel. A default was used, "
    "so the parameters are not on a physical scale.":
        "이 모델에는 실험 패널의 {v1} 값이 필요합니다. 기본값이 사용되었으므로 "
        "매개변수가 물리적 척도에 놓여 있지 않습니다.",

    "K° conversion failed at T = {v1} K: {exc}":
        "T = {v1} K에서 K° 변환에 실패했습니다: {exc}",

    "The Boyd plot has intercept {intercept} ± {intercept_stderr} and "
    "R² = {v1:.4f}. ":
        "Boyd 그래프의 절편은 {intercept} ± {intercept_stderr}, R²은 "
        "{v1:.4f}입니다. ",

    " From the slope B = {slope} min⁻¹ and a particle radius of {r} cm, "
    "the effective diffusion coefficient is D_i = B·r²/π² = {Di} cm²/min.":
        " 기울기 B = {slope} min⁻¹과 입자 반지름 {r} cm로부터 유효 확산계수는 "
        "D_i = B·r²/π² = {Di} cm²/min입니다.",

    "The plot resolves into {v3} linear regions, which is the expected "
    "multi-step behaviour. Region 1 has k_id = {v2} and region 2 has "
    "k_id = {v1} mg g⁻¹ min⁻⁰·⁵. ":
        "그래프가 선형 구간 {v3}개로 나뉘며, 이는 예상되는 다단계 거동입니다. "
        "구간 1의 k_id는 {v2}, 구간 2의 k_id는 {v1} mg g⁻¹ min⁻⁰·⁵입니다. ",
}
