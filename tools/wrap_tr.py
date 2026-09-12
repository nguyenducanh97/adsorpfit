# -*- coding: utf-8 -*-
"""Wrap the plain prose strings of a module in tr(), leaving f-strings alone.

Most generated sentences are plain string literals appended to a list. Those
can be wrapped mechanically and safely: the text is untouched, only tr(...)
goes around it, and the indentation of the continuation lines is preserved.

f-strings are deliberately skipped. They carry interpolated values that have
to become named placeholders, and choosing those names is a judgement about
what the translator will see, so they are converted by hand.

The rewrite is textual rather than an ast.unparse round trip, because these
modules are heavily commented and unparse would discard every comment.

Run:  python tools/wrap_tr.py py/advisor.py           show what would change
      python tools/wrap_tr.py py/advisor.py --write   apply it
"""
import ast
import io
import re
import sys


def targets(src):
    """(start, end) offsets of plain string literals that reach the reader.

    A literal qualifies when it is an argument to one of the append calls
    that build the prose lists, or the text argument of issue(), and when it
    is not already wrapped in tr().
    """
    # col_offset is counted in UTF-8 bytes, not characters, so a line
    # containing a degree sign or a superscript would otherwise place the
    # closing bracket several characters adrift. Work in bytes throughout.
    tree = ast.parse(src)
    lines = src.encode("utf-8").splitlines(keepends=True)
    starts = [0]
    for ln in lines:
        starts.append(starts[-1] + len(ln))

    def offset(lineno, col):
        return starts[lineno - 1] + col

    out = []

    # Spans already passed to tr(). Wrapping one again would produce
    # tr(tr(...)), whose key is a call rather than a sentence, so the
    # lookup would silently never match.
    done = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "tr" and node.args):
            a = node.args[0]
            done.add((offset(a.lineno, a.col_offset),
                      offset(a.end_lineno, a.end_col_offset)))

    def take(a):
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            span = (offset(a.lineno, a.col_offset),
                    offset(a.end_lineno, a.end_col_offset))
            if len(a.value.split()) >= 3 and span not in done:
                out.append(span)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name == "append" and node.args:
            take(node.args[0])
        elif name == "issue" and len(node.args) >= 3:
            take(node.args[2])

    # The interpretation functions also build their paragraphs as plain
    # list literals. Those are prose too, but the same shape inside a
    # ModelSpec is the assumptions list, which is model metadata rather
    # than generated results, so only the interpretation bodies are
    # searched: the named _interp_* functions and the lambdas passed as
    # interpretation=, which is how the shorter models declare theirs.
    bodies = [fn for fn in ast.walk(tree)
              if isinstance(fn, ast.FunctionDef) and fn.name.startswith("_interp")]
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "interpretation":
            if isinstance(node.value, ast.Lambda):
                bodies.append(node.value)
    for fn in bodies:
        for node in ast.walk(fn):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                take(node)
    return sorted(set(out), reverse=True)


def main():
    path = sys.argv[1]
    src = open(path, encoding="utf-8").read()
    spans = targets(src)
    raw = src.encode("utf-8")
    for a, b in spans:                       # reverse order, so earlier
        raw = raw[:a] + b"tr(" + raw[a:b] + b")" + raw[b:]
    new = raw.decode("utf-8")                # offsets stay valid
    print("%s: %d plain literal(s) wrapped" % (path, len(spans)))
    if "--write" in sys.argv:
        ast.parse(new)                       # refuse to write a broken file
        open(path, "w", encoding="utf-8", newline="").write(new)
        print("written")
    else:
        print("(dry run, pass --write to apply)")


if __name__ == "__main__":
    main()
