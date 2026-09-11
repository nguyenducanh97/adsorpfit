/* ==========================================================================
   AdsorpFit: internationalisation.

   Scope note, stated honestly: the interface, the guide, the model names,
   the parameter meanings and the advisor verdicts are translated. The
   automatically generated interpretation paragraphs are composed in Python
   with fitted numbers interpolated into them, and those remain English for
   now: translating them means maintaining a parallel set of sentence
   templates in the Python layer, which is a separate piece of work.

   Usage:
     I18N.set("ko")            switch language
     I18N.t("tab.kinetics")    look up a string
     I18N.apply(root)          translate every [data-i18n] node under root
   ========================================================================== */

const I18N = (function () {
  "use strict";

  const DICT = {
    en: {
      "brand.sub": "Adsorption data modelling",
      "brand.product": "A product of",
      "brand.and": "and",

      "tab.kinetics": "Kinetics",
      "tab.isotherm": "Isotherms",
      "tab.thermo": "Thermodynamics",
      "tab.guide": "Guide",

      "panel.data": "1 · Data",
      "panel.experiment": "2 · Experiment",
      "panel.models": "3 · Models",
      "panel.options": "4 · Fitting options",
      "panel.results": "Results",
      "panel.advisor": "Model advisor",

      "sub.overview": "Overview",
      "sub.figures": "Figures",
      "sub.params": "Parameters",
      "sub.interp": "Interpretation",
      "sub.diffusion": "Diffusion",
      "sub.linear": "Linear plots",
      "sub.export": "Export",

      "btn.example": "Load example",
      "btn.clear": "Clear",
      "btn.upload": "Upload CSV",
      "btn.fit": "Fit models",
      "btn.advise": "Analyse my data",
      "btn.applyAdvice": "Select recommended",
      "btn.all": "all",
      "btn.none": "none",
      "btn.download": "Download figure",
      "btn.downloadAll": "Download every format",
      "btn.downloadTable": "Download table",
      "btn.copy": "Copy to clipboard",
      "btn.save": "Save",
      "btn.cancel": "Cancel",
      "btn.delete": "Delete",
      "btn.rename": "Rename",
      "btn.load": "Load",
      "btn.close": "Close",
      "btn.addTemp": "+ Add temperature",
      "btn.runThermo": "Run thermodynamic analysis",
      "btn.remove": "remove",

      "lbl.timeUnit": "Time unit",
      "lbl.qUnit": "q unit",
      "lbl.cUnit": "C unit",
      "lbl.temperature": "Temperature (K)",
      "lbl.c0": "C₀ (mg L⁻¹)",
      "lbl.dose": "Adsorbent dose (g L⁻¹)",
      "lbl.radius": "Particle radius (cm)",
      "lbl.mw": "Molar mass (g mol⁻¹)",
      "lbl.cs": "Solubility Cs (mg L⁻¹)",
      "lbl.weighting": "Residual weighting",
      "lbl.criterion": "Ranking criterion",
      "lbl.alsoLinear": "Also compute classical linearised fits for comparison",
      "lbl.format": "Format",
      "lbl.resolution": "Resolution",
      "lbl.view": "View",
      "lbl.noData": "no data",
      "lbl.points": "points",

      "data.pasteKinetics": "Paste two columns: time and qt",
      "data.pasteIsotherm": "Paste two columns: Ce and qe",

      "opt.ols": "Ordinary least squares (equal weight)",
      "opt.rel": "Relative error (1/y): favours small values",
      "opt.sqrt": "Poisson-like (1/√y)",

      "fig.labels": "Labels & title",
      "fig.type": "Typography",
      "fig.axes": "Axes & ticks",
      "fig.grid": "Grid",
      "fig.legend": "Legend",
      "fig.canvas": "Canvas & export",
      "fig.series": "Series appearance",
      "fig.presets": "Journal size presets",
      "fig.viewFit": "Data + fitted curves",
      "fig.viewResid": "Residuals vs x",
      "fig.viewParity": "Predicted vs observed",

      "adv.title": "What your data can support",
      "adv.recommend": "Recommended",
      "adv.usable": "Usable with caveats",
      "adv.avoid": "Not advised",
      "adv.intro": "Screened every model against the shape of your raw data and a fast trial fit. Physics overrides statistics: a model that predicts impossible values is rejected however well it fits.",
      "adv.none": "Run the analysis to see which models your data can actually support.",

      "set.title": "Settings",
      "set.language": "Language",
      "set.theme": "Theme",
      "set.themeLight": "Light",
      "set.themeDark": "Dark",
      "set.themeAuto": "Match system",
      "set.motion": "Background motion",
      "set.motionFull": "Full",
      "set.motionCalm": "Calm",
      "set.motionOff": "Off",
      "set.layout": "Layout",
      "set.layoutSide": "Controls on the left",
      "set.layoutRight": "Controls on the right",
      "set.layoutStack": "Single column",
      "set.density": "Density",
      "set.densityComfy": "Comfortable",
      "set.densityCompact": "Compact",

      "set.panels": "Panels",
      "set.panelsHelp": "Drag the bar between the two columns to resize them. Drag a panel by the dotted grip in its header to reorder it, click the chevron to collapse it, and drag the grip under a figure to change its height.",
      "set.resetLayout": "Reset panel layout",
      "set.layoutReset": "Panel layout reset.",

      "proj.title": "Projects",
      "proj.save": "Save project",
      "proj.saveAs": "Save as…",
      "proj.name": "Project name",
      "proj.none": "No saved projects yet. Save one to pick up where you left off.",
      "proj.saved": "Project saved.",
      "proj.loaded": "Project loaded.",
      "proj.deleted": "Project deleted.",
      "proj.renamed": "Project renamed.",
      "proj.clickToRename": "Click to rename",
      "proj.confirmDelete": "Delete permanently?",
      "proj.export": "Export to file",
      "proj.import": "Import from file",
      "proj.modified": "last saved",
      "proj.current": "current",

      "issue.block": "Blocking",
      "issue.warn": "Caution",
      "issue.info": "Note",
      "issue.heading": "Domain and validity checks",

      "th.model": "Model",
      "th.parameter": "Parameter",
      "th.unit": "Unit",
      "th.value": "Value",
      "th.stderr": "Std. error",
      "th.ci": "95% CI",
      "th.support": "support",
      "th.rank": "#",
      "th.weight": "weight",

      "help.kinData": "Tab, comma, semicolon or space separated. A header row is detected automatically. Column 1 = time, column 2 = qt. Optional column 3 = error bars on qt.",
      "help.isoData": "Column 1 = equilibrium concentration Ce, column 2 = equilibrium loading qe. Optional column 3 = error bars. Optional column 4 = initial concentration C0 (enables the Langmuir separation factor RL).",
      "help.radius": "For Boyd and Crank diffusion coefficients.",
      "help.mw": "Needed for Dubinin–Radushkevich E and for the thermodynamic K° conversion.",
      "help.thermoIntro": "Enter one isotherm dataset per temperature. AdsorpFit fits your chosen isotherm model at each temperature, converts its constant into a properly dimensionless K°, and runs the van't Hoff analysis.",
      "help.boot": "This loads NumPy, SciPy and Matplotlib into your browser. It happens once per visit and takes roughly 10–20 seconds. Nothing you enter ever leaves your computer, all fitting runs locally.",
      "help.footPrivacy": "All fitting runs locally in your browser, no data is uploaded.",
      "foot.dept": "Sustainable Water Treatment Laboratory, Sungkyunkwan University",
      "foot.opensource": "Open source under the MIT licence.",
      "foot.contact": "Questions and bug reports",
      "th.step1": "1 · Isotherms at several temperatures",
      "th.step2": "2 · Equilibrium constant",
      "th.step3": "3 · Optional analyses",
      "th.routeHint": "this choice changes ΔG°",
      "th.modelLbl": "Isotherm model to fit at each T",
      "th.routeLbl": "Route to a dimensionless K°",

      "msg.selectModel": "Select at least one model.",
      "msg.needData": "Paste or upload some data first.",
      "msg.fitted": "Fitted {n} models.",
      "msg.rendering": "Rendering {fmt} at {dpi} dpi…",
      "msg.downloaded": "Downloaded.",
      "msg.copied": "Copied."
    },

    ko: {
      "brand.sub": "흡착 데이터 모델링",
      "brand.product": "제작",
      "brand.and": "·",

      "tab.kinetics": "동역학",
      "tab.isotherm": "등온흡착식",
      "tab.thermo": "열역학",
      "tab.guide": "사용 안내",

      "panel.data": "1 · 데이터",
      "panel.experiment": "2 · 실험 조건",
      "panel.models": "3 · 모델 선택",
      "panel.options": "4 · 피팅 옵션",
      "panel.results": "결과",
      "panel.advisor": "모델 추천",

      "sub.overview": "요약",
      "sub.figures": "그래프",
      "sub.params": "매개변수",
      "sub.interp": "해석",
      "sub.diffusion": "확산 해석",
      "sub.linear": "선형화 그래프",
      "sub.export": "내보내기",

      "btn.example": "예제 불러오기",
      "btn.clear": "지우기",
      "btn.upload": "CSV 업로드",
      "btn.fit": "모델 피팅",
      "btn.advise": "데이터 분석",
      "btn.applyAdvice": "추천 모델 선택",
      "btn.all": "전체",
      "btn.none": "해제",
      "btn.download": "그래프 다운로드",
      "btn.downloadAll": "모든 형식 다운로드",
      "btn.downloadTable": "표 다운로드",
      "btn.copy": "클립보드에 복사",
      "btn.save": "저장",
      "btn.cancel": "취소",
      "btn.delete": "삭제",
      "btn.rename": "이름 변경",
      "btn.load": "불러오기",
      "btn.close": "닫기",
      "btn.addTemp": "+ 온도 추가",
      "btn.runThermo": "열역학 해석 실행",
      "btn.remove": "제거",

      "lbl.timeUnit": "시간 단위",
      "lbl.qUnit": "q 단위",
      "lbl.cUnit": "농도 단위",
      "lbl.temperature": "온도 (K)",
      "lbl.c0": "초기 농도 C₀ (mg L⁻¹)",
      "lbl.dose": "흡착제 주입량 (g L⁻¹)",
      "lbl.radius": "입자 반경 (cm)",
      "lbl.mw": "분자량 (g mol⁻¹)",
      "lbl.cs": "용해도 Cs (mg L⁻¹)",
      "lbl.weighting": "잔차 가중치",
      "lbl.criterion": "모델 순위 기준",
      "lbl.alsoLinear": "비교를 위해 기존 선형화 피팅도 함께 계산",
      "lbl.format": "파일 형식",
      "lbl.resolution": "해상도",
      "lbl.view": "보기",
      "lbl.noData": "데이터 없음",
      "lbl.points": "개 데이터",

      "data.pasteKinetics": "두 개의 열을 붙여넣으세요: 시간과 qt",
      "data.pasteIsotherm": "두 개의 열을 붙여넣으세요: Ce와 qe",

      "opt.ols": "일반 최소제곱 (동일 가중치)",
      "opt.rel": "상대 오차 (1/y): 작은 값 중시",
      "opt.sqrt": "푸아송형 (1/√y)",

      "fig.labels": "축 제목 및 제목",
      "fig.type": "글꼴",
      "fig.axes": "축과 눈금",
      "fig.grid": "격자",
      "fig.legend": "범례",
      "fig.canvas": "크기 및 내보내기",
      "fig.series": "계열 서식",
      "fig.presets": "학술지 규격 사전 설정",
      "fig.viewFit": "데이터 + 피팅 곡선",
      "fig.viewResid": "잔차 그래프",
      "fig.viewParity": "예측값 대 실측값",

      "adv.title": "데이터가 뒷받침할 수 있는 모델",
      "adv.recommend": "추천",
      "adv.usable": "조건부 사용 가능",
      "adv.avoid": "권장하지 않음",
      "adv.intro": "원자료의 형태와 빠른 시험 피팅을 기준으로 모든 모델을 검토했습니다. 통계보다 물리적 타당성이 우선이며, 불가능한 값을 예측하는 모델은 적합도가 높아도 제외됩니다.",
      "adv.none": "분석을 실행하면 데이터가 실제로 뒷받침할 수 있는 모델을 확인할 수 있습니다.",

      "set.title": "설정",
      "set.language": "언어",
      "set.theme": "테마",
      "set.themeLight": "밝게",
      "set.themeDark": "어둡게",
      "set.themeAuto": "시스템 설정",
      "set.motion": "배경 애니메이션",
      "set.motionFull": "전체",
      "set.motionCalm": "약하게",
      "set.motionOff": "끄기",
      "set.layout": "레이아웃",
      "set.layoutSide": "설정창 왼쪽",
      "set.layoutRight": "설정창 오른쪽",
      "set.layoutStack": "한 열로 배치",
      "set.density": "간격",
      "set.densityComfy": "넓게",
      "set.densityCompact": "좁게",

      "set.panels": "패널",
      "set.panelsHelp": "두 열 사이의 막대를 끌어 너비를 조절할 수 있습니다. 패널 머리글의 점 모양 손잡이를 끌면 순서를 바꿀 수 있고, 화살표를 누르면 접히며, 그래프 아래 손잡이를 끌면 높이를 조절할 수 있습니다.",
      "set.resetLayout": "패널 배치 초기화",
      "set.layoutReset": "패널 배치를 초기화했습니다.",

      "proj.title": "프로젝트",
      "proj.save": "프로젝트 저장",
      "proj.saveAs": "다른 이름으로 저장…",
      "proj.name": "프로젝트 이름",
      "proj.none": "저장된 프로젝트가 없습니다. 저장해 두면 다음에 이어서 작업할 수 있습니다.",
      "proj.saved": "프로젝트를 저장했습니다.",
      "proj.loaded": "프로젝트를 불러왔습니다.",
      "proj.deleted": "프로젝트를 삭제했습니다.",
      "proj.renamed": "프로젝트 이름을 변경했습니다.",
      "proj.clickToRename": "클릭하여 이름 변경",
      "proj.confirmDelete": "완전히 삭제할까요?",
      "proj.export": "파일로 내보내기",
      "proj.import": "파일에서 가져오기",
      "proj.modified": "마지막 저장",
      "proj.current": "현재",

      "issue.block": "사용 불가",
      "issue.warn": "주의",
      "issue.info": "참고",
      "issue.heading": "적용 범위 및 타당성 검사",

      "th.model": "모델",
      "th.parameter": "매개변수",
      "th.unit": "단위",
      "th.value": "값",
      "th.stderr": "표준오차",
      "th.ci": "95% 신뢰구간",
      "th.support": "근거",
      "th.rank": "순위",
      "th.weight": "가중치",

      "help.kinData": "탭, 쉼표, 세미콜론 또는 공백으로 구분합니다. 머리글 행은 자동으로 인식됩니다. 1열 = 시간, 2열 = qt. 3열(선택) = qt의 오차 막대.",
      "help.isoData": "1열 = 평형 농도 Ce, 2열 = 평형 흡착량 qe. 3열(선택) = 오차 막대. 4열(선택) = 초기 농도 C0 (Langmuir 분리 계수 RL 계산에 사용).",
      "help.radius": "Boyd 및 Crank 확산계수 계산에 사용됩니다.",
      "help.mw": "Dubinin–Radushkevich의 E 값과 열역학 K° 변환에 필요합니다.",
      "help.thermoIntro": "온도별로 등온흡착 데이터를 하나씩 입력하세요. 각 온도에서 선택한 등온흡착식을 피팅하고, 그 상수를 무차원 K°로 변환한 뒤 van't Hoff 해석을 수행합니다.",
      "help.boot": "NumPy, SciPy, Matplotlib을 브라우저에 불러옵니다. 방문할 때 한 번만 수행되며 약 10~20초가 걸립니다. 입력한 데이터는 컴퓨터를 벗어나지 않으며 모든 계산은 로컬에서 실행됩니다.",
      "help.footPrivacy": "모든 계산은 사용자의 브라우저에서 실행되며, 데이터는 업로드되지 않습니다.",
      "foot.dept": "지속가능 수처리 연구실, 성균관대학교",
      "foot.opensource": "MIT 라이선스로 공개된 오픈소스입니다.",
      "foot.contact": "문의 및 오류 제보",
      "th.step1": "1 · 여러 온도의 등온흡착 데이터",
      "th.step2": "2 · 평형상수",
      "th.step3": "3 · 선택 해석",
      "th.routeHint": "이 선택이 ΔG°를 바꿉니다",
      "th.modelLbl": "각 온도에서 피팅할 등온흡착식",
      "th.routeLbl": "무차원 K°로 변환하는 방법",

      "msg.selectModel": "모델을 최소 하나 선택하세요.",
      "msg.needData": "먼저 데이터를 붙여넣거나 업로드하세요.",
      "msg.fitted": "{n}개 모델을 피팅했습니다.",
      "msg.rendering": "{fmt} 형식, {dpi} dpi로 생성 중…",
      "msg.downloaded": "다운로드했습니다.",
      "msg.copied": "복사했습니다."
    }
  };

  let lang = "en";
  const listeners = [];

  function t(key, vars) {
    let s = (DICT[lang] && DICT[lang][key]) || DICT.en[key] || key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        s = s.replace(new RegExp("\\{" + k + "\\}", "g"), vars[k]);
      });
    }
    return s;
  }

  function apply(root) {
    (root || document).querySelectorAll("[data-i18n]").forEach(function (n) {
      const key = n.getAttribute("data-i18n");
      const attr = n.getAttribute("data-i18n-attr");
      if (attr) n.setAttribute(attr, t(key));
      else n.textContent = t(key);
    });
  }

  function set(next) {
    if (!DICT[next]) return;
    lang = next;
    document.documentElement.setAttribute("lang", next);
    try { localStorage.setItem("adsorpfit-lang", next); } catch (e) {}
    apply(document);
    listeners.forEach(function (fn) { try { fn(next); } catch (e) {} });
  }

  function init() {
    let saved = null;
    try { saved = localStorage.getItem("adsorpfit-lang"); } catch (e) {}
    if (!saved) {
      saved = (navigator.language || "en").toLowerCase().indexOf("ko") === 0
        ? "ko" : "en";
    }
    lang = DICT[saved] ? saved : "en";
    document.documentElement.setAttribute("lang", lang);
  }

  return {
    t: t, set: set, apply: apply, init: init,
    get: function () { return lang; },
    onChange: function (fn) { listeners.push(fn); },
    languages: [["en", "English"], ["ko", "한국어"]]
  };
})();
