# -*- coding: utf-8 -*-
"""Pre-publication audit of the whole project.

Checks the things that are easy to get wrong and invisible once wrong:
translation coverage, dead references between the layers, asset weight,
leftover debugging, licence and attribution, and the consistency of the
model registry with what the interface claims.

Run from the project root:  python tools/audit.py
"""
import io, json, os, re, sys

ISSUES = []          # (severity, area, message)


def add(sev, area, msg):
    ISSUES.append((sev, area, msg))


def read(path):
    return io.open(path, encoding="utf-8").read()


# --------------------------------------------------------------------------
def check_i18n():
    src = read("js/i18n.js")
    blocks = {}
    for lang in ("en", "ko"):
        m = re.search(r"\n    %s: \{(.*?)\n    \}" % lang, src, re.S)
        if not m:
            add("ERROR", "i18n", "could not find the %s dictionary" % lang)
            return
        blocks[lang] = set(re.findall(r'"([^"]+)":\s*"', m.group(1)))

    only_en = blocks["en"] - blocks["ko"]
    only_ko = blocks["ko"] - blocks["en"]
    for k in sorted(only_en):
        add("WARN", "i18n", "key missing from Korean: %s" % k)
    for k in sorted(only_ko):
        add("WARN", "i18n", "key missing from English: %s" % k)
    if not only_en and not only_ko:
        add("OK", "i18n", "%d keys, both languages complete" % len(blocks["en"]))

    # every key referenced in markup or code must exist
    used = set(re.findall(r'data-i18n="([^"]+)"', read("index.html")))
    dynamic = set()
    for f in ("js/app.js", "js/plot.js", "js/layout.js"):
        src_f = read(f)
        used |= set(re.findall(r'I18N\.t\("([^"]+)"', src_f))
        # keys assembled at runtime, e.g. I18N.t("adv." + verdict)
        dynamic |= set(re.findall(r'I18N\.t\("([^"]+\.)"\s*\+', src_f))
        # keys passed as a variable, e.g. field("fig.colour", node)
        used |= set(re.findall(r'field\("([^"]+)"', src_f))
        used |= set(re.findall(r'segmented\("([^"]+)", "[^"]+", \[', src_f))
        used |= set(re.findall(r'\["[^"]+", "([a-z]+\.[A-Za-z]+)"\]', src_f))
    used -= dynamic
    for pre in dynamic:
        used |= {k for k in blocks["en"] if k.startswith(pre)}
    missing = sorted(used - blocks["en"])
    for k in missing:
        add("ERROR", "i18n", "referenced but not defined: %s" % k)
    if not missing:
        add("OK", "i18n", "all %d referenced keys are defined" % len(used))

    unused = sorted(blocks["en"] - used)
    if unused:
        add("INFO", "i18n", "%d defined but never referenced (%s%s)" %
            (len(unused), ", ".join(unused[:5]),
             ", ..." if len(unused) > 5 else ""))


# --------------------------------------------------------------------------
def check_models():
    sys.path.insert(0, "py")
    from isotherms import ISOTHERM_MODELS
    from kinetics import KINETIC_MODELS
    all_models = dict(ISOTHERM_MODELS)
    all_models.update(KINETIC_MODELS)

    for key, m in all_models.items():
        if not m.equation:
            add("ERROR", "models", "%s has no LaTeX equation" % key)
        if not m.equation_plain:
            add("ERROR", "models", "%s has no ASCII fallback equation" % key)
        if not m.citation:
            add("ERROR", "models", "%s has no citation" % key)
        if not m.assumptions:
            add("WARN", "models", "%s lists no assumptions" % key)
        if m.interpretation is None:
            add("WARN", "models", "%s has no interpretation function" % key)
        for p in m.params:
            if not p.meaning:
                add("ERROR", "models", "%s.%s has no meaning text" % (key, p.key))
            if not p.unit:
                add("WARN", "models", "%s.%s has no unit" % (key, p.key))
            if p.lower >= p.upper:
                add("ERROR", "models",
                    "%s.%s bounds are inverted" % (key, p.key))
    add("OK", "models", "%d models: %d isotherm, %d kinetic" %
        (len(all_models), len(ISOTHERM_MODELS), len(KINETIC_MODELS)))

    # the README's headline counts must match reality
    rd = read("README.md")
    for n, word in ((len(KINETIC_MODELS), "kinetics"),
                    (len(ISOTHERM_MODELS), "isotherm")):
        if not re.search(r"\b%d\b" % n, rd):
            add("WARN", "docs",
                "README does not mention the %s model count (%d)" % (word, n))
    if str(len(all_models)) not in rd:
        add("WARN", "docs", "README total model count is stale")


