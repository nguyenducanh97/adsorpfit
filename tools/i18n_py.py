# -*- coding: utf-8 -*-
"""Track the translation of the prose the Python layer generates.

The interpretation paragraphs, domain warnings, advisor reasons and ranking
summary are composed in Python with fitted numbers in them, so they are
translated through lang.tr(), whose lookup key is the English sentence
itself. This walks the source, collects every template actually passed to
tr(), and compares that set with the Korean table in py/ko.py.

It reports three things, and only the last two are defects:

  coverage   how much of the generated prose a reader in Korean will see
             in Korean rather than in English
  orphaned   a Korean entry whose English sentence no longer exists,
             usually because the English was edited afterwards
  mismatched a translation whose {placeholders} differ from the English
             ones, which would otherwise fall back mid-sentence

Run:  python tools/i18n_py.py            report
      python tools/i18n_py.py --check    exit non-zero on a defect
      python tools/i18n_py.py --todo     print untranslated templates
"""
import ast
import io
import os
import re
import sys

MODULES = ["model names", "assumptions", "core.py", "isotherms.py", "kinetics.py", "thermo.py",
           "advisor.py", "bridge.py"]


def literal(node):
    """The template string of a tr() call, or None if it is not a literal."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    # implicit concatenation across lines is folded by the parser already
    return None


def templates():
    """Every template passed to tr(), keyed to the module it came from."""
    found = {}
    for mod in MODULES:
        path = os.path.join("py", mod)
        if not os.path.isfile(path):
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if name != "tr" or not node.args:
                continue
            s = literal(node.args[0])
            if s is None:
                continue
            found.setdefault(s, set()).add(mod)

    # Model names reach tr() as a variable, tr(spec.name), so they cannot be
    # collected from the call sites. They are translatable all the same, and
    # counting them here is what stops the audit reporting the name table as
    # a set of orphaned translations.
    try:
        from isotherms import ISOTHERM_MODELS
        from kinetics import KINETIC_MODELS
        for reg in (ISOTHERM_MODELS, KINETIC_MODELS):
            for m in reg.values():
                found.setdefault(m.name, set()).add("model names")
                for a in m.assumptions:
                    found.setdefault(a, set()).add("assumptions")
    except Exception:
        pass
    return found


def holders(s):
    return set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)", s))


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, "py")
    from ko import KO

    tpl = templates()
    done = [t for t in tpl if t in KO]
    todo = sorted(t for t in tpl if t not in KO)
    orphan = sorted(k for k in KO if k not in tpl)
    mismatch = [(t, holders(t), holders(KO[t])) for t in done
                if holders(t) != holders(KO[t])]

    if "--todo" in sys.argv:
        for t in todo:
            print("%s\n   (%s)\n" % (t, ", ".join(sorted(tpl[t]))))
        return 0

    per_mod = {}
    for t, mods in tpl.items():
        for m in mods:
            d, n = per_mod.get(m, (0, 0))
            per_mod[m] = (d + (1 if t in KO else 0), n + 1)

    print("=" * 66)
    print("PYTHON PROSE TRANSLATION")
    print("=" * 66)
    for m in MODULES:
        if m in per_mod:
            d, n = per_mod[m]
            print("  %-14s %3d / %3d   %5.1f%%" % (m, d, n, 100.0 * d / n))
    print("  " + "-" * 40)
    print("  %-14s %3d / %3d   %5.1f%%"
          % ("ko total", len(done), len(tpl),
             100.0 * len(done) / max(1, len(tpl))))

    bad = False
    for t, a, b in mismatch:
        bad = True
        print("\n  MISMATCH placeholders %s vs %s\n    %s"
              % (sorted(a), sorted(b), t[:70]))
    for k in orphan:
        bad = True
        print("\n  ORPHANED translation, no such English sentence:\n    %s"
              % k[:70])
    if not bad:
        print("\n  no orphaned entries, no placeholder mismatches")
    if todo and "--check" not in sys.argv:
        print("\n  %d template(s) still to translate, run --todo to list them"
              % len(todo))
    return 1 if (bad and "--check" in sys.argv) else 0


if __name__ == "__main__":
    sys.exit(main())
