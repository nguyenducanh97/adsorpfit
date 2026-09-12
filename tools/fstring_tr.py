# -*- coding: utf-8 -*-
"""Turn the prose f-strings of a module into tr() templates.

An f-string cannot be translated: by the time it is a value the numbers are
already inside it, so there is nothing left to look up. Each one has to
become a template with named placeholders plus the expressions that fill
them. There are about 150 of these across the model library, so they are
converted mechanically rather than by hand.

The rewrite works on the source text, not on an ast.unparse round trip, so
the original line breaks, indentation and the surrounding comments all
survive. Only two things change: the f prefixes go, and each {expression}
becomes a {name} that is passed as a keyword argument.

Names are derived from the expression itself, because the name is what a
translator sees:

    {fmt(qe)}              -> {qe}
    {f.params['k1']}       -> {k1}
    {s['n_early']}         -> {n_early}
    {spec.n_params}        -> {n_params}
    {diff:.0f}             -> {diff:.0f}
    {1.0 / b if b else 0}  -> {v1}      (no sensible name, so numbered)

Run:  python tools/fstring_tr.py py/kinetics.py          preview
      python tools/fstring_tr.py py/kinetics.py --write  apply
"""
import ast
import keyword
import os
import re
import sys

MIN_WORDS = 5


def line_starts(raw):
    starts = [0]
    for ln in raw.splitlines(keepends=True):
        starts.append(starts[-1] + len(ln))
    return starts


def split_fields(text):
    """Yield (start, end, expression, suffix) for each {...} in an f-string.

    suffix keeps any !conversion and :format spec, which must survive
    untouched or the number would be printed to a different precision.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "{":
            if i + 1 < n and text[i + 1] == "{":
                i += 2
                continue
            depth, j = 1, i + 1
            quote = None
            while j < n and depth:
                ch = text[j]
                if quote:
                    if ch == quote:
                        quote = None
                elif ch in "'\"":
                    quote = ch
                elif ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = text[i + 1:j]
            # the format spec is a top-level colon, outside every bracket
            d, q, cut = 0, None, None
            for k, ch in enumerate(body):
                if q:
                    if ch == q:
                        q = None
                elif ch in "'\"":
                    q = ch
                elif ch in "([{":
                    d += 1
                elif ch in ")]}":
                    d -= 1
                elif ch in ":!" and d == 0:
                    if ch == "!" and k + 1 < len(body) and body[k + 1] == "=":
                        continue
                    cut = k
                    break
            expr = body if cut is None else body[:cut]
            suffix = "" if cut is None else body[cut:]
            out.append((i, j + 1, expr.strip(), suffix))
            i = j + 1
        else:
            i += 1
    return out


def name_for(expr, used):
    """A readable placeholder name for an expression."""
    e = expr.strip()
    m = re.fullmatch(r"fmt\((.*)\)", e)
    if m:
        e = m.group(1).strip()
    m = re.fullmatch(r"int\((.*)\)|float\((.*)\)", e)
    if m:
        e = (m.group(1) or m.group(2)).strip()
    cand = None
    m = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", e)
    if m:
        cand = e
    if cand is None:
        m = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*\[['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\]", e)
        if m:
            cand = m.group(1)
    if cand is None:
        m = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.get\(['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\)", e)
        if m:
            cand = m.group(1)
    if cand is None:
        m = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.([A-Za-z_][A-Za-z0-9_]*)", e)
        if m:
            cand = m.group(1)
    if cand is None or keyword.iskeyword(cand) or cand in ("format", "self"):
        i = 1
        while ("v%d" % i) in used:
            i += 1
        cand = "v%d" % i
    base, i = cand, 2
    while cand in used and used[cand] != expr:
        cand = "%s%d" % (base, i)
        i += 1
    return cand


def strip_f_prefixes(text):
    """Drop the f from every literal in an implicitly concatenated group."""
    return re.sub(r'(^|[\s(\[,+])([fF])(["\'])', r"\1\3", text)


def convert(path, write=False):
    src = open(path, encoding="utf-8").read()
    raw = src.encode("utf-8")
    starts = line_starts(raw)
    tree = ast.parse(src)

    jobs = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        text = "".join(v.value for v in node.values
                       if isinstance(v, ast.Constant))
        if len(text.split()) < MIN_WORDS:
            continue
        a = starts[node.lineno - 1] + node.col_offset
        b = starts[node.end_lineno - 1] + node.end_col_offset
        jobs.append((a, b))

    changed = 0
    for a, b in sorted(set(jobs), reverse=True):
        chunk = raw[a:b].decode("utf-8")
        used, kwargs = {}, []
        fields = split_fields(chunk)
        new = chunk
        for (i, j, expr, suffix) in reversed(fields):
            nm = name_for(expr, used)
            if nm not in used:
                used[nm] = expr
                kwargs.append((nm, expr))
            new = new[:i] + "{" + nm + suffix + "}" + new[j:]
        new = strip_f_prefixes(new)
        kwargs.reverse()
        # indentation of the continuation, taken from the line the node is on
        line_start = raw.rfind(b"\n", 0, a) + 1
        indent = " " * (len(raw[line_start:a].decode("utf-8"))
                        - len(raw[line_start:a].decode("utf-8").lstrip()))
        pad = indent + "    "
        args = ", ".join("%s=%s" % (n, e) for n, e in kwargs)
        if args:
            body = "tr(" + new + ",\n" + pad + args + ")"
        else:
            body = "tr(" + new + ")"
        raw = raw[:a] + body.encode("utf-8") + raw[b:]
        changed += 1

    out = raw.decode("utf-8")
    print("%s: %d f-string(s) converted" % (path, changed))
    try:
        ast.parse(out)
    except SyntaxError as exc:
        print("  REFUSED, result does not parse: %s" % exc)
        return 1
    if write:
        open(path, "w", encoding="utf-8", newline="").write(out)
        print("  written")
    else:
        print("  (dry run, pass --write to apply)")
    return 0


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(convert(sys.argv[1], "--write" in sys.argv))