# --------------------------------------------------------------------------
def check_presets():
    src = read("js/presets.js")
    m = re.search(r"const PRESETS = (\[.*\]);", src, re.S)
    if not m:
        add("ERROR", "presets", "could not parse the preset list")
        return
    presets = json.loads(m.group(1))
    sys.path.insert(0, "py")
    for p in presets:
        for field in ("id", "cat", "cite", "data", "en", "ko"):
            if not p.get(field):
                add("ERROR", "presets", "%s is missing %s" % (p.get("id"), field))
        rows = [r for r in p["data"].split("\n")[1:] if r.strip()]
        if len(rows) < 4:
            add("WARN", "presets", "%s has only %d rows" % (p["id"], len(rows)))
        for r in rows:
            for cell in r.split("\t"):
                try:
                    float(cell)
                except ValueError:
                    add("ERROR", "presets",
                        "%s has a non-numeric cell: %r" % (p["id"], cell))
                    break
        if "10." not in p["cite"] and "doi" not in p["cite"].lower():
            add("WARN", "presets", "%s citation has no DOI" % p["id"])
    add("OK", "presets", "%d presets, all numeric and attributed" % len(presets))


# --------------------------------------------------------------------------
def check_assets():
    total = 0
    for root, dirs, files in os.walk("."):
        if any(s in root for s in (".git", "__pycache__", ".claude")):
            continue
        for f in files:
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            total += size
            if f.endswith((".js", ".css", ".html")) and size > 250 * 1024:
                add("WARN", "assets", "%s is %.0f KB" % (path, size / 1024))
    add("OK", "assets", "repository is %.1f MB in total" % (total / 1024 / 1024))

    # anything the page loads must actually exist
    html = read("index.html")
    for ref in re.findall(r'(?:src|href)="((?!https?:|data:|#|mailto:|tel:)[^"]+)"', html):
        path = ref.split("?")[0]
        if not os.path.exists(path):
            add("ERROR", "assets", "index.html references a missing file: %s" % path)


def check_cache_busting():
    html = read("index.html")
    ver = re.search(r'window\.APP_VERSION = "([^"]+)"', html)
    if not ver:
        add("ERROR", "release", "APP_VERSION is not set")
        return
    v = ver.group(1)
    refs = re.findall(r'(?:src|href)="(?:js|css)/[^"?]+\?v=([^"]+)"', html)
    unversioned = re.findall(r'(?:src|href)="((?:js|css)/[^"?]+)"', html)
    if unversioned:
        add("ERROR", "release",
            "these will be served from cache after an update: %s" %
            ", ".join(unversioned))
    bad = sorted(set(r for r in refs if r != v))
    if bad:
        add("ERROR", "release",
            "asset versions disagree with APP_VERSION=%s: %s" % (v, bad))
    else:
        add("OK", "release", "all %d assets tagged v=%s" % (len(refs), v))


