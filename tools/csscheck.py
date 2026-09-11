# -*- coding: utf-8 -*-
"""Report malformed selectors in a stylesheet.

Written after two rounds of regex edits left selector fragments with no body,
which silently absorbed the following rule into a compound selector that can
never match. The symptom is invisible: the CSS parses, no error is logged,
the rule simply never applies.

Flags a selector when it:
  * names :root or html more than once (a fragment swallowed the next rule)
  * contains a run of two or more descendant combinators' worth of nothing
  * is empty, or ends in a combinator
  * repeats the same attribute selector twice in one compound
"""
import io, re, sys


def rules(css):
    """Yield (selector, body, line_no) for every top-level rule."""
    css = re.sub(r'/\*.*?\*/', lambda m: "\n" * m.group(0).count("\n"), css, flags=re.S)
    i, n, depth, start = 0, len(css), 0, 0
    sel_start = 0
    line = 1
    line_at = {}
    for idx, ch in enumerate(css):
        if ch == "\n":
            line += 1
        line_at[idx] = line
    while i < n:
        ch = css[i]
        if ch == "{":
            if depth == 0:
                sel = css[sel_start:i].strip()
                start = i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                body = css[start:i]
                yield sel, body, line_at.get(sel_start, 0)
                sel_start = i + 1
        i += 1


def suspicious(sel):
    s = " ".join(sel.split())
    if not s:
        return "empty selector"
    for part in s.split(","):
        p = part.strip()
        if not p:
            return "empty selector in list"
        if p.endswith((">", "+", "~")):
            return "ends in a combinator: " + p[:60]
        if len(re.findall(r':root\b', p)) > 1:
            return "names :root more than once: " + p[:70]
        if len(re.findall(r'\bhtml\b', p)) > 1:
            return "names html more than once: " + p[:70]
        attrs = re.findall(r'\[[^\]]+\]', p)
        if len(attrs) != len(set(attrs)) and len(attrs) > 1:
            return "repeats an attribute selector: " + p[:70]
    return None


def main(path):
    css = io.open(path, encoding="utf-8").read()
    bad = 0
    empty = 0
    for sel, body, line in rules(css):
        if sel.startswith("@"):
            continue
        why = suspicious(sel)
        if why:
            print("  line %-5d %s" % (line, why))
            bad += 1
        if not body.strip():
            print("  line %-5d empty rule body: %s" % (line, sel[:60]))
            empty += 1
    print("%s: %d malformed selector(s), %d empty rule(s)" % (path, bad, empty))
    return 1 if (bad or empty) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "css/style.css"))
