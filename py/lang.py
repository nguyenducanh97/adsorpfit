# -*- coding: utf-8 -*-
"""Translation of the prose AdsorpFit generates.

The interpretation paragraphs, the domain and validity warnings, the
advisor's reasons and the ranking summary are all composed here in Python,
with fitted numbers interpolated into them. That puts them out of reach of
the [data-i18n] attributes the rest of the interface uses, which is why the
results panel stayed English when the interface switched to Korean.

Every such sentence is therefore written as a template, and the English
template is itself the lookup key. Two consequences are worth knowing:

  A missing translation is not an error. The English template is returned
  and formatted as usual, so the site keeps working while a language is
  still being filled in, and a half-translated release degrades to English
  sentence by sentence rather than breaking.

  Editing an English sentence orphans its translation. tools/audit.py
  reports the coverage and names any Korean entry whose key no longer
  matches a template in the source, which is how that gets caught.

Placeholders are named rather than positional, because Korean puts the
number in a different place from English more often than not and a
translator has to be free to reorder them.

  tr("The capacity is {qm} {unit}.", qm="12.4", unit="mg/g")
"""

from ko import KO

LANG = "en"

TABLES = {"ko": KO}


def set_lang(code):
    """Choose the language for everything generated from here on."""
    global LANG
    LANG = code if code in ("en", "ko") else "en"
    return LANG


def get_lang():
    return LANG


def tr(template, **vars):
    """Translate a sentence template, then fill in the numbers.

    The template is returned untranslated when no entry exists, so a
    sentence that has not been translated yet still reads correctly.
    """
    table = TABLES.get(LANG)
    text = template
    if table is not None:
        text = table.get(template, template)
    if not vars:
        return text
    try:
        return text.format(**vars)
    except (KeyError, IndexError, ValueError):
        # A translation whose placeholders do not match the English ones
        # would otherwise raise in the middle of a fit. Fall back rather
        # than lose the whole result over a typo in a translation file.
        try:
            return template.format(**vars)
        except Exception:
            return template


def tr_list(templates):
    """Translate a list of plain sentences that carry no numbers."""
    return [tr(t) for t in templates]