# --------------------------------------------------------------------------
def check_hygiene():
    for path in ["index.html"] + ["js/" + f for f in os.listdir("js")] + \
                ["py/" + f for f in os.listdir("py")]:
        if not os.path.isfile(path):
            continue
        src = read(path)
        for pat, msg in ((r"\bTODO\b", "TODO left in"),
                         (r"\bFIXME\b", "FIXME left in"),
                         (r"\bXXX\b", "XXX left in"),
                         (r"\bdebugger;", "debugger statement"),
                         (r"console\.log\(", "console.log left in")):
            n = len(re.findall(pat, src))
            if n:
                add("WARN", "hygiene", "%s: %s (%d)" % (path, msg, n))
        if path.endswith(".py") and "\t" in src:
            add("WARN", "hygiene", "%s contains tab indentation" % path)

    # secrets and personal data that should not be committed
    for path in ("index.html", "js/app.js", "js/presets.js"):
        src = read(path)
        for pat, msg in ((r"(?i)api[_-]?key\s*[:=]\s*['\"]", "possible API key"),
                         (r"(?i)password\s*[:=]\s*['\"]", "possible password"),
                         (r"(?i)secret\s*[:=]\s*['\"]", "possible secret")):
            if re.search(pat, src):
                add("ERROR", "security", "%s: %s" % (path, msg))
    add("OK", "security", "no credentials found in the shipped files")


def check_external():
    html = read("index.html")
    hosts = sorted(set(re.findall(r'(?:src|href)="https://([^/"]+)', html)))
    add("INFO", "network", "third-party hosts: %s" % ", ".join(hosts))
    for h in hosts:
        if h not in ("cdn.jsdelivr.net", "cdn.plot.ly", "fonts.googleapis.com",
                     "fonts.gstatic.com", "www.skku.edu", "www.swatlab.or.kr"):
            add("WARN", "network", "unexpected external host: %s" % h)
    if "crossorigin" not in html:
        add("WARN", "network", "CDN tags carry no crossorigin attribute")


def check_notation():
    """Parameter symbols must all convert to valid LaTeX for the tables."""
    sys.path.insert(0, "py")
    from isotherms import ISOTHERM_MODELS
    from kinetics import KINETIC_MODELS
    models = dict(ISOTHERM_MODELS)
    models.update(KINETIC_MODELS)
    bad = 0
    total = 0
    for key, m in models.items():
        for prm in m.params:
            total += 1
            t = prm.symbol_tex
            if not t or ("_" in t and "{" not in t) or re.search(u"[₀-₉]", t):
                add("ERROR", "notation", "%s.%s renders as %r" % (key, prm.key, t))
                bad += 1
    if not bad:
        add("OK", "notation",
            "%d parameter symbols convert to LaTeX cleanly" % total)


def check_licence():
    if not os.path.exists("LICENSE"):
        add("ERROR", "legal", "no LICENSE file")
    rd = read("README.md")
    for token in ("zenodo", "Wang", "CC0"):
        if token.lower() not in rd.lower():
            add("WARN", "legal",
                "README does not credit the preset data source (%s)" % token)


def check_accessibility():
    html = read("index.html")
    for m in re.finditer(r"<button(?![^>]*aria-label)([^>]*)>(.*?)</button>",
                         html, re.S):
        inner = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not inner:
            add("WARN", "a11y", "button with neither text nor aria-label: %s"
                % m.group(1).strip()[:60])
    if 'lang="' not in html:
        add("ERROR", "a11y", "no lang attribute on <html>")
    n_inputs = len(re.findall(r"<input", html))
    n_labels = len(re.findall(r"<label", html))
    if n_labels < n_inputs * 0.6:
        add("WARN", "a11y", "%d inputs but only %d labels" % (n_inputs, n_labels))
    add("OK", "a11y", "%d inputs, %d labels" % (n_inputs, n_labels))


# --------------------------------------------------------------------------
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for fn in (check_i18n, check_models, check_presets, check_assets,
               check_cache_busting, check_hygiene, check_external,
               check_notation, check_licence, check_accessibility):
        try:
            fn()
        except Exception as exc:
            add("ERROR", fn.__name__, "audit step crashed: %s" % exc)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2, "OK": 3}
    ISSUES.sort(key=lambda i: (order[i[0]], i[1]))
    print("=" * 84)
    print("PRE-PUBLICATION AUDIT")
    print("=" * 84)
    for sev, area, msg in ISSUES:
        print("  %-5s %-10s %s" % (sev, area, msg))
    errs = sum(1 for i in ISSUES if i[0] == "ERROR")
    warns = sum(1 for i in ISSUES if i[0] == "WARN")
    print("=" * 84)
    print("%d error(s), %d warning(s)" % (errs, warns))
    sys.exit(1 if errs else 0)
